from __future__ import annotations

import pytest

from package_comparison_tool.formatting import format_markdown, format_summary, render_result


def _pkg(name: str, branch: str) -> dict[str, object]:
    return {
        "branch": branch,
        "name": name,
        "epoch": 0,
        "version": "1.0",
        "release": "1",
        "arch": "x86_64",
        "buildtime": 0,
        "disttag": "tag",
        "url": f"https://example.test/{branch}/{name}",
    }


def _sample_result() -> dict[str, object]:
    return {
        "branch1": "a",
        "branch2": "b",
        "generated_at": "2024-01-01T00:00:00Z",
        "packages_only_in_branch1": [_pkg("pkg-a", "a")],
        "packages_only_in_branch2": [_pkg("pkg-b", "b")],
        "packages_with_higher_version_in_branch1": [],
        "packages_with_higher_version_in_branch2": [],
        "stats": {
            "only_in_branch1": 1,
            "only_in_branch2": 1,
            "higher_in_branch1": 0,
            "higher_in_branch2": 0,
            "total_branch1_indexed": 1,
            "total_branch2_indexed": 1,
            "differences": 2,
        },
    }


def test_format_summary_truncates() -> None:
    result = _sample_result()
    result["packages_only_in_branch1"].append(_pkg("pkg-c", "a"))

    output = format_summary(result, limit=1)
    assert "pkg-a" in output
    assert "... and more" in output


def test_format_markdown_contains_links() -> None:
    output = format_markdown(_sample_result(), limit=5)
    assert "| Name | EVR | Arch | Branch | Disttag |" in output
    assert "[pkg-a]" in output
    assert "(https://example.test/a/pkg-a)" in output


def test_render_result_unknown_format() -> None:
    with pytest.raises(ValueError):
        render_result(_sample_result(), fmt="xml")
