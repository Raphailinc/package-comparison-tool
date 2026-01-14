# Package Comparison Tool (altpkg-diff)

CLI and library for diffing ALT Linux binary packages between branches. Fetches both branches in parallel with retries and outputs JSON, human-readable summaries, or GitHub-ready Markdown.

## Highlights
- JSON, summary, and Markdown outputs; `--limit` keeps human output compact (set `0` for unlimited).
- Filters: architectures (`--arch`), regex by package name (`--filter`), and name-only comparison (`--ignore-arch`).
- CI-friendly: `--fail-on-diff` exits with code `1` when differences are found.
- Resilient HTTP client with retries, timeouts, and customizable `--user-agent`.
- New CLI alias `altpkg-diff` (keeps `package-comparison` for compatibility).

## Installation
```bash
git clone https://github.com/Raphailinc/package-comparison-tool.git
cd package-comparison-tool
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
```

Or install directly via pip:
```bash
pip install git+https://github.com/Raphailinc/package-comparison-tool.git
```

## CLI usage
```bash
# defaults: sisyphus vs p10, JSON to stdout
package-comparison

# same tool via shorter alias
altpkg-diff sisyphus p10 --format summary

# GitHub-ready Markdown report (first 25 rows shown) saved to file
package-comparison sisyphus p10 --format markdown --limit 25 -o report.md

# CI mode: fail on any differences, ignore arch suffixes, filter only nginx packages
package-comparison p10 sisyphus --ignore-arch --filter nginx --fail-on-diff
```

Key options:
- `--format json|summary|markdown|text` – choose output format (JSON honors `--pretty/--no-pretty`).
- `--filter REGEX` – repeatable regex for package names (case-insensitive).
- `--arch ARCH` – repeatable arch filter; `--ignore-arch` compares by name only.
- `--limit N` – limit rows in human-readable formats (Markdown/summary); `0` shows everything.
- `--fail-on-diff` – exit with code `1` when differences exist (useful for CI/pipelines).
- `--timeout`, `--user-agent` – tune HTTP behavior.

## Library use
```python
from package_comparison_tool.compare import compare_packages

result = compare_packages(
    "sisyphus",
    "p10",
    ignore_arch=False,
    arches={"x86_64", "noarch"},
    name_patterns=None,
)

print(result["stats"])
# {'only_in_branch1': ..., 'differences': ...}
```

## Development
- Run tests: `pytest`
- Lint: `ruff check .`

## License
MIT – see [LICENSE](LICENSE).
