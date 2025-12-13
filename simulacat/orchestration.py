"""Simulator process orchestration for simulacat.

This module manages the lifecycle of the Bun-based GitHub API simulator,
handling process startup, port discovery, and cleanup.

Example:
-------
Start and stop a simulator::

    from pathlib import Path
    from simulacat.orchestration import start_sim_process, stop_sim_process

    proc, port = start_sim_process({}, Path("/tmp"))
    # Use the simulator at http://127.0.0.1:{port}
    stop_sim_process(proc)

"""

from __future__ import annotations

import contextlib
import json
import os
import queue

# S404: subprocess is required for spawning the Bun simulator process with
# validated arguments and without a shell.
import subprocess  # noqa: S404  # simulacat#123: spawn Bun simulator with validated args; shell=False
import threading
import time
import typing as typ
from importlib import resources
from pathlib import Path

if typ.TYPE_CHECKING:
    import collections.abc as cabc


class GitHubSimProcessError(RuntimeError):
    """Exception raised when the simulator process fails to start or run."""


DEFAULT_STOP_TIMEOUT_SECONDS = 5.0
_KILL_WAIT_TIMEOUT_SECONDS = 1.0


def sim_entrypoint() -> Path:
    """Return the path to the simulator entry point script.

    Returns
    -------
    Path
        Absolute path to the github-sim-server.ts file.

    """
    package_root = resources.files("simulacat")
    packaged_entrypoint = Path(
        str(package_root.joinpath("src").joinpath("github-sim-server.ts"))
    )
    repo_entrypoint = (
        Path(__file__).resolve().parent.parent / "src" / "github-sim-server.ts"
    )
    candidates = [packaged_entrypoint, repo_entrypoint]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    return candidates[0]


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
    effective_config: dict[str, typ.Any] = _empty_initial_state()
    effective_config.update(dict(config))

    config_path = tmpdir / "github-sim-config.json"
    try:
        serialized_config = json.dumps(effective_config)
    except (TypeError, ValueError) as exc:
        msg = "Failed to serialize simulator configuration to JSON"
        raise GitHubSimProcessError(msg) from exc

    config_path.write_text(serialized_config, encoding="utf-8")
    return config_path


def _spawn_process(
    bun_executable: str,
    entrypoint: Path,
    config_path: Path,
) -> subprocess.Popen[str]:
    """Spawn the simulator process."""
    try:
        # S603: Arguments are validated paths and executable name, no shell used.
        return subprocess.Popen(  # noqa: S603  # simulacat#123: validated executable + paths; shell=False
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
    with contextlib.suppress(json.JSONDecodeError):
        evt = json.loads(line)
        if isinstance(evt, dict):
            return evt
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
    line_queue, reader = _start_stdout_reader(proc)

    try:
        while time.time() < deadline:
            line = _read_stdout_line(deadline, line_queue)
            status = _line_status(proc, line)

            if status == "continue":
                continue
            if status == "break":
                break

            if line is None:
                continue

            port = _process_stdout_line(proc, line, output_lines)
            if port is not None:
                return port
    finally:
        reader.join(timeout=0.1)

    return _cleanup_failed_process(proc, output_lines)


def _start_stdout_reader(
    proc: subprocess.Popen[str],
) -> tuple[queue.Queue[str | None], threading.Thread]:
    """Start a background reader thread that feeds stdout lines into a queue."""
    stdout = proc.stdout
    if stdout is None:
        msg = "Failed to capture simulator stdout"
        raise GitHubSimProcessError(msg)

    line_queue: queue.Queue[str | None] = queue.Queue()

    def _reader() -> None:
        for line in iter(stdout.readline, ""):
            line_queue.put(line)
        line_queue.put(None)

    thread = threading.Thread(
        target=_reader,
        name="simulator-stdout-reader",
        daemon=True,
    )
    thread.start()
    return line_queue, thread


def _read_stdout_line(
    deadline: float,
    line_queue: queue.Queue[str | None],
) -> str | None:
    """Read a line from stdout without blocking past the deadline."""
    remaining = max(0.0, deadline - time.time())
    try:
        return line_queue.get(timeout=remaining)
    except queue.Empty:
        return None


def _line_status(
    proc: subprocess.Popen[str],
    line: str | None,
) -> typ.Literal["break", "continue", "ok"]:
    """Classify stdout read outcomes to simplify control flow."""
    if line is None:
        return "break" if proc.poll() is not None else "continue"

    if line == "":
        if proc.poll() is not None:
            return "break"

        return "continue"

    return "ok"


def _process_stdout_line(
    proc: subprocess.Popen[str],
    line: str,
    output_lines: list[str],
) -> int | None:
    """Handle a line of simulator output, returning port if available."""
    output_lines.append(line)
    evt = _parse_event(line)

    if evt is None:
        return None

    if evt.get("event") == "listening":
        try:
            return int(evt["port"])
        except (KeyError, TypeError, ValueError):
            msg = f"Invalid listening event from simulator: {evt!r}"
            _cleanup_failed_process(proc, output_lines, message=msg)

    if evt.get("event") == "error":
        error_msg = evt.get("message", "Unknown error")
        msg = f"Simulator error: {error_msg}"
        _cleanup_failed_process(proc, output_lines, message=msg)

    return None


def _cleanup_failed_process(
    proc: subprocess.Popen[str],
    output_lines: list[str],
    *,
    message: str | None = None,
) -> typ.NoReturn:
    """Clean up a failed process and raise an error."""
    _drain_process_output(proc, output_lines)
    _stop_process(proc)

    msg = message or (
        "Simulator did not report a listening port.\n"
        f"Exit code: {proc.poll()}\n"
        f"Output:\n{''.join(output_lines)}"
    )
    raise GitHubSimProcessError(msg)


def _drain_process_output(
    proc: subprocess.Popen[str],
    output_lines: list[str],
) -> None:
    """Drain remaining output and wait for the process.

    Parameters
    ----------
    proc
        The subprocess to drain.
    output_lines
        Mutable list already populated by caller; retained for diagnostic context.

    """
    # Do not call communicate() since a reader thread may be active on stdout.
    # Just wait briefly for the process to exit; _stop_process handles cleanup.
    with contextlib.suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=1)


def _stop_process(proc: subprocess.Popen[str], *, timeout: float = 1.0) -> None:
    with contextlib.suppress(OSError):
        proc.terminate()

    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        proc.wait(timeout=timeout)

    if proc.poll() is None:
        with contextlib.suppress(OSError):
            proc.kill()
        with contextlib.suppress(subprocess.TimeoutExpired, OSError):
            proc.wait(timeout=timeout)


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

    try:
        config_path = _write_config(config, tmpdir)
        proc = _spawn_process(bun_executable, entrypoint, config_path)
    except GitHubSimProcessError:
        raise
    except Exception as exc:
        msg = "Failed to start simulator"
        raise GitHubSimProcessError(msg) from exc
    port = _wait_for_port(proc, startup_timeout)

    return proc, port


def stop_sim_process(
    proc: subprocess.Popen[str],
    *,
    timeout: float = DEFAULT_STOP_TIMEOUT_SECONDS,
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
        kill_wait_timeout = min(timeout, _KILL_WAIT_TIMEOUT_SECONDS)
        with contextlib.suppress(subprocess.TimeoutExpired, OSError):
            proc.wait(timeout=kill_wait_timeout)
