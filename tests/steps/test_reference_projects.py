"""Step definitions for Step 3.2 reference project behavioural tests.

These steps validate the user-observable behaviour of the new reference
projects by:

- executing their pytest suites, and
- checking CI workflow semantics (Python + Node.js setup).
"""

from __future__ import annotations

import subprocess  # noqa: S404  # trusted static commands in repository tests
import sys
import typing as typ
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/reference_projects.feature")


class ReferenceProjectContext(typ.TypedDict):
    """Shared scenario context for reference project steps."""

    project_name: str | None
    project_dir: Path | None
    last_result: subprocess.CompletedProcess[str] | None


def _repo_root() -> Path:
    """Return the repository root path."""
    return Path(__file__).resolve().parents[2]


def _project_path(project_name: str) -> Path:
    """Return the path to a named reference project."""
    return _repo_root() / "examples" / "reference-projects" / project_name


@given(
    parsers.parse('the reference project "{project_name}"'),
    target_fixture="reference_context",
)
def given_reference_project(project_name: str) -> ReferenceProjectContext:
    """Provide context for a named reference project."""
    return {
        "project_name": project_name,
        "project_dir": _project_path(project_name),
        "last_result": None,
    }


@when(parsers.parse('the reference project is switched to "{project_name}"'))
def when_reference_project_switched(
    reference_context: ReferenceProjectContext,
    project_name: str,
) -> None:
    """Switch scenario context to a different named reference project."""
    reference_context["project_name"] = project_name
    reference_context["project_dir"] = _project_path(project_name)
    reference_context["last_result"] = None


@when("the project's pytest suite is executed")
def when_project_pytest_suite_executed(
    reference_context: ReferenceProjectContext,
) -> None:
    """Execute the project's smoke-test suite via the current Python runtime."""
    project_dir = reference_context["project_dir"]
    assert project_dir is not None, "Expected reference project directory in context"

    result = subprocess.run(  # noqa: S603  # static test command
        [sys.executable, "-m", "pytest", "-q", "tests"],
        cwd=project_dir,
        check=False,
        capture_output=True,
        text=True,
    )
    reference_context["last_result"] = result


@then("the suite command succeeds")
def then_suite_command_succeeds(reference_context: ReferenceProjectContext) -> None:
    """Assert that the pytest command exits successfully."""
    result = reference_context["last_result"]
    assert result is not None, "Expected command result in context"
    assert result.returncode == 0, (
        "Expected suite command to succeed.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


@then("the workflow includes setup-python and setup-node actions")
def then_workflow_includes_required_setup_actions(
    reference_context: ReferenceProjectContext,
) -> None:
    """Assert workflow contains standard Python + Node.js setup steps."""
    project_dir = reference_context["project_dir"]
    assert project_dir is not None, "Expected reference project directory in context"

    workflow_path = project_dir / ".github" / "workflows" / "ci.yml"
    content = workflow_path.read_text(encoding="utf-8")

    assert "actions/setup-python" in content, (
        f"Expected actions/setup-python in {workflow_path}"
    )
    assert "actions/setup-node" in content, (
        f"Expected actions/setup-node in {workflow_path}"
    )
