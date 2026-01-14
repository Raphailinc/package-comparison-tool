from __future__ import annotations

import json
from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def _evr(pkg: dict[str, object]) -> str:
    epoch = pkg.get("epoch") or 0
    version = pkg.get("version") or ""
    release = pkg.get("release") or ""
    evr = f"{version}-{release}".strip("-")
    if epoch:
        return f"{epoch}:{evr}"
    return evr


def _limit_items(items: Iterable[T], limit: int | None) -> tuple[list[T], bool]:
    normalized_limit = None if limit is None or limit <= 0 else limit
    if normalized_limit is None:
        return list(items), False

    collected: list[T] = []
    for idx, item in enumerate(items):
        if idx >= normalized_limit:
            return collected, True
        collected.append(item)
    return collected, False


def _format_pkg_line(pkg: dict[str, object]) -> str:
    arch = pkg.get("arch", "")
    evr = _evr(pkg)
    name = str(pkg.get("name", ""))
    return f"{name} {evr} [{arch}]"


def format_summary(result: dict[str, object], *, limit: int | None = None) -> str:
    stats = result.get("stats", {}) if isinstance(result, dict) else {}
    branch1 = result.get("branch1", "") if isinstance(result, dict) else ""
    branch2 = result.get("branch2", "") if isinstance(result, dict) else ""
    generated_at = result.get("generated_at", "") if isinstance(result, dict) else ""

    lines = [
        f"Comparison: {branch1} vs {branch2}",
        f"Generated at: {generated_at}",
        f"Only in {branch1}: {stats.get('only_in_branch1', 0)}",
        f"Only in {branch2}: {stats.get('only_in_branch2', 0)}",
        f"Higher versions in {branch1}: {stats.get('higher_in_branch1', 0)}",
        f"Higher versions in {branch2}: {stats.get('higher_in_branch2', 0)}",
        f"Total differences: {stats.get('differences', 0)}",
    ]

    sections = [
        ("Only in " + str(branch1), result.get("packages_only_in_branch1", [])),
        ("Only in " + str(branch2), result.get("packages_only_in_branch2", [])),
        (
            "Higher in " + str(branch1),
            result.get("packages_with_higher_version_in_branch1", []),
        ),
        (
            "Higher in " + str(branch2),
            result.get("packages_with_higher_version_in_branch2", []),
        ),
    ]

    for title, items_obj in sections:
        if not isinstance(items_obj, Iterable):
            continue

        items, truncated = _limit_items(items_obj, limit)
        if not items and not truncated:
            continue

        lines.append("")
        lines.append(f"{title}:")
        for pkg in items:
            if not isinstance(pkg, dict):
                continue
            lines.append(f"- {_format_pkg_line(pkg)}")
        if truncated:
            lines.append(f"... and more (limited to first {limit})")

    return "\n".join(lines).rstrip() + "\n"


def _markdown_table(items: Iterable[dict[str, object]], limit: int | None = None) -> list[str]:
    rows, truncated = _limit_items(items, limit)
    lines = ["| Name | EVR | Arch | Branch | Disttag |", "| --- | --- | --- | --- | --- |"]

    for pkg in rows:
        if not isinstance(pkg, dict):
            continue
        name = str(pkg.get("name", ""))
        url = str(pkg.get("url", "")) if pkg.get("url") else ""
        name_cell = f"[{name}]({url})" if url else name
        evr = _evr(pkg)
        arch = pkg.get("arch", "")
        branch = pkg.get("branch", "")
        disttag = pkg.get("disttag", "")
        lines.append(f"| {name_cell} | {evr} | {arch} | {branch} | {disttag} |")

    if truncated:
        lines.append(f"| … | … | … | … | showing first {limit} |")
    return lines


def format_markdown(result: dict[str, object], *, limit: int | None = None) -> str:
    branch1 = result.get("branch1", "") if isinstance(result, dict) else ""
    branch2 = result.get("branch2", "") if isinstance(result, dict) else ""
    stats = result.get("stats", {}) if isinstance(result, dict) else {}
    generated_at = result.get("generated_at", "") if isinstance(result, dict) else ""

    lines = [
        f"# Package comparison: {branch1} vs {branch2}",
        "",
        f"- Generated at: `{generated_at}`",
        f"- Total differences: `{stats.get('differences', 0)}`",
        f"- Only in {branch1}: `{stats.get('only_in_branch1', 0)}`",
        f"- Only in {branch2}: `{stats.get('only_in_branch2', 0)}`",
        f"- Higher in {branch1}: `{stats.get('higher_in_branch1', 0)}`",
        f"- Higher in {branch2}: `{stats.get('higher_in_branch2', 0)}`",
    ]

    sections = [
        ("Only in " + str(branch1), result.get("packages_only_in_branch1", [])),
        ("Only in " + str(branch2), result.get("packages_only_in_branch2", [])),
        (
            "Higher in " + str(branch1),
            result.get("packages_with_higher_version_in_branch1", []),
        ),
        (
            "Higher in " + str(branch2),
            result.get("packages_with_higher_version_in_branch2", []),
        ),
    ]

    for title, items in sections:
        if not isinstance(items, Iterable):
            continue
        lines.append("")
        lines.append(f"## {title}")
        lines.extend(_markdown_table(items, limit=limit))

    return "\n".join(lines).rstrip() + "\n"


def format_json(result: dict[str, object], *, pretty: bool = True) -> str:
    json_kwargs: dict[str, object] = {"ensure_ascii": False}
    if pretty:
        json_kwargs.update({"indent": 2, "sort_keys": True})

    return json.dumps(result, **json_kwargs) + "\n"


def render_result(
    result: dict[str, object], *, fmt: str, pretty: bool = True, limit: int | None = None
) -> str:
    fmt = fmt.lower()
    if fmt == "json":
        return format_json(result, pretty=pretty)
    if fmt == "markdown":
        return format_markdown(result, limit=limit)
    if fmt in {"summary", "text"}:
        return format_summary(result, limit=limit)

    raise ValueError(f"Unknown format: {fmt}")
