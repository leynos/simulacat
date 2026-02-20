"""Install bundled simulator JavaScript dependencies.

This module centralizes dependency installation for simulator-backed tests in
local development and CI:

    python -m simulacat.install_simulator_deps

The command resolves the installed simulacat JavaScript package root and runs
`bun install --cwd <resolved-root>`.
"""

from __future__ import annotations

# S404: subprocess is required to invoke Bun without shell expansion.
import subprocess  # noqa: S404  # simulacat#123: run Bun install via explicit args; shell=False
import sys
import typing as typ

from simulacat.orchestration import GitHubSimProcessError, sim_package_root

if typ.TYPE_CHECKING:
    from pathlib import Path


def install_simulator_dependencies(*, bun_executable: str = "bun") -> Path:
    """Install simulator JavaScript dependencies via Bun.

    Parameters
    ----------
    bun_executable
        Executable name or path for Bun.

    Returns
    -------
    Path
        The resolved directory that contains simulacat's `package.json`.

    Raises
    ------
    GitHubSimProcessError
        If the package root cannot be resolved, Bun cannot be executed, or
        dependency installation fails.

    """
    package_root = sim_package_root()
    command = [bun_executable, "install", "--cwd", str(package_root)]
    try:
        # S603: command arguments are fixed executable + validated path.
        result = subprocess.run(command, check=False)  # noqa: S603  # simulacat#123: explicit command list only; shell=False
    except FileNotFoundError as exc:
        msg = f"Bun executable not found: {bun_executable}"
        raise GitHubSimProcessError(msg) from exc

    if result.returncode != 0:
        msg = (
            "Failed to install simulator dependencies with command: "
            f"{' '.join(command)}"
        )
        raise GitHubSimProcessError(msg)

    return package_root


def main() -> int:
    """Run dependency installation and return a process exit code.

    Returns
    -------
    int
        `0` when dependency installation succeeds; otherwise `1` after writing
        an error message to stderr.

    """
    try:
        package_root = install_simulator_dependencies()
    except GitHubSimProcessError as exc:
        print(f"Failed to install simulator dependencies: {exc}", file=sys.stderr)
        return 1

    print(f"Installed simulator dependencies in {package_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
