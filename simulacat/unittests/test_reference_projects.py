"""Unit tests for Step 3.2 reference project artifacts.

These tests verify static contracts for the reference projects used to
demonstrate CI integration:

- expected directory layout exists,
- each project defines a pytest suite that uses simulacat fixtures,
- each project ships a GitHub Actions workflow with Python + Node.js setup.
"""

from __future__ import annotations

from tests.reference_project_paths import reference_project_path

REFERENCE_PROJECT_TEST_FILES = {
    "basic-pytest": "test_basic_simulator_smoke.py",
    "authenticated-pytest": "test_authenticated_simulator_smoke.py",
}


def test_reference_project_directories_exist() -> None:
    """Both Step 3.2 reference project directories exist."""
    basic = reference_project_path("basic-pytest")
    authenticated = reference_project_path("authenticated-pytest")

    assert basic.is_dir(), f"Missing reference project directory: {basic}"
    assert authenticated.is_dir(), (
        f"Missing reference project directory: {authenticated}"
    )


def test_reference_projects_include_expected_files() -> None:
    """Each reference project includes the minimum expected files."""
    for project_name, test_file in REFERENCE_PROJECT_TEST_FILES.items():
        project_dir = reference_project_path(project_name)
        expected_paths = (
            project_dir / "README.md",
            project_dir / "pyproject.toml",
            project_dir / "tests" / test_file,
            project_dir / ".github" / "workflows" / "ci.yml",
        )
        for path in expected_paths:
            assert path.is_file(), f"Missing expected file: {path}"


def test_reference_project_tests_use_simulacat() -> None:
    """Reference pytest suites use simulacat fixtures or scenario helpers."""
    for project_name, test_file in REFERENCE_PROJECT_TEST_FILES.items():
        test_path = reference_project_path(project_name) / "tests" / test_file
        content = test_path.read_text(encoding="utf-8")
        assert "github_simulator" in content, (
            f"Expected github_simulator usage in {test_path}"
        )
        assert "simulacat" in content, f"Expected simulacat usage in {test_path}"


def test_reference_ci_workflows_use_python_and_node_tooling() -> None:
    """Reference CI workflows include setup for Python and Node.js."""
    for project_name in ("basic-pytest", "authenticated-pytest"):
        workflow_path = (
            reference_project_path(project_name) / ".github" / "workflows" / "ci.yml"
        )
        content = workflow_path.read_text(encoding="utf-8")
        assert "actions/setup-python" in content, (
            f"Missing actions/setup-python in {workflow_path}"
        )
        assert "actions/setup-node" in content, (
            f"Missing actions/setup-node in {workflow_path}"
        )
        assert "bun-version" in content, (
            f"Missing pinned bun-version in {workflow_path}"
        )
        assert "python -m simulacat.install_simulator_deps" in content, (
            f"Expected central install command usage in {workflow_path}"
        )
        assert "pytest" in content, f"Missing pytest run command in {workflow_path}"
