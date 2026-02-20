"""Unit tests for the `python -m simulacat.js_root` helper command."""

from __future__ import annotations

import typing as typ

from simulacat import js_root
from simulacat.orchestration import GitHubSimProcessError, sim_package_root

if typ.TYPE_CHECKING:
    import pytest


class TestJsRootCommand:
    """Validate command behaviour for JS package-root discovery."""

    @staticmethod
    def test_main_prints_resolved_package_root(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The command prints the same path as `sim_package_root()`."""
        exit_code = js_root.main()
        captured = capsys.readouterr()

        assert exit_code == 0, "Expected successful exit code"
        assert captured.out.strip() == str(sim_package_root()), (
            "Expected stdout to contain the resolved package root path"
        )
        assert captured.err == "", "Expected no stderr output on success"

    @staticmethod
    def test_main_reports_resolution_failures(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Resolution failures are reported to stderr with non-zero exit code."""

        def raise_failure() -> typ.NoReturn:
            msg = "missing package manifest"
            raise GitHubSimProcessError(msg)

        monkeypatch.setattr(js_root, "sim_package_root", raise_failure)

        exit_code = js_root.main()
        captured = capsys.readouterr()

        assert exit_code == 1, "Expected non-zero exit code on resolution failure"
        assert "Failed to resolve SIMULACAT_JS_ROOT" in captured.err, (
            "Expected command failure prefix in stderr"
        )
        assert "missing package manifest" in captured.err, (
            "Expected original failure details in stderr"
        )
        assert captured.out == "", "Expected no stdout output when resolution fails"
