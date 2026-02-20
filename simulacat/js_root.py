"""Command-line helper for resolving simulacat's JavaScript package root.

This module provides a stable command for shell scripts and CI workflows:

    python -m simulacat.js_root

The command prints the absolute directory containing simulacat's bundled
`package.json`, suitable for `bun install --cwd ...`.
"""

from __future__ import annotations

import sys

from simulacat.orchestration import GitHubSimProcessError, sim_package_root


def main() -> int:
    """Print the JavaScript package root and return a process exit code."""
    try:
        package_root = sim_package_root()
    except GitHubSimProcessError as exc:
        print(f"Failed to resolve SIMULACAT_JS_ROOT: {exc}", file=sys.stderr)
        return 1

    print(package_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
