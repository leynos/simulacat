"""Unit tests for the github_simulator pytest fixture.

These tests verify that simulacat exposes a fixture that:

- starts the simulator process via the orchestration layer,
- constructs a github3.py client pointing at the simulator,
- guarantees teardown even when a test fails.

Running tests
-------------
Execute these tests with::

    pytest simulacat/unittests/test_github_simulator.py -v

Or run via make::

    make test

"""

from __future__ import annotations

import re
import sys
import textwrap
import typing as typ

pytest_plugins = ["pytester"]

if typ.TYPE_CHECKING:
    import pytest
    from _pytest.pytester import Pytester


def test_github_simulator_skips_when_bun_is_unavailable(
    pytester: Pytester,
) -> None:
    """The fixture skips with a clear message when Bun cannot be located."""
    pytester.makeconftest(
        textwrap.dedent(
            """\
            from __future__ import annotations

            from simulacat import pytest_plugin

            pytest_plugin.shutil.which = lambda *_: None
            """
        )
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
            def test_skipped(github_simulator):
                assert github_simulator is not None
            """
        )
    )
    result = pytester.runpytest_subprocess("-q", "-rs")
    result.assert_outcomes(skipped=1)
    output = result.stdout.str() + result.stderr.str()
    assert re.search(r"SKIPPED.*Bun", output, re.IGNORECASE), output


def test_github_simulator_constructs_client_and_passes_config(
    pytester: Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fixture binds github3 to the simulator URL and tears down."""
    monkeypatch.setenv("BUN", sys.executable)

    pytester.makeconftest(
        textwrap.dedent(
            """\
            from __future__ import annotations

            import json
            import sys
            from pathlib import Path

            import github3
            import github3.session as github3_session

            from simulacat import orchestration, pytest_plugin

            pytest_plugin.shutil.which = lambda *_: sys.executable


            def start_sim_process(config, tmpdir, **_):
                Path(tmpdir, "seen-config.json").write_text(
                    json.dumps(config),
                    encoding="utf-8",
                )
                return object(), 4242


            def stop_sim_process(proc, **_):
                Path(__file__).with_name("stopped.txt").write_text(
                    "stopped",
                    encoding="utf-8",
                )


            orchestration.start_sim_process = start_sim_process
            orchestration.stop_sim_process = stop_sim_process


            class FakeSession:
                base_url = ""


            def GitHubSession():
                return FakeSession()


            def GitHub(*, session=None, **_):
                Path(__file__).with_name("session-base-url.txt").write_text(
                    session.base_url,
                    encoding="utf-8",
                )
                return object()


            github3_session.GitHubSession = GitHubSession
            github3.GitHub = GitHub
            """
        )
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
            import json

            import pytest


            @pytest.mark.parametrize(
                "github_sim_config",
                [{"users": [{"login": "alice", "organizations": []}]}],
                indirect=True,
            )
            def test_binds_client_and_calls_start(github_simulator, tmp_path):
                assert github_simulator is not None

                cfg = json.loads(
                    (tmp_path / "seen-config.json").read_text(encoding="utf-8")
                )
                assert cfg["users"][0]["login"] == "alice"
                assert cfg["organizations"] == []
                assert cfg["repositories"] == []
                assert cfg["branches"] == []
                assert cfg["blobs"] == []
            """
        )
    )
    result = pytester.runpytest_subprocess("-q")
    result.assert_outcomes(passed=1)
    assert (pytester.path / "stopped.txt").is_file()
    assert (pytester.path / "session-base-url.txt").read_text(
        encoding="utf-8"
    ) == "http://127.0.0.1:4242"


def test_teardown_runs_even_when_fixture_setup_fails(
    pytester: Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fixture still triggers stop_sim_process when setup fails after start."""
    monkeypatch.setenv("BUN", sys.executable)

    pytester.makeconftest(
        textwrap.dedent(
            """\
            from __future__ import annotations

            import sys
            from pathlib import Path

            import github3
            import github3.session as github3_session

            from simulacat import orchestration, pytest_plugin

            pytest_plugin.shutil.which = lambda *_: sys.executable


            def start_sim_process(config, tmpdir, **_):
                return object(), 4242


            def stop_sim_process(proc, **_):
                Path(__file__).with_name("stopped.txt").write_text(
                    "stopped",
                    encoding="utf-8",
                )


            orchestration.start_sim_process = start_sim_process
            orchestration.stop_sim_process = stop_sim_process


            def GitHubSession():
                raise RuntimeError("boom during fixture setup")


            github3_session.GitHubSession = GitHubSession
            github3.GitHub = lambda **_: object()
            """
        )
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
            def test_setup_failure_still_tears_down(github_simulator):
                # The test body is not reached because fixture setup fails.
                assert github_simulator is not None
            """
        )
    )

    result = pytester.runpytest_subprocess("-q")
    result.assert_outcomes(errors=1)
    assert (pytester.path / "stopped.txt").is_file()


def test_teardown_runs_even_when_test_fails(
    pytester: Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fixture still triggers stop_sim_process when a test fails."""
    monkeypatch.setenv("BUN", sys.executable)

    pytester.makeconftest(
        textwrap.dedent(
            """\
            from __future__ import annotations

            from pathlib import Path

            from simulacat import orchestration


            def start_sim_process(config, tmpdir, **_):
                # Record that the fixture attempted startup with the provided tmpdir.
                Path(tmpdir, "start-called.txt").write_text(
                    "started",
                    encoding="utf-8",
                )
                return object(), 12345


            def stop_sim_process(proc, **_):
                Path(__file__).with_name("stopped.txt").write_text(
                    "stopped",
                    encoding="utf-8",
                )


            orchestration.start_sim_process = start_sim_process
            orchestration.stop_sim_process = stop_sim_process
            """
        )
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
            def test_failure_still_tears_down(github_simulator):
                assert github_simulator is not None
                assert False, "force failure to ensure teardown still runs"
            """
        )
    )
    result = pytester.runpytest_subprocess("-q")
    result.assert_outcomes(failed=1)
    assert (pytester.path / "stopped.txt").is_file(), (
        "expected github_simulator teardown to write stopped.txt"
    )
