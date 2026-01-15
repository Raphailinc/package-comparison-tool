from __future__ import annotations

import logging
import time
from collections.abc import Mapping

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import __version__
from .exceptions import AltApiError, BranchNotFoundError
from .models import PackageInfo

ALT_RDB_API_BASE = "https://rdb.altlinux.org/api/export"
DEFAULT_USER_AGENT = f"package-comparison-tool/{__version__}"
RETRYABLE_STATUSES = (429, 500, 502, 503, 504)

logger = logging.getLogger(__name__)


def create_session(*, user_agent: str | None = None, retries: int = 3) -> requests.Session:
    """Create a requests.Session with basic retry configuration.

    This function is part of the public API; callers own the returned session and must close it.
    """

    session = requests.Session()
    if user_agent:
        session.headers.update({"User-Agent": user_agent})

    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=0.3,
        status_forcelist=RETRYABLE_STATUSES,
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _merge_headers(
    session: requests.Session | None,
    *,
    user_agent: str | None,
    headers: Mapping[str, str] | None,
) -> dict[str, str]:
    merged: dict[str, str] = {}
    if session is not None and session.headers:
        merged.update(session.headers)  # copy to avoid mutating caller-owned headers

    resolved_ua = user_agent or merged.get("User-Agent") or DEFAULT_USER_AGENT
    merged["User-Agent"] = resolved_ua

    if headers:
        merged.update(headers)

    return merged


def _sleep_backoff(attempt: int, backoff_factor: float) -> None:
    delay = backoff_factor * (2 ** (attempt - 1))
    time.sleep(delay)


def _request_with_retries(
    session: requests.Session,
    url: str,
    *,
    timeout_s: float,
    headers: Mapping[str, str] | None,
    retries: int,
    backoff_factor: float,
) -> requests.Response:
    attempts = max(1, retries)
    last_exc: requests.RequestException | None = None

    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=timeout_s, headers=headers)
            if response.status_code in RETRYABLE_STATUSES and attempt < attempts:
                logger.debug(
                    "ALT RDB API returned %s for %s (attempt %s/%s), retrying",
                    response.status_code,
                    url,
                    attempt,
                    attempts,
                )
                response.close()
                _sleep_backoff(attempt, backoff_factor)
                continue
            return response
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            if attempt < attempts:
                logger.debug("Request to %s failed with %s (attempt %s/%s), retrying", url, exc, attempt, attempts)
                _sleep_backoff(attempt, backoff_factor)
                continue
            raise AltApiError(f"Failed to fetch data from ALT RDB API: {exc}") from exc
        except requests.RequestException as exc:  # other request errors are not retried
            last_exc = exc
            raise AltApiError(f"Failed to fetch data from ALT RDB API: {exc}") from exc

    # If we ever exit the loop without returning/raising above
    if last_exc is not None:
        raise AltApiError(f"Failed to fetch data from ALT RDB API: {last_exc}") from last_exc
    raise AltApiError("Failed to fetch data from ALT RDB API: unknown error")


def fetch_branch_binary_packages(
    branch: str,
    *,
    session: requests.Session | None = None,
    timeout_s: float = 30.0,
    arches: set[str] | None = None,
    max_packages: int | None = None,
    user_agent: str | None = None,
    headers: Mapping[str, str] | None = None,
    retries: int = 3,
    retry_backoff: float = 0.3,
) -> list[PackageInfo]:
    """Fetch binary packages for a branch from the ALT RDB API.

    If ``session`` is ``None``, a short-lived session is created and closed automatically.
    Caller-owned sessions are never closed. Headers are merged per request (session headers,
    then ``user_agent`` if provided, then explicit ``headers`` override everything) so
    user agents are honored even with custom sessions. Retry/backoff applies to timeouts,
    connection errors, and 5xx/429 responses.
    """
    if not branch:
        raise ValueError("branch must be a non-empty string")

    url = f"{ALT_RDB_API_BASE}/branch_binary_packages/{branch}"
    resolved_user_agent = user_agent or DEFAULT_USER_AGENT

    def _fetch_with_session(sess: requests.Session) -> list[PackageInfo]:
        merged_headers = _merge_headers(sess, user_agent=resolved_user_agent, headers=headers)
        response = _request_with_retries(
            sess,
            url,
            timeout_s=timeout_s,
            headers=merged_headers,
            retries=retries,
            backoff_factor=retry_backoff,
        )

        if response.status_code == 404:
            raise BranchNotFoundError(branch)

        if response.status_code in RETRYABLE_STATUSES and retries > 1:
            # All retryable statuses should have been retried above; reaching here means we ran out of attempts.
            snippet = response.text[:200].replace("\n", " ")
            raise AltApiError(f"ALT RDB API error {response.status_code} for {url}: {snippet}")

        if not response.ok:
            snippet = response.text[:200].replace("\n", " ")
            raise AltApiError(f"ALT RDB API error {response.status_code} for {url}: {snippet}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise AltApiError("ALT RDB API returned invalid JSON response") from exc

        return _parse_packages_payload(payload, branch=branch, arches=arches, max_packages=max_packages)

    if session is None:
        with create_session(user_agent=resolved_user_agent, retries=retries) as sess:
            return _fetch_with_session(sess)

    return _fetch_with_session(session)


def _parse_packages_payload(
    payload: dict[str, object] | list[object],
    *,
    branch: str,
    arches: set[str] | None,
    max_packages: int | None,
) -> list[PackageInfo]:
    packages_raw = payload.get("packages", []) if isinstance(payload, dict) else []
    if not isinstance(packages_raw, list):
        raise AltApiError("Unexpected ALT RDB API response shape: 'packages' is not a list")

    def to_int(value: object, *, field: str) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except Exception as exc:  # noqa: BLE001
            raise AltApiError(f"Invalid {field} value in API payload: {value!r}") from exc

    result: list[PackageInfo] = []

    for pkg in packages_raw:
        if not isinstance(pkg, dict):
            continue

        arch = str(pkg.get("arch", ""))
        if arches and arch not in arches:
            continue

        result.append(
            PackageInfo(
                name=str(pkg.get("name", "")),
                epoch=to_int(pkg.get("epoch", 0), field="epoch"),
                version=str(pkg.get("version", "")),
                release=str(pkg.get("release", "")),
                arch=arch,
                buildtime=to_int(pkg.get("buildtime", 0), field="buildtime"),
                disttag=str(pkg.get("disttag", "")),
            )
        )

        if max_packages is not None and len(result) >= max_packages:
            break

    return result


def get_branch_binary_packages(branch: str) -> dict[str, list[dict[str, object]]]:
    """Backwards-compatible wrapper returning a dict with a 'packages' list."""

    packages = fetch_branch_binary_packages(branch)
    return {"packages": [p.to_dict(branch=branch) for p in packages]}
