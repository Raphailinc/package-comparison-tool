from __future__ import annotations

from typing import Iterable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import __version__
from .exceptions import AltApiError, BranchNotFoundError
from .models import PackageInfo

ALT_RDB_API_BASE = "https://rdb.altlinux.org/api/export"


def create_session(*, user_agent: str | None = None, retries: int = 3) -> requests.Session:
    session = requests.Session()
    if user_agent:
        session.headers.update({"User-Agent": user_agent})

    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=0.3,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_branch_binary_packages(
    branch: str,
    *,
    session: requests.Session | None = None,
    timeout_s: float = 30.0,
    arches: set[str] | None = None,
    max_packages: int | None = None,
    user_agent: str | None = None,
) -> list[PackageInfo]:
    if not branch:
        raise ValueError("branch must be a non-empty string")

    url = f"{ALT_RDB_API_BASE}/branch_binary_packages/{branch}"
    default_ua = f"package-comparison-tool/{__version__}"
    sess = session or create_session(user_agent=user_agent or default_ua)

    try:
        response = sess.get(url, timeout=timeout_s)
    except requests.RequestException as exc:
        raise AltApiError(f"Failed to fetch data from ALT RDB API: {exc}") from exc

    if response.status_code == 404:
        raise BranchNotFoundError(branch)

    if not response.ok:
        snippet = response.text[:200].replace("\n", " ")
        raise AltApiError(f"ALT RDB API error {response.status_code}: {snippet}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise AltApiError("ALT RDB API returned invalid JSON") from exc

    packages_raw = payload.get("packages", [])
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
