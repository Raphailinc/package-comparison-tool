from __future__ import annotations

import re
import sys

import click

from .compare import compare_packages
from .formatting import render_result


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("branch1", required=False, default="sisyphus")
@click.argument("branch2", required=False, default="p10")
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.Path(dir_okay=False, writable=True, path_type=str),
    help="Output file path, or '-' for stdout.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "summary", "markdown", "text"], case_sensitive=False),
    default="json",
    show_default=True,
    help="Output format.",
)
@click.option("--pretty/--no-pretty", default=True, help="Pretty-print JSON output.")
@click.option(
    "--arch",
    "arches",
    multiple=True,
    help="Filter by architecture (repeatable), e.g. --arch x86_64 --arch noarch",
)
@click.option(
    "--ignore-arch",
    is_flag=True,
    default=False,
    help="Compare packages by name only (ignores architecture).",
)
@click.option("--timeout", "timeout_s", default=30.0, show_default=True, type=float)
@click.option(
    "--max-packages",
    default=None,
    type=int,
    hidden=True,
    help="Debug-only: limit packages fetched per branch.",
)
@click.option(
    "--limit",
    type=int,
    default=25,
    show_default=True,
    help="Limit rows shown in human-readable formats (use 0 for unlimited).",
)
@click.option(
    "--filter",
    "name_filters",
    multiple=True,
    help="Only include packages whose name matches the given regex (repeatable).",
)
@click.option(
    "--fail-on-diff",
    is_flag=True,
    default=False,
    help="Return exit code 1 if any differences are found (useful for CI).",
)
@click.option(
    "--user-agent",
    default=None,
    help="Custom User-Agent header for API requests.",
)
def main(
    branch1: str,
    branch2: str,
    output: str,
    output_format: str,
    pretty: bool,
    arches: tuple[str, ...],
    ignore_arch: bool,
    timeout_s: float,
    max_packages: int | None,
    limit: int,
    name_filters: tuple[str, ...],
    fail_on_diff: bool,
    user_agent: str | None,
) -> None:
    """Compare binary packages between two ALT Linux branches."""

    name_patterns = []
    for pattern in name_filters:
        try:
            name_patterns.append(re.compile(pattern, re.IGNORECASE))
        except re.error as exc:
            raise click.BadParameter(f"Invalid regex '{pattern}': {exc}") from exc

    arches_set = {a.strip() for a in arches if a.strip()} or None

    click.echo(f"Fetching and comparing: {branch1} vs {branch2}", err=True)
    if arches_set:
        click.echo(f"Arch filter: {', '.join(sorted(arches_set))}", err=True)
    if name_patterns:
        click.echo(f"Name filter patterns: {', '.join(p.pattern for p in name_patterns)}", err=True)

    result = compare_packages(
        branch1,
        branch2,
        ignore_arch=ignore_arch,
        arches=arches_set,
        timeout_s=timeout_s,
        max_packages=max_packages,
        name_patterns=tuple(name_patterns) if name_patterns else None,
        user_agent=user_agent,
    )

    payload = render_result(result, fmt=output_format, pretty=pretty, limit=limit)

    if output == "-":
        sys.stdout.write(payload)
    else:
        with open(output, "w", encoding="utf8") as f:
            f.write(payload)
        click.echo(f"Wrote {output}", err=True)

    stats = result.get("stats", {}) if isinstance(result, dict) else {}
    differences = int(stats.get("differences", 0)) if isinstance(stats, dict) else 0
    if fail_on_diff and differences > 0:
        raise SystemExit(1)
