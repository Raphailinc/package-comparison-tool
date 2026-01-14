from __future__ import annotations

from dataclasses import dataclass


def _is_separators_only_or_zeros(value: str, start: int) -> bool:
    i = start
    n = len(value)

    while True:
        while i < n and not value[i].isalnum() and value[i] not in "~^":
            i += 1

        if i >= n:
            return True

        if value[i] in "~^":
            return False

        if value[i].isdigit():
            j = i
            while j < n and value[j].isdigit():
                j += 1

            if any(ch != "0" for ch in value[i:j]):
                return False

            i = j
            continue

        return False


def _cmp_segment_numeric(a: str, b: str) -> int:
    a_stripped = a.lstrip("0") or "0"
    b_stripped = b.lstrip("0") or "0"

    if len(a_stripped) != len(b_stripped):
        return 1 if len(a_stripped) > len(b_stripped) else -1

    if a_stripped == b_stripped:
        return 0

    return 1 if a_stripped > b_stripped else -1


def rpmvercmp(a: str | None, b: str | None) -> int:
    """Compare RPM-like version segments.

    This implementation follows the general behavior of RPM's version comparison:
    - splits into numeric and alpha segments
    - compares numeric segments as integers
    - compares alpha segments lexicographically
    - '~' sorts before everything
    - treats trailing ".0" segments as equal
    """

    a = a or ""
    b = b or ""

    i = 0
    j = 0
    na = len(a)
    nb = len(b)

    while True:
        ca = a[i] if i < na else ""
        cb = b[j] if j < nb else ""

        if ca == "~" or cb == "~":
            if ca != "~":
                return 1
            if cb != "~":
                return -1
            i += 1
            j += 1
            continue

        if ca == "^" or cb == "^":
            if ca != "^":
                return 1
            if cb != "^":
                return -1
            i += 1
            j += 1
            continue

        while i < na and not a[i].isalnum() and a[i] not in "~^":
            i += 1
        while j < nb and not b[j].isalnum() and b[j] not in "~^":
            j += 1

        if i >= na and j >= nb:
            return 0

        if i >= na:
            if _is_separators_only_or_zeros(b, j):
                return 0
            return -1 if b[j].isdigit() else 1

        if j >= nb:
            if _is_separators_only_or_zeros(a, i):
                return 0
            return 1 if a[i].isdigit() else -1

        is_num_a = a[i].isdigit()
        is_num_b = b[j].isdigit()

        if is_num_a and not is_num_b:
            return 1
        if is_num_b and not is_num_a:
            return -1

        if is_num_a:
            ia = i
            ib = j

            while ia < na and a[ia].isdigit():
                ia += 1
            while ib < nb and b[ib].isdigit():
                ib += 1

            seg_a = a[i:ia]
            seg_b = b[j:ib]

            rc = _cmp_segment_numeric(seg_a, seg_b)
            if rc != 0:
                return rc

            i = ia
            j = ib
            continue

        ia = i
        ib = j

        while ia < na and a[ia].isalpha():
            ia += 1
        while ib < nb and b[ib].isalpha():
            ib += 1

        seg_a = a[i:ia]
        seg_b = b[j:ib]

        if seg_a != seg_b:
            return 1 if seg_a > seg_b else -1

        i = ia
        j = ib


@dataclass(frozen=True, slots=True)
class EVR:
    epoch: int
    version: str
    release: str


def compare_evr(a: EVR, b: EVR) -> int:
    if a.epoch != b.epoch:
        return 1 if a.epoch > b.epoch else -1

    rc = rpmvercmp(a.version, b.version)
    if rc != 0:
        return rc

    return rpmvercmp(a.release, b.release)


def compare_version_release(version_release1: str, version_release2: str) -> int:
    """Backwards-compatible helper: compares 'version-release' strings."""

    def split(vr: str) -> tuple[str, str]:
        if "-" not in vr:
            return vr, ""
        version, release = vr.split("-", 1)
        return version, release

    v1, r1 = split(version_release1)
    v2, r2 = split(version_release2)
    return compare_evr(EVR(epoch=0, version=v1, release=r1), EVR(epoch=0, version=v2, release=r2))

