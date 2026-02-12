"""BDD step definitions for GitHub App installation metadata behaviour.

These steps validate the GitHub App and installation configuration helpers
defined in ``simulacat.scenario_models`` and ``simulacat.scenario_config``.

Feature files
-------------
The step definitions bind to scenarios in:
- tests/features/github_app.feature

Running tests
-------------
Execute behavioural tests with::

    pytest tests/steps/test_github_app.py -v

Or run all tests via make::

    make test

"""

from __future__ import annotations

import typing as typ

import pytest
from pytest_bdd import given, scenarios, then, when

from simulacat import (
    AppInstallation,
    ConfigValidationError,
    GitHubApp,
    Repository,
    ScenarioConfig,
    User,
    github_app_scenario,
    merge_scenarios,
    single_repo_scenario,
)

if typ.TYPE_CHECKING:
    from simulacat.types import GitHubSimConfig

scenarios("../features/github_app.feature")


class GitHubAppContext(typ.TypedDict):
    """Shared context for GitHub App BDD steps."""

    scenario: ScenarioConfig | None
    scenario_a: ScenarioConfig | None
    scenario_b: ScenarioConfig | None
    merged: ScenarioConfig | None
    config: GitHubSimConfig | None
    token: str | None
    error: Exception | None


@pytest.fixture
def github_app_context() -> GitHubAppContext:
    """Provide shared state for GitHub App steps."""
    return {
        "scenario": None,
        "scenario_a": None,
        "scenario_b": None,
        "merged": None,
        "config": None,
        "token": None,
        "error": None,
    }


@given("a scenario with a GitHub App and installation")
def given_app_and_installation(github_app_context: GitHubAppContext) -> None:
    """Create a scenario with a GitHub App and one installation."""
    github_app_context["scenario"] = ScenarioConfig(
        users=(User(login="octocat"),),
        repositories=(Repository(owner="octocat", name="hello-world"),),
        apps=(GitHubApp(app_slug="test-bot", name="Test Bot"),),
        app_installations=(
            AppInstallation(
                installation_id=1,
                app_slug="test-bot",
                account="octocat",
                repositories=("octocat/hello-world",),
                permissions=("contents",),
            ),
        ),
    )


@when("the scenario is validated and serialized")
def when_validated_and_serialized(github_app_context: GitHubAppContext) -> None:
    """Validate and serialize the scenario."""
    scenario = github_app_context["scenario"]
    assert scenario is not None, "Expected scenario to be set"
    scenario.validate()
    github_app_context["config"] = scenario.to_simulator_config()


@then("the serialized configuration does not include app metadata")
def then_no_app_metadata_in_config(github_app_context: GitHubAppContext) -> None:
    """Verify that app metadata is absent from the serialized configuration."""
    config = github_app_context["config"]
    assert config is not None, "Expected serialized config to be set"
    assert "apps" not in config, "Apps must not appear in simulator config"
    assert "app_installations" not in config, (
        "Installations must not appear in simulator config"
    )


@given("a scenario with a GitHub App installation that has an access token")
def given_installation_with_token(github_app_context: GitHubAppContext) -> None:
    """Create a scenario with an installation that has an access token."""
    github_app_context["scenario"] = ScenarioConfig(
        users=(User(login="octocat"),),
        apps=(GitHubApp(app_slug="auth-bot", name="Auth Bot"),),
        app_installations=(
            AppInstallation(
                installation_id=1,
                app_slug="auth-bot",
                account="octocat",
                access_token="ghs_bdd_token",  # noqa: S106 # test token value
            ),
        ),
    )


@when("the auth token is resolved")
def when_token_resolved(github_app_context: GitHubAppContext) -> None:
    """Resolve the auth token from the scenario."""
    scenario = github_app_context["scenario"]
    assert scenario is not None, "Expected scenario to be set"
    github_app_context["token"] = scenario.resolve_auth_token()


@then("the resolved token matches the installation access token")
def then_token_matches(github_app_context: GitHubAppContext) -> None:
    """Verify the resolved token matches the installation access token."""
    assert github_app_context["token"] == "ghs_bdd_token", (  # noqa: S105 # test token value
        "Expected resolved token to match installation access_token"
    )


@given("a GitHub App scenario and a repository scenario")
def given_app_and_repo_scenarios(github_app_context: GitHubAppContext) -> None:
    """Create an app scenario and a repository scenario for merging."""
    github_app_context["scenario_a"] = github_app_scenario(
        "deploy-bot",
        "Deploy Bot",
        account="octocat",
    )
    github_app_context["scenario_b"] = single_repo_scenario(
        "octocat",
        name="hello-world",
    )


@when("the scenarios are merged")
def when_scenarios_merged(github_app_context: GitHubAppContext) -> None:
    """Merge the two scenarios."""
    left = github_app_context["scenario_a"]
    right = github_app_context["scenario_b"]
    assert left is not None, "Expected left scenario to be set"
    assert right is not None, "Expected right scenario to be set"
    github_app_context["merged"] = merge_scenarios(left, right)


@then("the merged scenario contains the app and the repository")
def then_merged_has_app_and_repo(github_app_context: GitHubAppContext) -> None:
    """Verify the merged scenario contains both app and repository data."""
    merged = github_app_context["merged"]
    assert merged is not None, "Expected merged scenario to be set"
    assert len(merged.apps) == 1, "Expected one app in merged scenario"
    assert merged.apps[0].app_slug == "deploy-bot", (
        "Expected deploy-bot app in merged scenario"
    )
    repo_names = {repo.name for repo in merged.repositories}
    assert "hello-world" in repo_names, (
        "Expected hello-world repository in merged scenario"
    )


@given("a scenario with an installation referencing an undefined app")
def given_invalid_installation(github_app_context: GitHubAppContext) -> None:
    """Create a scenario with an installation that references a missing app."""
    github_app_context["scenario"] = ScenarioConfig(
        users=(User(login="alice"),),
        app_installations=(
            AppInstallation(
                installation_id=1,
                app_slug="missing-bot",
                account="alice",
            ),
        ),
    )


@when("the scenario is validated")
def when_scenario_validated(github_app_context: GitHubAppContext) -> None:
    """Attempt to validate the scenario, capturing any error."""
    scenario = github_app_context["scenario"]
    assert scenario is not None, "Expected scenario to be set"
    try:
        scenario.validate()
        github_app_context["error"] = None
    except ConfigValidationError as exc:
        github_app_context["error"] = exc


@then("a validation error about the app reference is raised")
def then_app_reference_error(github_app_context: GitHubAppContext) -> None:
    """Verify a ConfigValidationError about the app reference was raised."""
    error = github_app_context["error"]
    assert isinstance(error, ConfigValidationError), (
        f"Expected ConfigValidationError, got {error!r}"
    )
    assert "Installation app must reference a defined GitHub App" in str(error), (
        f"Expected app reference error message, got: {error}"
    )
