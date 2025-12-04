"""Simulator process orchestration for simulacat.

This module manages the lifecycle of the Bun-based GitHub API simulator,
handling process startup, port discovery, and cleanup.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess  # noqa: S404
import time
import typing as typ
from pathlib import Path

if typ.TYPE_CHECKING:
    import collections.abc as cabc


class GitHubSimProcessError(RuntimeError):
    """Exception raised when the simulator process fails to start or run."""


def sim_entrypoint() -> Path:
    """Return the path to the simulator entry point script.

    Returns
    -------
    Path
        Absolute path to the github-sim-server.ts file.

    """
    package_root = Path(__file__).resolve().parent.parent
    return package_root / "src" / "github-sim-server.ts"


def _empty_initial_state() -> dict[str, list[typ.Any]]:
    """Return the minimal valid initial state for the simulator.

    Returns
    -------
    dict
        A dictionary with empty arrays for required simulator fields.

    """
    return {
        "users": [],
        "organizations": [],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }


def _write_config(
    config: cabc.Mapping[str, typ.Any],
    tmpdir: Path,
) -> Path:
    """Write simulator configuration to a temporary file."""
    effective_config: dict[str, typ.Any] = dict(config) if config else {}
    if not effective_config:
        effective_config = _empty_initial_state()

    config_path = tmpdir / "github-sim-config.json"
    config_path.write_text(json.dumps(effective_config), encoding="utf-8")
    return config_path


def _spawn_process(
    bun_executable: str,
    entrypoint: Path,
    config_path: Path,
) -> subprocess.Popen[str]:
    """Spawn the simulator process."""
    try:
        return subprocess.Popen(  # noqa: S603
            [bun_executable, str(entrypoint), str(config_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as exc:
        msg = f"Bun executable not found: {bun_executable}"
        raise GitHubSimProcessError(msg) from exc


def _parse_event(line: str) -> dict[str, typ.Any] | None:
    """Parse a JSON event line, returning None if parsing fails."""
    try:
        evt = json.loads(line)
        if isinstance(evt, dict):
            return evt
    except json.JSONDecodeError:
        pass
    return None


def _wait_for_port(
    proc: subprocess.Popen[str],
    startup_timeout: float,
) -> int:
    """Wait for the simulator to report its listening port."""
    if proc.stdout is None:
        msg = "Failed to capture simulator stdout"
        raise GitHubSimProcessError(msg)

    output_lines: list[str] = []
    deadline = time.time() + startup_timeout

    while time.time() < deadline:
        line = proc.stdout.readline()
        if line == "":
            if proc.poll() is not None:
                break
            time.sleep(0.05)
            continue

        output_lines.append(line)
        evt = _parse_event(line)

        if evt is None:
            continue

        if evt.get("event") == "listening":
            try:
                return int(evt["port"])
            except (KeyError, TypeError, ValueError) as exc:
                msg = f"Invalid listening event from simulator: {evt!r}"
                raise GitHubSimProcessError(msg) from exc

        if evt.get("event") == "error":
            error_msg = evt.get("message", "Unknown error")
            msg = f"Simulator error: {error_msg}"
            raise GitHubSimProcessError(msg)

    _cleanup_failed_process(proc, output_lines)
    msg = "Unreachable"
    raise AssertionError(msg)


def _cleanup_failed_process(
    proc: subprocess.Popen[str],
    output_lines: list[str],
) -> typ.NoReturn:
    """Clean up a failed process and raise an error."""
    try:
        remaining, _ = proc.communicate(timeout=1)
        if remaining:
            output_lines.append(remaining)
    except subprocess.TimeoutExpired:
        pass

    with contextlib.suppress(OSError):
        proc.terminate()

    msg = (
        "Simulator did not report a listening port.\n"
        f"Exit code: {proc.poll()}\n"
        f"Output:\n{''.join(output_lines)}"
    )
    raise GitHubSimProcessError(msg)


def start_sim_process(
    config: cabc.Mapping[str, typ.Any],
    tmpdir: Path,
    *,
    bun_executable: str | None = None,
    startup_timeout: float = 30.0,
) -> tuple[subprocess.Popen[str], int]:
    """Start the simulator process and wait for it to report a listening port.

    Parameters
    ----------
    config
        Configuration mapping to pass to the simulator. If empty, a minimal
        valid configuration with empty arrays will be used.
    tmpdir
        Directory where the configuration file will be written.
    bun_executable
        Path to the bun executable. Defaults to the BUN environment variable
        or "bun".
    startup_timeout
        Maximum seconds to wait for the simulator to start.

    Returns
    -------
    tuple[subprocess.Popen[str], int]
        A tuple of (process handle, port number).

    Raises
    ------
    GitHubSimProcessError
        If the simulator fails to start or does not report a port within
        the timeout.

    """
    bun_executable = bun_executable or os.environ.get("BUN", "bun")
    entrypoint = sim_entrypoint()

    if not entrypoint.is_file():
        msg = f"Simulator entry point not found: {entrypoint}"
        raise GitHubSimProcessError(msg)

    config_path = _write_config(config, tmpdir)
    proc = _spawn_process(bun_executable, entrypoint, config_path)
    port = _wait_for_port(proc, startup_timeout)

    return proc, port


def stop_sim_process(
    proc: subprocess.Popen[str],
    *,
    timeout: float = 5.0,
) -> None:
    """Stop the simulator process gracefully.

    First attempts to terminate the process, then kills it if it does not
    exit within the timeout.

    Parameters
    ----------
    proc
        The subprocess handle for the simulator.
    timeout
        Maximum seconds to wait for graceful termination before killing.

    """
    if proc.poll() is not None:
        return

    try:
        proc.terminate()
    except OSError:
        return

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(OSError):
            proc.kill()
