from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, closing
from datetime import datetime, timezone
from re import Pattern

import requests

from .api import fetch_branch_binary_packages
from .models import PackageInfo
from .version import EVR, compare_evr

logger = logging.getLogger(__name__)


def _pkg_key(pkg: PackageInfo, *, ignore_arch: bool) -> tuple[str, str] | str:
    return pkg.name if ignore_arch else (pkg.name, pkg.arch)


def _index_packages(
    packages: list[PackageInfo], *, ignore_arch: bool
) -> dict[tuple[str, str] | str, PackageInfo]:
    index: dict[tuple[str, str] | str, PackageInfo] = {}
    for pkg in packages:
        key = _pkg_key(pkg, ignore_arch=ignore_arch)
        existing = index.get(key)
        if existing is None:
            index[key] = pkg
            continue

        if (
            compare_evr(
                EVR(epoch=pkg.epoch, version=pkg.version, release=pkg.release),
                EVR(epoch=existing.epoch, version=existing.version, release=existing.release),
            )
            > 0
        ):
            index[key] = pkg

    return index


def compare_packages(
    branch1: str,
    branch2: str,
    *,
    ignore_arch: bool = False,
    arches: set[str] | None = None,
    timeout_s: float = 30.0,
    session: requests.Session | None = None,
    max_packages: int | None = None,
    name_patterns: Iterable[Pattern[str]] | None = None,
    user_agent: str | None = None,
    headers: dict[str, str] | None = None,
    retries: int = 3,
    retry_backoff: float = 0.3,
    session_factory: Callable[[], requests.Session] | None = None,
    allow_concurrency_with_session: bool = False,
) -> dict[str, object]:
    """Compare binary packages between two ALT branches.

    Returns a JSON-serializable dict.

    When ``session`` is provided, calls are sequential by default to avoid sharing a
    potentially non-thread-safe session across threads. To regain parallel fetches, pass
    ``allow_concurrency_with_session=True`` (the session will be cloned) or provide a
    ``session_factory`` that returns independent sessions for each branch. Sessions created
    via ``session_factory`` are closed automatically; caller-provided sessions are not.
    """

    compiled_patterns = list(name_patterns) if name_patterns else None

    def _filter_by_name(packages: list[PackageInfo]) -> list[PackageInfo]:
        if not compiled_patterns:
            return packages
        return [pkg for pkg in packages if any(p.search(pkg.name) for p in compiled_patterns)]

    fetch_kwargs = dict(
        timeout_s=timeout_s,
        arches=arches,
        max_packages=max_packages,
        user_agent=user_agent,
        headers=headers,
        retries=retries,
        retry_backoff=retry_backoff,
    )

    def _fetch(branch: str, *, sess: requests.Session | None) -> list[PackageInfo]:
        return fetch_branch_binary_packages(branch, session=sess, **fetch_kwargs)  # type: ignore[arg-type]

    def _parallel(
        sess1: requests.Session | None,
        sess2: requests.Session | None,
    ) -> tuple[list[PackageInfo], list[PackageInfo]]:
        with ThreadPoolExecutor(max_workers=2) as pool:
            future1 = pool.submit(_fetch, branch1, sess=sess1)
            future2 = pool.submit(_fetch, branch2, sess=sess2)
            return future1.result(), future2.result()

    packages1: list[PackageInfo]
    packages2: list[PackageInfo]

    if session_factory is not None:
        with ExitStack() as stack:
            sess1 = stack.enter_context(closing(session_factory()))
            sess2 = stack.enter_context(closing(session_factory()))
            packages1, packages2 = _parallel(sess1, sess2)
    elif session is None:
        packages1, packages2 = _parallel(None, None)
    elif allow_concurrency_with_session:
        with ExitStack() as stack:
            # Clone caller-provided session to avoid cross-thread use of a single Session
            sess1 = stack.enter_context(closing(_clone_session(session)))
            sess2 = stack.enter_context(closing(_clone_session(session)))
            packages1, packages2 = _parallel(sess1, sess2)
    else:
        logger.debug("Using sequential fetch because a session was provided and allow_concurrency_with_session=False")
        packages1 = _fetch(branch1, sess=session)
        packages2 = _fetch(branch2, sess=session)

    packages1 = _filter_by_name(packages1)
    packages2 = _filter_by_name(packages2)

    idx1 = _index_packages(packages1, ignore_arch=ignore_arch)
    idx2 = _index_packages(packages2, ignore_arch=ignore_arch)

    only1: list[PackageInfo] = []
    only2: list[PackageInfo] = []
    higher1: list[PackageInfo] = []
    higher2: list[PackageInfo] = []

    keys1 = set(idx1.keys())
    keys2 = set(idx2.keys())

    for key in keys1 - keys2:
        only1.append(idx1[key])
    for key in keys2 - keys1:
        only2.append(idx2[key])

    for key in keys1 & keys2:
        a = idx1[key]
        b = idx2[key]
        rc = compare_evr(
            EVR(epoch=a.epoch, version=a.version, release=a.release),
            EVR(epoch=b.epoch, version=b.version, release=b.release),
        )
        if rc > 0:
            higher1.append(a)
        elif rc < 0:
            higher2.append(b)

    sort_key = (lambda p: (p.name, p.arch)) if not ignore_arch else (lambda p: p.name)
    only1.sort(key=sort_key)
    only2.sort(key=sort_key)
    higher1.sort(key=sort_key)
    higher2.sort(key=sort_key)

    generated_at = datetime.now(timezone.utc).isoformat()
    diff_total = len(only1) + len(only2) + len(higher1) + len(higher2)

    result: dict[str, object] = {
        "branch1": branch1,
        "branch2": branch2,
        "generated_at": generated_at,
        "packages_only_in_branch1": [p.to_dict(branch=branch1) for p in only1],
        "packages_only_in_branch2": [p.to_dict(branch=branch2) for p in only2],
        "packages_with_higher_version_in_branch1": [p.to_dict(branch=branch1) for p in higher1],
        "packages_with_higher_version_in_branch2": [p.to_dict(branch=branch2) for p in higher2],
        "stats": {
            "only_in_branch1": len(only1),
            "only_in_branch2": len(only2),
            "higher_in_branch1": len(higher1),
            "higher_in_branch2": len(higher2),
            "total_branch1_indexed": len(idx1),
            "total_branch2_indexed": len(idx2),
            "differences": diff_total,
        },
    }

    return result


def _clone_session(base: requests.Session) -> requests.Session:
    """Create a lightweight copy of a requests.Session for safe parallel use."""

    clone = requests.Session()
    clone.headers.update(base.headers)
    clone.cookies.update(base.cookies)
    clone.auth = base.auth
    clone.verify = base.verify
    clone.cert = base.cert
    clone.proxies = dict(base.proxies)
    clone.trust_env = base.trust_env

    return clone
