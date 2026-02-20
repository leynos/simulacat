"""Unit tests for simulator orchestration.

This module verifies the orchestration functionality for starting and stopping
the GitHub API simulator process. Tests cover:

- Entry point discovery (sim_entrypoint)
- Process startup with various configurations (start_sim_process)
- Graceful process termination (stop_sim_process)
- Error handling for invalid executables and configurations

Fixtures
--------
- tmp_path: pytest built-in for temporary directories

Running tests
-------------
Execute these tests with::

    pytest simulacat/unittests/test_orchestration.py -v

Or run via make::

    make test

"""

from __future__ import annotations

import http.client
import os

# S404: tests spawn controlled local helpers only; no shell usage.
import subprocess  # noqa: S404  # simulacat#123: test helpers spawn controlled subprocesses; shell=False
import sys
import typing as typ
import zipfile
from pathlib import Path

import pytest

from simulacat.orchestration import (
    DEFAULT_STOP_TIMEOUT_SECONDS,
    GitHubSimProcessError,
    _empty_initial_state,
    _wait_for_port,
    _write_config,
    sim_entrypoint,
    sim_package_root,
    start_sim_process,
    stop_sim_process,
)
from tests import conftest as test_conftest

bun_required = test_conftest.bun_required


class _PipeProcess:
    """Minimal Popen-like object backed by an OS pipe for testing."""

    def __init__(self, lines: list[str], returncode: int | None = None) -> None:
        read_fd, write_fd = os.pipe()
        with os.fdopen(write_fd, "w", encoding="utf-8") as writer:
            for line in lines:
                writer.write(line)
            writer.flush()
        self.stdout = os.fdopen(read_fd, "r", encoding="utf-8")
        self.returncode = returncode
        self.terminated = False
        self.killed = False
        self.wait_timeout: float | None = None
        self.communicate_timeout: float | None = None

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        if self.returncode is None:
            self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        if self.returncode is None:
            self.returncode = -9

    def wait(self, timeout: float | None = None) -> int | None:
        self.wait_timeout = timeout
        return self.returncode

    def communicate(self, timeout: float | None = None) -> tuple[str, str]:
        self.communicate_timeout = timeout
        if not self.stdout.closed:
            self.stdout.close()
        return "", ""


class TestSimEntrypoint:
    """Tests for the sim_entrypoint function."""

    @staticmethod
    def test_returns_path_to_server_script() -> None:
        """The entrypoint returns a path to github-sim-server.ts."""
        entrypoint = sim_entrypoint()

        assert entrypoint.name == "github-sim-server.ts", (
            f"expected entrypoint.name to be 'github-sim-server.ts', "
            f"got {entrypoint.name}"
        )
        assert entrypoint.parent.name == "src", (
            f"expected entrypoint parent directory to be 'src', "
            f"got {entrypoint.parent.name}"
        )

    @staticmethod
    def test_entrypoint_exists() -> None:
        """The returned entrypoint file exists on disk."""
        entrypoint = sim_entrypoint()

        assert entrypoint.is_file(), (
            f"expected entrypoint to exist as a file: {entrypoint}"
        )

    @staticmethod
    def test_package_root_contains_package_manifest() -> None:
        """The resolved JavaScript package root contains package.json."""
        package_root = sim_package_root()

        assert package_root.is_dir(), (
            f"expected package root to exist as a directory: {package_root}"
        )
        assert (package_root / "package.json").is_file(), (
            f"expected package manifest at {package_root / 'package.json'}"
        )


class TestHelperFunctions:
    """Tests for orchestration helper utilities."""

    @staticmethod
    def test_empty_initial_state_has_required_arrays() -> None:
        """_empty_initial_state returns all required keys with empty lists."""
        state = _empty_initial_state()

        expected = {
            "users": [],
            "organizations": [],
            "repositories": [],
            "branches": [],
            "blobs": [],
        }
        assert state == expected, f"expected initial state {expected}, got {state}"

    @staticmethod
    def test_write_config_wraps_serialization_errors(tmp_path: Path) -> None:
        """Non-serializable config values raise GitHubSimProcessError."""
        config = {"path": tmp_path / "example"}

        with pytest.raises(GitHubSimProcessError):
            _write_config(config, tmp_path)


class TestPackaging:
    """Packaging-time guarantees for the simulator entrypoint."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.packaging
    def test_wheel_includes_simulator_entrypoint(tmp_path: Path) -> None:
        """Built wheels ship the Bun entrypoint required at runtime."""
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)

        # S603: build wheel in test only with explicit args and shell disabled.
        build = subprocess.run(  # noqa: S603  # simulacat#123: wheel build uses explicit args; shell=False
            [
                sys.executable,
                "-m",
                "hatchling",
                "build",
                "--target",
                "wheel",
                "-d",
                str(dist_dir),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[2],
        )

        assert build.returncode == 0, build.stdout + build.stderr

        wheels = list(dist_dir.glob("simulacat-*.whl"))
        assert wheels, (
            f"Wheel not produced; build output: {build.stdout + build.stderr}"
        )

        with zipfile.ZipFile(wheels[0]) as archive:
            contents = set(archive.namelist())
            assert "simulacat/src/github-sim-server.ts" in contents, (
                "Wheel missing simulator entrypoint inside package"
            )
            assert "simulacat/package.json" in contents, (
                "Wheel missing Bun package manifest inside package"
            )
            assert "simulacat/bun.lock" in contents, (
                "Wheel missing Bun lockfile inside package"
            )


class TestStartSimProcess:
    """Tests for starting the simulator process."""

    @staticmethod
    def test_wait_for_port_handles_error_event() -> None:
        """An error event triggers cleanup and raises GitHubSimProcessError."""
        proc = _PipeProcess(['{"event": "error", "message": "boom"}\n'])

        with pytest.raises(GitHubSimProcessError):
            _wait_for_port(typ.cast("subprocess.Popen[str]", proc), startup_timeout=0.2)

        assert proc.terminated or proc.killed, (
            "expected process to be terminated or killed after error event"
        )

    @staticmethod
    def test_wait_for_port_handles_invalid_listening_event() -> None:
        """Malformed listening events raise and stop the process."""
        proc = _PipeProcess(['{"event": "listening", "port": "abc"}\n'])

        with pytest.raises(GitHubSimProcessError):
            _wait_for_port(typ.cast("subprocess.Popen[str]", proc), startup_timeout=0.2)

        assert proc.terminated or proc.killed, (
            "expected process to be terminated or killed after invalid listening event"
        )

    @staticmethod
    def test_wait_for_port_timeout_triggers_cleanup() -> None:
        """Lack of events until deadline results in cleanup and error."""
        proc = _PipeProcess([], returncode=None)

        with pytest.raises(GitHubSimProcessError):
            _wait_for_port(
                typ.cast("subprocess.Popen[str]", proc), startup_timeout=0.05
            )

        assert proc.terminated or proc.killed, (
            "expected process to be terminated or killed after timeout"
        )

    @staticmethod
    @pytest.mark.timeout(2.5)
    def test_times_out_when_simulator_is_silent(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A silent simulator that never writes stdout triggers the timeout."""

        def silent_proc(*_args: object) -> subprocess.Popen[str]:
            return subprocess.Popen(  # noqa: S603  # simulacat#123: test helper spawns controlled Python process; shell=False
                [sys.executable, "-c", "import time; time.sleep(60)"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

        monkeypatch.setattr(
            "simulacat.orchestration._spawn_process",
            silent_proc,
        )

        with pytest.raises(GitHubSimProcessError):
            start_sim_process({}, tmp_path, startup_timeout=0.2)

    @staticmethod
    def test_error_event_from_spawned_process_triggers_cleanup(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An error event from the spawned process raises with cleanup."""
        fake_proc = _PipeProcess(['{"event": "error", "message": "sim failed"}\n'])

        monkeypatch.setattr(
            "simulacat.orchestration._spawn_process",
            lambda *_, **__: typ.cast("subprocess.Popen[str]", fake_proc),
        )

        with pytest.raises(GitHubSimProcessError, match="sim failed"):
            start_sim_process({}, tmp_path, bun_executable="bun")

        assert fake_proc.terminated or fake_proc.killed, (
            "expected fake process to be terminated or killed after error event"
        )

    @staticmethod
    def test_malformed_listening_event_triggers_cleanup(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A malformed listening event raises and stops the fake process."""
        fake_proc = _PipeProcess(['{"event": "listening", "port": "abc"}\n'])

        monkeypatch.setattr(
            "simulacat.orchestration._spawn_process",
            lambda *_, **__: typ.cast("subprocess.Popen[str]", fake_proc),
        )

        with pytest.raises(GitHubSimProcessError):
            start_sim_process({}, tmp_path, bun_executable="bun")

        assert fake_proc.terminated or fake_proc.killed, (
            "expected fake process to be terminated or killed after malformed event"
        )

    @staticmethod
    @pytest.mark.timeout(15)
    @bun_required
    def test_start_process_serves_http(tmp_path: Path) -> None:
        """Start the real simulator and perform an HTTP request."""
        proc, port = start_sim_process({}, tmp_path)
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            try:
                conn.request("GET", "/")
                response = conn.getresponse()
                # Any HTTP status demonstrates the server accepted the request.
                assert response.status >= 100, (
                    f"expected HTTP status >= 100, got {response.status}"
                )
            finally:
                conn.close()
        finally:
            stop_sim_process(proc, timeout=1.0)

    @staticmethod
    @bun_required
    def test_starts_with_empty_config(tmp_path: Path) -> None:
        """An empty config successfully starts the simulator."""
        proc, port = start_sim_process({}, tmp_path)
        try:
            assert port > 0, f"expected port > 0, got {port}"
            assert proc.poll() is None, "expected process to still be running"
        finally:
            stop_sim_process(proc, timeout=1.0)

    @staticmethod
    @bun_required
    def test_starts_with_minimal_explicit_config(tmp_path: Path) -> None:
        """A minimal explicit config starts the simulator."""
        config = {
            "users": [],
            "organizations": [],
            "repositories": [],
            "branches": [],
            "blobs": [],
        }
        proc, port = start_sim_process(config, tmp_path)
        try:
            assert port > 0, f"expected port > 0, got {port}"
        finally:
            stop_sim_process(proc, timeout=1.0)

    @staticmethod
    def test_raises_for_invalid_bun_executable(tmp_path: Path) -> None:
        """An invalid bun executable raises GitHubSimProcessError."""
        with pytest.raises(GitHubSimProcessError):
            start_sim_process({}, tmp_path, bun_executable="/nonexistent/bun")


class TestStopSimProcess:
    """Tests for stopping the simulator process."""

    class _SlowToExitProcess:
        """Popen-like stub that only exits if given enough wait timeout."""

        def __init__(self, *, exit_after_seconds: float) -> None:
            self._exit_after_seconds = exit_after_seconds
            self._returncode: int | None = None
            self._terminated = False
            self._killed = False
            self.wait_timeouts: list[float | None] = []

            # subprocess.TimeoutExpired expects a "cmd" for the args parameter.
            self.args = ["fake-process"]

        def poll(self) -> int | None:
            return self._returncode

        def terminate(self) -> None:
            self._terminated = True

        def kill(self) -> None:
            self._killed = True
            self._returncode = -9

        def wait(self, timeout: float | None = None) -> int | None:
            self.wait_timeouts.append(timeout)
            if self._returncode is not None:
                return self._returncode

            if timeout is None or timeout >= self._exit_after_seconds:
                self._returncode = 0
                return self._returncode

            raise subprocess.TimeoutExpired(self.args, timeout)

    @staticmethod
    @bun_required
    def test_terminates_running_process(tmp_path: Path) -> None:
        """A running process is terminated cleanly."""
        proc, _port = start_sim_process({}, tmp_path)

        stop_sim_process(proc, timeout=1.0)

        assert proc.poll() is not None, "expected process to have exited after stop"

    @staticmethod
    @bun_required
    def test_handles_already_exited_process(tmp_path: Path) -> None:
        """Stopping an already-exited process does not raise."""
        proc, _port = start_sim_process({}, tmp_path)
        proc.terminate()
        proc.wait(timeout=5)

        stop_sim_process(proc, timeout=1.0)

    @staticmethod
    def test_default_timeout_is_five_seconds() -> None:
        """The public default timeout remains conservative to avoid flakiness."""
        assert pytest.approx(5.0) == DEFAULT_STOP_TIMEOUT_SECONDS

    @staticmethod
    def test_default_timeout_allows_slow_exit() -> None:
        """The public default should allow reasonably slow exits without kill."""
        proc = TestStopSimProcess._SlowToExitProcess(exit_after_seconds=2.0)

        stop_sim_process(typ.cast("subprocess.Popen[str]", proc))

        assert proc._terminated, "expected stop_sim_process to terminate the process"
        assert not proc._killed, "did not expect stop_sim_process to kill the process"
        assert proc.wait_timeouts == [DEFAULT_STOP_TIMEOUT_SECONDS], (
            "expected stop_sim_process to wait using the public default timeout"
        )

    @staticmethod
    def test_default_timeout_kills_very_slow_process() -> None:
        """If the process does not exit within the default timeout, it is killed."""
        proc = TestStopSimProcess._SlowToExitProcess(exit_after_seconds=6.0)

        stop_sim_process(typ.cast("subprocess.Popen[str]", proc))

        assert proc._terminated, "expected stop_sim_process to terminate the process"
        assert proc._killed, "expected stop_sim_process to kill after timeout"
        assert proc.wait_timeouts[0] == DEFAULT_STOP_TIMEOUT_SECONDS, (
            "expected first wait to use the public default timeout"
        )
        kill_wait_timeout = proc.wait_timeouts[1]
        assert kill_wait_timeout is not None, "expected a bounded wait after kill"
        assert kill_wait_timeout <= 1.0, (
            "expected kill wait to be bounded to keep teardown responsive"
        )

    @staticmethod
    def test_custom_timeout_kills_slow_exit() -> None:
        """A smaller custom timeout can force kill for faster teardowns."""
        proc = TestStopSimProcess._SlowToExitProcess(exit_after_seconds=2.0)

        stop_sim_process(typ.cast("subprocess.Popen[str]", proc), timeout=1.0)

        assert proc._terminated, "expected stop_sim_process to terminate the process"
        assert proc._killed, "expected stop_sim_process to kill after custom timeout"
        assert pytest.approx(1.0) == proc.wait_timeouts[0], (
            "expected stop_sim_process to use the provided timeout"
        )
        kill_wait_timeout = proc.wait_timeouts[1]
        assert kill_wait_timeout is not None, "expected a bounded wait after kill"
        assert kill_wait_timeout <= 1.0, (
            "expected kill wait to be bounded to keep teardown responsive"
        )


class TestGitHubSimProcessError:
    """Tests for the exception class."""

    @staticmethod
    def test_is_runtime_error() -> None:
        """GitHubSimProcessError is a RuntimeError subclass."""
        error = GitHubSimProcessError("test message")

        assert isinstance(error, RuntimeError), (
            f"expected GitHubSimProcessError to be a RuntimeError, got {type(error)}"
        )
        assert str(error) == "test message", (
            f"expected error message 'test message', got '{error}'"
        )
