"""Behaviour tests for Step 4.1 compatibility matrix documentation and CI."""

from __future__ import annotations

from pathlib import Path

from pytest_bdd import given, scenarios, then

scenarios("../features/compatibility_matrix.feature")


def repo_root() -> Path:
    """Return the repository root path."""
    return Path(__file__).resolve().parents[2]


@given("the compatibility matrix workflow file", target_fixture="workflow_text")
def given_compatibility_workflow_file() -> str:
    """Load the compatibility matrix workflow as text."""
    workflow_path = repo_root() / ".github" / "workflows" / "compatibility-matrix.yml"
    return workflow_path.read_text(encoding="utf-8")


@given("the users guide document", target_fixture="users_guide_text")
def given_users_guide_document() -> str:
    """Load the users guide markdown text."""
    users_guide_path = repo_root() / "docs" / "users-guide.md"
    return users_guide_path.read_text(encoding="utf-8")


@then('the workflow includes Python versions "3.12" and "3.13"')
def then_workflow_includes_python_versions(workflow_text: str) -> None:
    """Workflow matrix includes both supported Python versions."""
    assert 'python-version: ["3.12", "3.13"]' in workflow_text


@then("the workflow executes both reference project suites")
def then_workflow_executes_reference_suites(workflow_text: str) -> None:
    """Workflow runs both Step 3.2 reference project suites."""
    assert "examples/reference-projects/basic-pytest/tests" in workflow_text
    assert "examples/reference-projects/authenticated-pytest/tests" in workflow_text


@then('the workflow includes github3.py constraint ">=3.2.0,<4.0.0"')
def then_workflow_includes_github3_v3(workflow_text: str) -> None:
    """Workflow matrix includes the github3.py v3 major track."""
    assert '">=3.2.0,<4.0.0"' in workflow_text


@then('the workflow includes github3.py constraint ">=4.0.0,<5.0.0"')
def then_workflow_includes_github3_v4(workflow_text: str) -> None:
    """Workflow matrix includes the github3.py v4 major track."""
    assert '">=4.0.0,<5.0.0"' in workflow_text


@then("the workflow installs pytest-bdd")
def then_workflow_installs_pytest_bdd(workflow_text: str) -> None:
    """Workflow installs pytest-bdd required by repository-level conftest."""
    assert "pytest-bdd" in workflow_text


@then('the users guide includes a "Compatibility matrix" section')
def then_users_guide_has_compatibility_section(users_guide_text: str) -> None:
    """Users guide contains compatibility policy section."""
    assert "## Compatibility matrix" in users_guide_text


@then('the users guide includes a "Known incompatibilities and workarounds" section')
def then_users_guide_has_incompatibility_section(users_guide_text: str) -> None:
    """Users guide contains known incompatibility section."""
    assert "### Known incompatibilities and workarounds" in users_guide_text


@then("the users guide documents Python, github3.py, Node.js, and simulator ranges")
def then_users_guide_documents_ranges(users_guide_text: str) -> None:
    """Users guide lists all Step 4.1 version range dimensions."""
    assert "| Python |" in users_guide_text
    assert "| github3.py |" in users_guide_text
    assert "| Node.js |" in users_guide_text
    assert "| @simulacrum/github-api-simulator |" in users_guide_text
