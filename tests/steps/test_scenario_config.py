"""BDD step definitions for scenario configuration helpers.

These steps build ScenarioConfig instances, serialize them for the simulator,
and assert that repositories, branches, issues, and pull requests are emitted
as expected. The definitions back the scenarios in
``tests/features/scenario_config.feature``.
"""

from __future__ import annotations

import typing as typ

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from simulacat.scenario import (
    Branch,
    DefaultBranch,
    Issue,
    PullRequest,
    Repository,
    ScenarioConfig,
    User,
)

if typ.TYPE_CHECKING:
    from simulacat.types import (
        GitHubBranchConfig,
        GitHubRepositoryConfig,
        GitHubSimConfig,
    )

scenarios("../features/scenario_config.feature")


class ScenarioContext(typ.TypedDict):
    """Shared context for scenario configuration tests."""

    config: GitHubSimConfig | None


@pytest.fixture
def scenario_context() -> ScenarioContext:
    """Provide shared state for scenario configuration steps."""
    return {"config": None}


def _find_repo(config: GitHubSimConfig, full_name: str) -> GitHubRepositoryConfig:
    repos = typ.cast("list[GitHubRepositoryConfig]", config.get("repositories", []))
    for repo in repos:
        owner = repo.get("owner")
        name = repo.get("name")
        if f"{owner}/{name}" == full_name:
            return repo
    msg = f"Repository {full_name!r} not found in config"
    raise AssertionError(msg)


def _find_branch(
    config: GitHubSimConfig, full_name: str, branch: str
) -> GitHubBranchConfig:
    branches = typ.cast("list[GitHubBranchConfig]", config.get("branches", []))
    for entry in branches:
        owner = entry.get("owner")
        name = entry.get("repository")
        if f"{owner}/{name}" == full_name and entry.get("name") == branch:
            return entry
    msg = f"Branch {branch!r} not found for {full_name!r}"
    raise AssertionError(msg)


@given(
    "a scenario with a single repository and default branch",
    target_fixture="scenario_config",
)
def given_single_repo_scenario() -> ScenarioConfig:
    """Create a scenario with a default branch."""
    return ScenarioConfig(
        users=(User(login="alice"),),
        repositories=(
            Repository(
                owner="alice",
                name="rocket",
                default_branch=DefaultBranch(name="main"),
            ),
        ),
    )


@given(
    "a scenario with public and private repositories",
    target_fixture="scenario_config",
)
def given_mixed_visibility_scenario() -> ScenarioConfig:
    """Create a scenario with multiple repositories and visibility settings."""
    return ScenarioConfig(
        users=(User(login="alice"),),
        repositories=(
            Repository(owner="alice", name="public-repo"),
            Repository(owner="alice", name="private-repo", is_private=True),
        ),
    )


@given(
    "a scenario with issues and pull requests",
    target_fixture="scenario_config",
)
def given_issues_and_pulls_scenario() -> ScenarioConfig:
    """Create a scenario with issues and pull requests."""
    return ScenarioConfig(
        users=(User(login="alice"),),
        repositories=(
            Repository(
                owner="alice",
                name="rocket",
                default_branch=DefaultBranch(name="main"),
            ),
        ),
        branches=(Branch(owner="alice", repository="rocket", name="feature"),),
        issues=(Issue(owner="alice", repository="rocket", number=1, title="Bug"),),
        pull_requests=(
            PullRequest(
                owner="alice",
                repository="rocket",
                number=2,
                title="Feature",
                base_branch="main",
                head_branch="feature",
            ),
        ),
    )


@when("the scenario is serialized for the simulator")
def when_scenario_serialized(
    scenario_config: ScenarioConfig,
    scenario_context: ScenarioContext,
) -> None:
    """Serialize the scenario configuration for the simulator."""
    scenario_context["config"] = scenario_config.to_simulator_config()


@when("the scenario is serialized for the simulator with issues and pull requests")
def when_scenario_serialized_with_issues(
    scenario_config: ScenarioConfig,
    scenario_context: ScenarioContext,
) -> None:
    """Serialize the scenario configuration including issues and pull requests."""
    scenario_context["config"] = scenario_config.to_simulator_config(
        include_unsupported=True
    )


@then('the configuration includes repository "alice/rocket" with default branch "main"')
def then_repository_default_branch(scenario_context: ScenarioContext) -> None:
    """Assert that repository metadata contains the default branch."""
    config = scenario_context["config"]
    assert config is not None, "Expected configuration to be set"
    repo = _find_repo(config, "alice/rocket")
    assert repo.get("default_branch") == "main"


@then('the configuration includes branch "main" for "alice/rocket"')
def then_default_branch_present(scenario_context: ScenarioContext) -> None:
    """Assert that the default branch is emitted as a branch entry."""
    config = scenario_context["config"]
    assert config is not None, "Expected configuration to be set"
    _find_branch(config, "alice/rocket", "main")


@then('the configuration marks repository "alice/public-repo" as public')
def then_public_repo_visibility(scenario_context: ScenarioContext) -> None:
    """Assert that public repositories are marked as not private."""
    config = scenario_context["config"]
    assert config is not None, "Expected configuration to be set"
    repo = _find_repo(config, "alice/public-repo")
    assert repo.get("private") is False


@then('the configuration marks repository "alice/private-repo" as private')
def then_private_repo_visibility(scenario_context: ScenarioContext) -> None:
    """Assert that private repositories are marked as private."""
    config = scenario_context["config"]
    assert config is not None, "Expected configuration to be set"
    repo = _find_repo(config, "alice/private-repo")
    assert repo.get("private") is True


@then(parsers.parse("the configuration includes {count:d} issue"))
def then_configuration_includes_issues(
    scenario_context: ScenarioContext,
    count: int,
) -> None:
    """Assert that issues are serialized when requested."""
    config = scenario_context["config"]
    assert config is not None, "Expected configuration to be set"
    issues = typ.cast("list[dict[str, typ.Any]]", config.get("issues", []))
    assert len(issues) == count
    for issue in issues:
        assert isinstance(issue.get("number"), int)
        assert isinstance(issue.get("title"), str)
        assert isinstance(issue.get("state"), str)


@then(parsers.parse("the configuration includes {count:d} pull request"))
def then_configuration_includes_pull_requests(
    scenario_context: ScenarioContext,
    count: int,
) -> None:
    """Assert that pull requests are serialized when requested."""
    config = scenario_context["config"]
    assert config is not None, "Expected configuration to be set"
    pull_requests = typ.cast(
        "list[dict[str, typ.Any]]", config.get("pull_requests", [])
    )
    assert len(pull_requests) == count
    for pull_request in pull_requests:
        assert isinstance(pull_request.get("number"), int)
        assert isinstance(pull_request.get("title"), str)
        assert isinstance(pull_request.get("state"), str)
