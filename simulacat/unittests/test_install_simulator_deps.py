"""Unit tests for simulator dependency installation helper command."""

from __future__ import annotations

# S404: tests patch subprocess.run and instantiate CompletedProcess only.
import subprocess  # noqa: S404  # simulacat#123: test-only subprocess objects
import typing as typ

import pytest

from simulacat import install_simulator_deps
from simulacat.orchestration import GitHubSimProcessError

if typ.TYPE_CHECKING:
    from pathlib import Path


class TestInstallSimulatorDependencies:
    """Validate Bun install orchestration for simulator dependencies."""

    @staticmethod
    def test_returns_package_root_when_bun_install_succeeds(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Successful Bun execution returns resolved package root."""

        def fake_run(
            command: list[str], *, check: bool
        ) -> subprocess.CompletedProcess[str]:
            assert check is False, "Expected subprocess call to disable check mode"
            assert command == ["bun", "install", "--cwd", str(tmp_path)]
            return subprocess.CompletedProcess(args=command, returncode=0)

        monkeypatch.setattr(
            install_simulator_deps, "sim_package_root", lambda: tmp_path
        )
        monkeypatch.setattr(install_simulator_deps.subprocess, "run", fake_run)

        package_root = install_simulator_deps.install_simulator_dependencies()
        assert package_root == tmp_path

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
        ) -> subprocess.CompletedProcess[str]:
            assert check is False, "Expected subprocess call to disable check mode"
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
            command: list[str], *, check: bool
        ) -> subprocess.CompletedProcess[str]:
            assert check is False, "Expected subprocess call to disable check mode"
            return subprocess.CompletedProcess(args=command, returncode=2)

        monkeypatch.setattr(
            install_simulator_deps, "sim_package_root", lambda: tmp_path
        )
        monkeypatch.setattr(install_simulator_deps.subprocess, "run", fake_run)

        with pytest.raises(
            GitHubSimProcessError,
            match="Failed to install simulator dependencies",
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

        assert exit_code == 0
        assert str(tmp_path) in captured.out
        assert captured.err == ""

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

        assert exit_code == 1
        assert "Failed to install simulator dependencies" in captured.err
        assert "dependency install failed" in captured.err
        assert captured.out == ""
