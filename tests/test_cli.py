from __future__ import annotations

from click.testing import CliRunner

import package_comparison_tool.cli as cli


def _sample_result() -> dict[str, object]:
    return {
        "branch1": "a",
        "branch2": "b",
        "generated_at": "2024-01-01T00:00:00Z",
        "packages_only_in_branch1": [],
        "packages_only_in_branch2": [
            {
                "name": "pkg-a",
                "version": "1",
                "release": "1",
                "arch": "x86_64",
                "epoch": 0,
                "disttag": "",
                "branch": "b",
            }
        ],
        "packages_with_higher_version_in_branch1": [],
        "packages_with_higher_version_in_branch2": [],
        "stats": {
            "only_in_branch1": 0,
            "only_in_branch2": 1,
            "higher_in_branch1": 0,
            "higher_in_branch2": 0,
            "total_branch1_indexed": 0,
            "total_branch2_indexed": 1,
            "differences": 1,
        },
    }


def test_cli_fail_on_diff(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(cli, "compare_packages", lambda *args, **kwargs: _sample_result())

    result = runner.invoke(cli.main, ["--format", "summary", "--fail-on-diff"])

    assert result.exit_code == 1
    assert "Total differences" in result.output


def test_cli_invalid_regex_exits(monkeypatch) -> None:
    runner = CliRunner()

    result = runner.invoke(cli.main, ["--filter", "["])

    assert result.exit_code != 0
    assert "Invalid regex" in result.output


def test_cli_branch_not_found(monkeypatch) -> None:
    runner = CliRunner()

    def _raise_branch(*_args, **_kwargs):
        raise cli.BranchNotFoundError("missing")

    monkeypatch.setattr(cli, "compare_packages", _raise_branch)

    result = runner.invoke(cli.main, ["sisyphus", "p10"])

    assert result.exit_code == 2
    assert "Error: Branch \"missing\" not found" in result.output
    assert "Traceback" not in result.output


def test_cli_alt_api_error(monkeypatch) -> None:
    runner = CliRunner()

    def _raise_alt(*_args, **_kwargs):
        raise cli.AltApiError("network down")

    monkeypatch.setattr(cli, "compare_packages", _raise_alt)

    result = runner.invoke(cli.main, ["sisyphus", "p10"])

    assert result.exit_code == 1
    assert "Error: network down" in result.output
    assert "Traceback" not in result.output


def test_cli_debug_shows_traceback(monkeypatch) -> None:
    runner = CliRunner()

    def _raise_alt(*_args, **_kwargs):
        raise cli.AltApiError("boom")

    monkeypatch.setattr(cli, "compare_packages", _raise_alt)

    result = runner.invoke(cli.main, ["sisyphus", "p10", "--debug"])

    assert result.exit_code == 1
    assert "Error: boom" in result.output
    assert "Traceback (most recent call last)" in result.output
