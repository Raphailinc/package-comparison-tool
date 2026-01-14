import re

import package_comparison_tool.compare as compare_mod
from package_comparison_tool.models import PackageInfo


def _pkg(
    name: str,
    *,
    epoch: int = 0,
    version: str = "1.0",
    release: str = "1",
    arch: str = "x86_64",
    buildtime: int = 0,
    disttag: str = "",
) -> PackageInfo:
    return PackageInfo(
        name=name,
        epoch=epoch,
        version=version,
        release=release,
        arch=arch,
        buildtime=buildtime,
        disttag=disttag,
    )


def test_compare_packages_arch_aware(monkeypatch) -> None:
    def fake_fetch(branch: str, **_kwargs):
        if branch == "a":
            return [_pkg("pkg1", version="1.0", release="1", arch="x86_64"), _pkg("pkg2", arch="noarch")]
        if branch == "b":
            return [_pkg("pkg1", version="1.0", release="2", arch="x86_64"), _pkg("pkg3", arch="noarch")]
        raise AssertionError(branch)

    monkeypatch.setattr(compare_mod, "fetch_branch_binary_packages", fake_fetch)

    result = compare_mod.compare_packages("a", "b")
    assert result["stats"]["only_in_branch1"] == 1
    assert result["stats"]["only_in_branch2"] == 1
    assert result["stats"]["higher_in_branch1"] == 0
    assert result["stats"]["higher_in_branch2"] == 1


def test_compare_packages_keeps_highest_evr_per_key(monkeypatch) -> None:
    def fake_fetch(branch: str, **_kwargs):
        if branch == "a":
            return [
                _pkg("pkg1", version="1.0", release="1", arch="x86_64"),
                _pkg("pkg1", version="1.0", release="2", arch="x86_64"),
            ]
        if branch == "b":
            return [_pkg("pkg1", version="1.0", release="1", arch="x86_64")]
        raise AssertionError(branch)

    monkeypatch.setattr(compare_mod, "fetch_branch_binary_packages", fake_fetch)

    result = compare_mod.compare_packages("a", "b")
    assert result["stats"]["higher_in_branch1"] == 1
    assert result["packages_with_higher_version_in_branch1"][0]["release"] == "2"


def test_compare_packages_ignore_arch(monkeypatch) -> None:
    def fake_fetch(branch: str, **_kwargs):
        if branch == "a":
            return [_pkg("pkg1", version="2.0", release="1", arch="aarch64")]
        if branch == "b":
            return [_pkg("pkg1", version="1.0", release="1", arch="x86_64")]
        raise AssertionError(branch)

    monkeypatch.setattr(compare_mod, "fetch_branch_binary_packages", fake_fetch)

    result = compare_mod.compare_packages("a", "b", ignore_arch=True)
    assert result["stats"]["higher_in_branch1"] == 1


def test_compare_packages_filters_by_name(monkeypatch) -> None:
    def fake_fetch(branch: str, **_kwargs):
        if branch == "a":
            return [_pkg("keepme"), _pkg("skipme")]
        if branch == "b":
            return [_pkg("keepme"), _pkg("another")]
        raise AssertionError(branch)

    monkeypatch.setattr(compare_mod, "fetch_branch_binary_packages", fake_fetch)

    patterns = (re.compile("keep"),)
    result = compare_mod.compare_packages("a", "b", name_patterns=patterns)
    assert result["stats"]["differences"] == 0
    assert result["stats"]["total_branch1_indexed"] == 1
    assert result["stats"]["total_branch2_indexed"] == 1
