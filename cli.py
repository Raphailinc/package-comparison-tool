"""Legacy entrypoint (kept for compatibility).

Prefer:
  python -m package_comparison_tool.cli
or after installation:
  package-comparison <branch1> <branch2>
"""

from __future__ import annotations

from package_comparison_tool.cli import main

if __name__ == "__main__":
    main()
