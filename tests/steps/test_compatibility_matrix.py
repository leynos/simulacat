"""Behaviour tests for Step 4.1 compatibility matrix documentation and CI."""

from __future__ import annotations

import typing as typ
from pathlib import Path

import yaml
from pytest_bdd import given, scenarios, then

from simulacat.compatibility_policy import COMPATIBILITY_POLICY

scenarios("../features/compatibility_matrix.feature")


def repo_root() -> Path:
    """Return the repository root path."""
    return Path(__file__).resolve().parents[2]


def as_object_dict(value: object, *, expectation: str) -> dict[object, object]:
    """Assert an object is a dict and return it as an object-keyed mapping."""
    assert isinstance(value, dict), expectation
    return typ.cast("dict[object, object]", value)


def extract_run_block(step: object) -> str | None:
    """Return a workflow step run block when present."""
    if not isinstance(step, dict):
        return None
    step_dict = typ.cast("dict[object, object]", step)
    run_value = step_dict.get("run")
    if isinstance(run_value, str):
        return run_value
    return None


def get_reference_suites_matrix(workflow: dict[object, object]) -> dict[object, object]:
    """Return the strategy matrix for the reference-suites workflow job."""
    jobs = as_object_dict(
        workflow.get("jobs"), expectation="Expected workflow to define jobs"
    )
    reference_suites_job = as_object_dict(
        jobs.get("reference-suites"),
        expectation="Expected compatibility workflow to define reference-suites job",
    )
    strategy = as_object_dict(
        reference_suites_job.get("strategy"),
        expectation="Expected strategy mapping on reference-suites",
    )
    return as_object_dict(
        strategy.get("matrix"),
        expectation="Expected matrix mapping on reference-suites",
    )


def extract_job_steps(workflow: dict[object, object], *, job_name: str) -> list[object]:
    """Return validated workflow steps for the named job."""
    jobs = as_object_dict(
        workflow.get("jobs"), expectation="Expected workflow to define jobs"
    )
    job = as_object_dict(
        jobs.get(job_name),
        expectation=f"Expected compatibility workflow to define {job_name} job",
    )
    steps = job.get("steps")
    assert isinstance(steps, list), (
        f"Expected workflow job '{job_name}' steps to be a list"
    )
    return typ.cast("list[object]", steps)


def collect_run_blocks(workflow: dict[object, object], *, job_name: str) -> str:
    """Return a newline-joined run script text for the named workflow job."""
    steps = extract_job_steps(workflow, job_name=job_name)
    run_blocks = [run_block for step in steps if (run_block := extract_run_block(step))]
    return "\n".join(run_blocks)


def get_validated_github3_specs(workflow: dict[object, object]) -> list[str]:
    """Return github3-spec matrix entries after validating list shape."""
    github3_specs = get_reference_suites_matrix(workflow).get("github3-spec")
    assert isinstance(github3_specs, list), (
        "Expected github3-spec to be defined as a matrix list"
    )
    return typ.cast("list[str]", github3_specs)


@given("the compatibility matrix workflow file", target_fixture="workflow")
def given_compatibility_workflow_file() -> dict[object, object]:
    """Load and parse the compatibility matrix workflow."""
    workflow_path = repo_root() / ".github" / "workflows" / "compatibility-matrix.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    loaded_workflow = yaml.safe_load(workflow_text)
    return as_object_dict(
        loaded_workflow,
        expectation="Expected compatibility workflow to parse as a mapping",
    )


@given("the users guide document", target_fixture="users_guide_text")
def given_users_guide_document() -> str:
    """Load the users guide markdown text."""
    users_guide_path = repo_root() / "docs" / "users-guide.md"
    return users_guide_path.read_text(encoding="utf-8")


@then('the workflow includes Python versions "3.12" and "3.13"')
def then_workflow_includes_python_versions(workflow: dict[object, object]) -> None:
    """Workflow matrix includes both supported Python versions."""
    matrix = get_reference_suites_matrix(workflow)
    python_versions = matrix.get("python-version")
    assert python_versions == ["3.12", "3.13"], (
        "Expected Python matrix versions ['3.12', '3.13']"
    )


@then('the workflow includes Node.js versions "20.x" and "22.x"')
def then_workflow_includes_node_versions(workflow: dict[object, object]) -> None:
    """Workflow matrix includes both supported Node.js major tracks."""
    matrix = get_reference_suites_matrix(workflow)
    node_versions = matrix.get("node-version")
    assert node_versions == ["20.x", "22.x"], (
        "Expected Node.js matrix versions ['20.x', '22.x']"
    )


@then("the workflow executes both reference project suites")
def then_workflow_executes_reference_suites(workflow: dict[object, object]) -> None:
    """Workflow runs both Step 3.2 reference project suites."""
    combined_run_text = collect_run_blocks(workflow, job_name="reference-suites")
    assert "examples/reference-projects/basic-pytest/tests" in combined_run_text, (
        "Expected workflow run steps to execute basic reference project tests"
    )
    assert (
        "examples/reference-projects/authenticated-pytest/tests" in combined_run_text
    ), "Expected workflow run steps to execute authenticated reference project tests"


@then('the workflow includes github3.py constraint ">=3.2.0,<4.0.0"')
def then_workflow_includes_github3_v3(workflow: dict[object, object]) -> None:
    """Workflow matrix includes the github3.py v3 major track."""
    github3_specs = get_validated_github3_specs(workflow)
    assert ">=3.2.0,<4.0.0" in github3_specs, (
        "Expected reference-suites matrix github3-spec to include >=3.2.0,<4.0.0"
    )


@then('the workflow includes github3.py constraint ">=4.0.0,<5.0.0"')
def then_workflow_includes_github3_v4(workflow: dict[object, object]) -> None:
    """Workflow matrix includes the github3.py v4 major track."""
    github3_specs = get_validated_github3_specs(workflow)
    assert ">=4.0.0,<5.0.0" in github3_specs, (
        "Expected reference-suites matrix github3-spec to include >=4.0.0,<5.0.0"
    )


@then("the workflow installs pytest-bdd")
def then_workflow_installs_pytest_bdd(workflow: dict[object, object]) -> None:
    """Workflow installs pytest-bdd required by repository-level conftest."""
    combined_run_text = collect_run_blocks(workflow, job_name="reference-suites")
    assert "pytest-bdd" in combined_run_text, (
        "Expected workflow Python dependency installation to include pytest-bdd"
    )


@then('the users guide includes a "Compatibility matrix" section')
def then_users_guide_has_compatibility_section(users_guide_text: str) -> None:
    """Users guide contains compatibility policy section."""
    assert "## Compatibility matrix" in users_guide_text, (
        "Expected users guide to contain a 'Compatibility matrix' section heading"
    )


@then('the users guide includes a "Known incompatibilities and workarounds" section')
def then_users_guide_has_incompatibility_section(users_guide_text: str) -> None:
    """Users guide contains known incompatibility section."""
    assert "### Known incompatibilities and workarounds" in users_guide_text, (
        "Expected users guide to contain known incompatibilities and "
        "workarounds heading"
    )


def _normalize_table_rows(text: str) -> list[tuple[str, ...]]:
    """Extract table rows from markdown and normalise cell whitespace."""
    rows: list[tuple[str, ...]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = tuple(cell.strip() for cell in stripped.split("|")[1:-1])
            rows.append(cells)
    return rows


@then("the users guide documents Python, github3.py, Node.js, and simulator ranges")
def then_users_guide_documents_ranges(users_guide_text: str) -> None:
    """Users guide lists all Step 4.1 dependency ranges from policy constants."""
    dependency_heading_map = {
        "python": "Python",
        "github3.py": "github3.py",
        "node.js": "Node.js",
        "@simulacrum/github-api-simulator": "@simulacrum/github-api-simulator",
    }
    normalised_rows = _normalize_table_rows(users_guide_text)
    for policy_key, heading in dependency_heading_map.items():
        policy = COMPATIBILITY_POLICY[policy_key]
        expected_cells = (
            heading,
            policy.minimum_version,
            policy.recommended_version,
            policy.supported_range,
        )
        assert expected_cells in normalised_rows, (
            f"Expected users guide compatibility row with cells: {expected_cells}"
        )
