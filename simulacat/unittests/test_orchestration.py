"""Unit tests for simulator orchestration."""

from __future__ import annotations

import typing as typ

import pytest

from simulacat.orchestration import (
    GitHubSimProcessError,
    sim_entrypoint,
    start_sim_process,
    stop_sim_process,
)

if typ.TYPE_CHECKING:
    from pathlib import Path


class TestSimEntrypoint:
    """Tests for the sim_entrypoint function."""

    @staticmethod
    def test_returns_path_to_server_script() -> None:
        """The entrypoint returns a path to github-sim-server.ts."""
        entrypoint = sim_entrypoint()

        assert entrypoint.name == "github-sim-server.ts"
        assert entrypoint.parent.name == "src"

    @staticmethod
    def test_entrypoint_exists() -> None:
        """The returned entrypoint file exists on disk."""
        entrypoint = sim_entrypoint()

        assert entrypoint.is_file()


class TestStartSimProcess:
    """Tests for starting the simulator process."""

    @staticmethod
    def test_starts_with_empty_config(tmp_path: Path) -> None:
        """An empty config successfully starts the simulator."""
        proc, port = start_sim_process({}, tmp_path)
        try:
            assert port > 0
            assert proc.poll() is None
        finally:
            stop_sim_process(proc)

    @staticmethod
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
            assert port > 0
        finally:
            stop_sim_process(proc)

    @staticmethod
    def test_raises_for_invalid_bun_executable(tmp_path: Path) -> None:
        """An invalid bun executable raises GitHubSimProcessError."""
        with pytest.raises(GitHubSimProcessError):
            start_sim_process({}, tmp_path, bun_executable="/nonexistent/bun")


class TestStopSimProcess:
    """Tests for stopping the simulator process."""

    @staticmethod
    def test_terminates_running_process(tmp_path: Path) -> None:
        """A running process is terminated cleanly."""
        proc, _port = start_sim_process({}, tmp_path)

        stop_sim_process(proc)

        assert proc.poll() is not None

    @staticmethod
    def test_handles_already_exited_process(tmp_path: Path) -> None:
        """Stopping an already-exited process does not raise."""
        proc, _port = start_sim_process({}, tmp_path)
        proc.terminate()
        proc.wait(timeout=5)

        stop_sim_process(proc)


class TestGitHubSimProcessError:
    """Tests for the exception class."""

    @staticmethod
    def test_is_runtime_error() -> None:
        """GitHubSimProcessError is a RuntimeError subclass."""
        error = GitHubSimProcessError("test message")

        assert isinstance(error, RuntimeError)
        assert str(error) == "test message"
