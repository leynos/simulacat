"""Unit tests for simulator dependency installation helper command."""

from __future__ import annotations

import dataclasses as dc

# S404: tests patch subprocess.run and raise TimeoutExpired only.
import subprocess  # noqa: S404  # simulacat#123: test-only subprocess objects
import typing as typ

import pytest

from simulacat import install_simulator_deps
from simulacat.orchestration import GitHubSimProcessError

if typ.TYPE_CHECKING:
    from pathlib import Path


@dc.dataclass(frozen=True)
class _FakeCompletedProcess:
    """Minimal subprocess result object exposing a return code."""

    returncode: int


class TestInstallSimulatorDependencies:
    """Validate Bun install orchestration for simulator dependencies."""

    @staticmethod
    def test_returns_package_root_when_bun_install_succeeds(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Successful Bun execution returns resolved package root."""

        def fake_run(
            command: list[str], *, check: bool, timeout: int
        ) -> _FakeCompletedProcess:
            assert check is False, "Expected subprocess call to disable check mode"
            assert timeout == 300, "Expected subprocess timeout to be 300 seconds"
            assert command == ["bun", "install", "--cwd", str(tmp_path)]
            return _FakeCompletedProcess(returncode=0)

        monkeypatch.setattr(
            install_simulator_deps, "sim_package_root", lambda: tmp_path
        )
        monkeypatch.setattr(install_simulator_deps.subprocess, "run", fake_run)

        package_root = install_simulator_deps.install_simulator_dependencies()
        assert package_root == tmp_path, (
            "Expected successful installation to return the resolved package root"
        )

    @staticmethod
    def test_raises_when_bun_executable_is_missing(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Missing Bun executable is wrapped as GitHubSimProcessError."""

        def fake_run(
            command: list[str],
            *,
            check: bool,
            timeout: int,
        ) -> _FakeCompletedProcess:
            assert check is False, "Expected subprocess call to disable check mode"
            assert timeout == 300, "Expected subprocess timeout to be 300 seconds"
            raise FileNotFoundError(command[0])

        monkeypatch.setattr(
            install_simulator_deps, "sim_package_root", lambda: tmp_path
        )
        monkeypatch.setattr(install_simulator_deps.subprocess, "run", fake_run)

        with pytest.raises(GitHubSimProcessError, match="Bun executable not found"):
            install_simulator_deps.install_simulator_dependencies()

    @staticmethod
    def test_raises_when_bun_install_returns_non_zero(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Non-zero Bun exit status raises GitHubSimProcessError."""

        def fake_run(
            command: list[str], *, check: bool, timeout: int
        ) -> _FakeCompletedProcess:
            assert check is False, "Expected subprocess call to disable check mode"
            assert timeout == 300, "Expected subprocess timeout to be 300 seconds"
            return _FakeCompletedProcess(returncode=2)

        monkeypatch.setattr(
            install_simulator_deps, "sim_package_root", lambda: tmp_path
        )
        monkeypatch.setattr(install_simulator_deps.subprocess, "run", fake_run)

        with pytest.raises(
            GitHubSimProcessError,
            match="Failed to install simulator dependencies",
        ):
            install_simulator_deps.install_simulator_dependencies()

    @staticmethod
    def test_raises_when_bun_install_times_out(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Timeouts from Bun are wrapped as GitHubSimProcessError."""

        def fake_run(
            command: list[str],
            *,
            check: bool,
            timeout: int,
        ) -> _FakeCompletedProcess:
            assert check is False, "Expected subprocess call to disable check mode"
            assert timeout == 300, "Expected subprocess timeout to be 300 seconds"
            raise subprocess.TimeoutExpired(
                cmd="bun install --cwd /tmp/simulacat-package-root",
                timeout=timeout,
            )

        monkeypatch.setattr(
            install_simulator_deps, "sim_package_root", lambda: tmp_path
        )
        monkeypatch.setattr(install_simulator_deps.subprocess, "run", fake_run)

        with pytest.raises(
            GitHubSimProcessError,
            match="Timed out while installing simulator dependencies",
        ):
            install_simulator_deps.install_simulator_dependencies()


class TestInstallSimulatorDepsMain:
    """Validate CLI exit codes and message output."""

    @staticmethod
    def test_main_prints_success_message(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """Successful execution prints install destination to stdout."""
        monkeypatch.setattr(
            install_simulator_deps,
            "install_simulator_dependencies",
            lambda: tmp_path,
        )

        exit_code = install_simulator_deps.main()
        captured = capsys.readouterr()

        assert exit_code == 0, "Expected zero exit code on successful install"
        assert str(tmp_path) in captured.out, (
            "Expected stdout to include installation destination"
        )
        assert captured.err == "", "Expected no stderr output on success"

    @staticmethod
    def test_main_prints_error_and_returns_non_zero(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Failures are reported to stderr with exit code 1."""

        def fail_install() -> typ.NoReturn:
            msg = "dependency install failed"
            raise GitHubSimProcessError(msg)

        monkeypatch.setattr(
            install_simulator_deps,
            "install_simulator_dependencies",
            fail_install,
        )

        exit_code = install_simulator_deps.main()
        captured = capsys.readouterr()

        assert exit_code == 1, "Expected non-zero exit code when installation fails"
        assert "Failed to install simulator dependencies" in captured.err, (
            "Expected prefixed failure message on stderr"
        )
        assert "dependency install failed" in captured.err, (
            "Expected original failure reason on stderr"
        )
        assert captured.out == "", "Expected no stdout output on failure"
