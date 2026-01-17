"""Unit tests for scenario factories and scenario merging helpers."""

from __future__ import annotations

import pytest

from simulacat.scenario import (
    Branch,
    ConfigValidationError,
    DefaultBranch,
    Issue,
    Organization,
    PullRequest,
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
    def test_empty_org_scenario_rejects_blank_login() -> None:
        """Empty org factory rejects blank organisation logins."""
        with pytest.raises(ConfigValidationError, match="Organization login"):
            empty_org_scenario(" ")

    @staticmethod
    def test_single_repo_scenario_rejects_blank_owner() -> None:
        """Single repo factory rejects blank owners."""
        with pytest.raises(ConfigValidationError, match="Owner"):
            single_repo_scenario("")

    @staticmethod
    def test_monorepo_with_apps_requires_apps() -> None:
        """Monorepo factory requires at least one app name."""
        with pytest.raises(ConfigValidationError, match="Apps must include"):
            monorepo_with_apps_scenario("alice", apps=())

    @staticmethod
    def test_monorepo_with_apps_rejects_duplicate_apps() -> None:
        """Monorepo factory rejects duplicate app names."""
        with pytest.raises(ConfigValidationError, match="Duplicate app name"):
            monorepo_with_apps_scenario("alice", apps=("api", "api"))

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

    @staticmethod
    def test_merge_scenarios_user_conflict_raises() -> None:
        """Conflicting user definitions raise a validation error."""
        left = ScenarioConfig(users=(User(login="alice", organizations=("org",)),))
        right = ScenarioConfig(users=(User(login="alice"),))

        with pytest.raises(ConfigValidationError, match="Conflicting user"):
            merge_scenarios(left, right)

    @staticmethod
    def test_merge_scenarios_org_conflict_raises() -> None:
        """Conflicting organisation definitions raise a validation error."""
        left = ScenarioConfig(organizations=(Organization(login="acme", name="Acme"),))
        right = ScenarioConfig(
            organizations=(Organization(login="acme", name="Different"),),
        )

        with pytest.raises(ConfigValidationError, match="Conflicting organization"):
            merge_scenarios(left, right)

    @staticmethod
    def test_merge_scenarios_branch_conflict_raises() -> None:
        """Conflicting branch definitions raise a validation error."""
        left = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
            branches=(Branch(owner="alice", repository="repo", name="main", sha="a"),),
        )
        right = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
            branches=(Branch(owner="alice", repository="repo", name="main", sha="b"),),
        )

        with pytest.raises(ConfigValidationError, match="Conflicting branch"):
            merge_scenarios(left, right)

    @staticmethod
    def test_merge_scenarios_issue_conflict_raises() -> None:
        """Conflicting issue definitions raise a validation error."""
        left = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
            issues=(Issue(owner="alice", repository="repo", number=1, title="Bug"),),
        )
        right = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
            issues=(Issue(owner="alice", repository="repo", number=1, title="Other"),),
        )

        with pytest.raises(ConfigValidationError, match="Conflicting issue"):
            merge_scenarios(left, right)

    @staticmethod
    def test_merge_scenarios_pull_request_conflict_raises() -> None:
        """Conflicting pull request definitions raise a validation error."""
        left = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
            pull_requests=(
                PullRequest(
                    owner="alice",
                    repository="repo",
                    number=2,
                    title="Feature",
                ),
            ),
        )
        right = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
            pull_requests=(
                PullRequest(
                    owner="alice",
                    repository="repo",
                    number=2,
                    title="Different",
                ),
            ),
        )

        with pytest.raises(ConfigValidationError, match="Conflicting pull request"):
            merge_scenarios(left, right)

    @staticmethod
    def test_merge_scenarios_deduplicates_issues_and_pulls() -> None:
        """Identical issues and pull requests are deduplicated."""
        issue = Issue(owner="alice", repository="repo", number=1, title="Bug")
        pull_request = PullRequest(
            owner="alice",
            repository="repo",
            number=2,
            title="Feature",
        )
        left = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
            issues=(issue,),
            pull_requests=(pull_request,),
        )
        right = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo"),),
            issues=(issue,),
            pull_requests=(pull_request,),
        )

        merged = merge_scenarios(left, right)

        assert merged.issues == (issue,)
        assert merged.pull_requests == (pull_request,)
