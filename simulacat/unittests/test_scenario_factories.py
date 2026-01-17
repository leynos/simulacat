"""Unit tests for scenario factories and scenario merging helpers."""

from __future__ import annotations

import pytest

from simulacat.scenario import (
    Branch,
    ConfigValidationError,
    DefaultBranch,
    Organization,
    Repository,
    ScenarioConfig,
    User,
)
from simulacat.scenario_factories import (
    empty_org_scenario,
    merge_scenarios,
    monorepo_with_apps_scenario,
    single_repo_scenario,
)


class TestScenarioFactories:
    """Tests for named scenario factory helpers."""

    @staticmethod
    def test_single_repo_scenario_defaults() -> None:
        """Single repo factory creates a user-owned repository."""
        scenario = single_repo_scenario("alice", name="rocket")

        assert scenario.users == (User(login="alice"),)
        assert scenario.organizations == ()
        assert scenario.repositories == (
            Repository(
                owner="alice",
                name="rocket",
                default_branch=DefaultBranch(name="main"),
            ),
        )
        assert scenario.branches == ()

    @staticmethod
    def test_single_repo_scenario_org_owner() -> None:
        """Single repo factory can create organisation-owned repositories."""
        scenario = single_repo_scenario("acme", name="platform", owner_is_org=True)

        assert scenario.users == ()
        assert scenario.organizations == (Organization(login="acme"),)
        assert scenario.repositories == (
            Repository(
                owner="acme",
                name="platform",
                default_branch=DefaultBranch(name="main"),
            ),
        )

    @staticmethod
    def test_empty_org_scenario() -> None:
        """Empty org factory provides only an organisation entry."""
        scenario = empty_org_scenario("octo-org")

        assert scenario.organizations == (Organization(login="octo-org"),)
        assert scenario.repositories == ()
        assert scenario.users == ()

    @staticmethod
    def test_monorepo_with_apps_scenario_branches() -> None:
        """Monorepo factory emits branches for each app."""
        scenario = monorepo_with_apps_scenario(
            "alice",
            repo="platform",
            apps=("api", "web"),
        )

        branch_names = {branch.name for branch in scenario.branches}
        assert branch_names == {"apps/api", "apps/web"}
        assert scenario.repositories == (
            Repository(
                owner="alice",
                name="platform",
                default_branch=DefaultBranch(name="main"),
            ),
        )
        assert scenario.users == (User(login="alice"),)


class TestScenarioMerging:
    """Tests for scenario composition helpers."""

    @staticmethod
    def test_merge_scenarios_deduplicates_users() -> None:
        """Merging scenarios keeps shared users once."""
        left = single_repo_scenario("alice", name="alpha")
        right = single_repo_scenario("alice", name="beta")

        merged = merge_scenarios(left, right)

        assert merged.users == (User(login="alice"),)
        repo_names = {repo.name for repo in merged.repositories}
        assert repo_names == {"alpha", "beta"}

    @staticmethod
    def test_merge_scenarios_preserves_branch_sets() -> None:
        """Branch definitions from multiple scenarios are merged."""
        left = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
            branches=(Branch(owner="alice", repository="repo", name="main"),),
        )
        right = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
            branches=(Branch(owner="alice", repository="repo", name="feature"),),
        )

        merged = merge_scenarios(left, right)

        branch_names = {branch.name for branch in merged.branches}
        assert branch_names == {"main", "feature"}

    @staticmethod
    def test_merge_scenarios_conflict_raises() -> None:
        """Conflicting repository definitions raise a validation error."""
        left = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
        )
        right = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo", is_private=True),),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Conflicting repository definition",
        ):
            merge_scenarios(left, right)
