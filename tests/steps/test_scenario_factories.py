"""BDD step definitions for named scenario factories.

These steps exercise the scenario factory helpers and scenario composition
utilities defined in ``simulacat.scenario_factories``. The scenarios are
specified in ``tests/features/scenario_factories.feature``.
"""

from __future__ import annotations

import typing as typ

import pytest
from pytest_bdd import given, scenarios, then, when

from simulacat.scenario import ConfigValidationError, Repository, ScenarioConfig, User
from simulacat.scenario_factories import (
    merge_scenarios,
    monorepo_with_apps_scenario,
    single_repo_scenario,
)

if typ.TYPE_CHECKING:
    from simulacat.types import GitHubSimConfig

scenarios("../features/scenario_factories.feature")


class ScenarioFactoryContext(typ.TypedDict):
    """Shared context for scenario factory tests."""

    scenario: ScenarioConfig | None
    scenario_a: ScenarioConfig | None
    scenario_b: ScenarioConfig | None
    merged: ScenarioConfig | None
    config: GitHubSimConfig | None
    error: Exception | None


@pytest.fixture
def scenario_factory_context() -> ScenarioFactoryContext:
    """Provide shared state for scenario factory steps."""
    return {
        "scenario": None,
        "scenario_a": None,
        "scenario_b": None,
        "merged": None,
        "config": None,
        "error": None,
    }


def _find_repo(config: GitHubSimConfig, full_name: str) -> dict[str, object]:
    repos = typ.cast("list[dict[str, object]]", config.get("repositories", []))
    for repo in repos:
        owner = repo.get("owner")
        name = repo.get("name")
        if f"{owner}/{name}" == full_name:
            return repo
    msg = f"Repository {full_name!r} not found in config"
    raise AssertionError(msg)


def _find_branch_names(config: GitHubSimConfig, full_name: str) -> set[str]:
    branches = typ.cast("list[dict[str, object]]", config.get("branches", []))
    names: set[str] = set()
    for entry in branches:
        owner = entry.get("owner")
        repo = entry.get("repository")
        if f"{owner}/{repo}" == full_name:
            name = entry.get("name")
            if isinstance(name, str):
                names.add(name)
    return names


@given("a single repository scenario factory")
def given_single_repo_factory(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Create a single repository scenario using the factory."""
    scenario_factory_context["scenario"] = single_repo_scenario(
        "alice",
        name="rocket",
    )


@given("a monorepo scenario with apps")
def given_monorepo_factory(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Create a monorepo scenario with app branches."""
    scenario_factory_context["scenario"] = monorepo_with_apps_scenario(
        "alice",
        repo="platform",
        apps=("api", "web"),
    )


@given("two scenario fragments with shared owner")
def given_mergeable_fragments(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Create two scenario fragments that should merge cleanly."""
    scenario_factory_context["scenario_a"] = single_repo_scenario(
        "alice",
        name="alpha",
    )
    scenario_factory_context["scenario_b"] = single_repo_scenario(
        "alice",
        name="beta",
    )


@given("two conflicting scenario fragments")
def given_conflicting_fragments(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Create two fragments that conflict on repository metadata."""
    left = ScenarioConfig(
        users=(User(login="alice"),),
        repositories=(Repository(owner="alice", name="alpha"),),
    )
    right = ScenarioConfig(
        users=(User(login="alice"),),
        repositories=(Repository(owner="alice", name="alpha", is_private=True),),
    )
    scenario_factory_context["scenario"] = None
    scenario_factory_context["merged"] = None
    scenario_factory_context["error"] = None
    scenario_factory_context["config"] = None
    scenario_factory_context["scenario_a"] = left
    scenario_factory_context["scenario_b"] = right


@when("the scenario is serialized for the simulator")
def when_scenario_serialized(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Serialize the current scenario into simulator configuration."""
    scenario = scenario_factory_context["scenario"]
    assert scenario is not None, "Expected scenario to be set"
    scenario_factory_context["config"] = scenario.to_simulator_config()


@when("the scenario fragments are merged")
def when_scenario_fragments_merged(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Merge scenario fragments created in the given step."""
    left = scenario_factory_context["scenario_a"]
    right = scenario_factory_context["scenario_b"]
    assert left is not None, "Expected left scenario to be set"
    assert right is not None, "Expected right scenario to be set"
    scenario_factory_context["merged"] = merge_scenarios(left, right)


@when("the conflicting fragments are merged")
def when_conflicting_fragments_merged(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Attempt to merge conflicting scenario fragments."""
    left = scenario_factory_context["scenario_a"]
    right = scenario_factory_context["scenario_b"]
    assert left is not None, "Expected left scenario to be set"
    assert right is not None, "Expected right scenario to be set"
    try:
        scenario_factory_context["merged"] = merge_scenarios(left, right)
        scenario_factory_context["error"] = None
    except ConfigValidationError as exc:
        scenario_factory_context["merged"] = None
        scenario_factory_context["error"] = exc


@then('the configuration includes repository "alice/rocket"')
def then_configuration_includes_repo(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Verify the single repository appears in the config."""
    config = scenario_factory_context["config"]
    assert config is not None, "Expected serialized config to be set"
    _find_repo(config, "alice/rocket")


@then("the configuration includes app branches")
def then_configuration_includes_app_branches(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Verify app branch names are emitted for the monorepo."""
    config = scenario_factory_context["config"]
    assert config is not None, "Expected serialized config to be set"
    branch_names = _find_branch_names(config, "alice/platform")
    assert {"apps/api", "apps/web"}.issubset(branch_names)


@then("the merged scenario contains 2 repositories")
def then_merged_scenario_contains_repos(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Verify merged scenario includes two repositories."""
    merged = scenario_factory_context["merged"]
    assert merged is not None, "Expected merged scenario to be set"
    assert len(merged.repositories) == 2


@then("a scenario conflict error is reported")
def then_conflict_error_reported(
    scenario_factory_context: ScenarioFactoryContext,
) -> None:
    """Verify a ConfigValidationError was raised during merge."""
    error = scenario_factory_context["error"]
    assert isinstance(error, ConfigValidationError), (
        f"Expected ConfigValidationError, got {error!r}"
    )
