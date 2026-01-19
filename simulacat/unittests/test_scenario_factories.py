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

        assert scenario.users == (User(login="alice"),), (
            f"Expected users to contain alice, got {scenario.users!r}"
        )
        assert scenario.organizations == (), (
            f"Expected no organizations, got {scenario.organizations!r}"
        )
        assert scenario.repositories == (
            Repository(
                owner="alice",
                name="rocket",
                default_branch=DefaultBranch(name="main"),
            ),
        ), f"Expected rocket repository with main branch, got {scenario.repositories!r}"
        assert scenario.branches == (), (
            f"Expected no branches, got {scenario.branches!r}"
        )

    @staticmethod
    def test_single_repo_scenario_org_owner() -> None:
        """Single repo factory can create organization-owned repositories."""
        scenario = single_repo_scenario("acme", name="platform", owner_is_org=True)

        assert scenario.users == (), f"Expected no users, got {scenario.users!r}"
        assert scenario.organizations == (Organization(login="acme"),), (
            f"Expected organization acme, got {scenario.organizations!r}"
        )
        assert scenario.repositories == (
            Repository(
                owner="acme",
                name="platform",
                default_branch=DefaultBranch(name="main"),
            ),
        ), (
            "Expected platform repository with main branch, got "
            f"{scenario.repositories!r}"
        )

    @staticmethod
    def test_empty_org_scenario() -> None:
        """Empty org factory provides only an organization entry."""
        scenario = empty_org_scenario("octo-org")

        assert scenario.organizations == (Organization(login="octo-org"),), (
            f"Expected octo-org organization, got {scenario.organizations!r}"
        )
        assert scenario.repositories == (), (
            f"Expected no repositories, got {scenario.repositories!r}"
        )
        assert scenario.users == (), f"Expected no users, got {scenario.users!r}"

    @staticmethod
    def test_empty_org_scenario_rejects_blank_login() -> None:
        """Empty org factory rejects blank organization logins."""
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
        assert branch_names == {"apps/api", "apps/web"}, (
            f"Expected app branches, got {branch_names!r}"
        )
        assert scenario.repositories == (
            Repository(
                owner="alice",
                name="platform",
                default_branch=DefaultBranch(name="main"),
            ),
        ), (
            "Expected platform repository with main branch, got "
            f"{scenario.repositories!r}"
        )
        assert scenario.users == (User(login="alice"),), (
            f"Expected user alice, got {scenario.users!r}"
        )


class TestScenarioMerging:
    """Tests for scenario composition helpers."""

    @staticmethod
    def test_merge_scenarios_deduplicates_users() -> None:
        """Merging scenarios keeps shared users once."""
        left = single_repo_scenario("alice", name="alpha")
        right = single_repo_scenario("alice", name="beta")

        merged = merge_scenarios(left, right)

        assert merged.users == (User(login="alice"),), (
            f"Expected merged users to contain alice, got {merged.users!r}"
        )
        repo_names = {repo.name for repo in merged.repositories}
        assert repo_names == {"alpha", "beta"}, (
            f"Expected repositories alpha and beta, got {repo_names!r}"
        )

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
        assert branch_names == {"main", "feature"}, (
            f"Expected branches main and feature, got {branch_names!r}"
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("left", "right", "pattern"),
        [
            (
                ScenarioConfig(
                    users=(User(login="alice"),),
                    repositories=(Repository(owner="alice", name="repo"),),
                ),
                ScenarioConfig(
                    users=(User(login="alice"),),
                    repositories=(
                        Repository(owner="alice", name="repo", is_private=True),
                    ),
                ),
                "Conflicting repository definition",
            ),
            (
                ScenarioConfig(users=(User(login="alice", organizations=("org",)),)),
                ScenarioConfig(users=(User(login="alice"),)),
                "Conflicting user definition",
            ),
            (
                ScenarioConfig(
                    organizations=(Organization(login="acme", name="Acme"),),
                ),
                ScenarioConfig(
                    organizations=(Organization(login="acme", name="Different"),),
                ),
                "Conflicting organization definition",
            ),
            (
                ScenarioConfig(
                    users=(User(login="alice"),),
                    repositories=(Repository(owner="alice", name="repo"),),
                    branches=(
                        Branch(
                            owner="alice",
                            repository="repo",
                            name="main",
                            sha="a",
                        ),
                    ),
                ),
                ScenarioConfig(
                    users=(User(login="alice"),),
                    repositories=(Repository(owner="alice", name="repo"),),
                    branches=(
                        Branch(
                            owner="alice",
                            repository="repo",
                            name="main",
                            sha="b",
                        ),
                    ),
                ),
                "Conflicting branch definition",
            ),
            (
                ScenarioConfig(
                    users=(User(login="alice"),),
                    repositories=(Repository(owner="alice", name="repo"),),
                    issues=(
                        Issue(
                            owner="alice",
                            repository="repo",
                            number=1,
                            title="Bug",
                        ),
                    ),
                ),
                ScenarioConfig(
                    users=(User(login="alice"),),
                    repositories=(Repository(owner="alice", name="repo"),),
                    issues=(
                        Issue(
                            owner="alice",
                            repository="repo",
                            number=1,
                            title="Other",
                        ),
                    ),
                ),
                "Conflicting issue definition",
            ),
            (
                ScenarioConfig(
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
                ),
                ScenarioConfig(
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
                ),
                "Conflicting pull request definition",
            ),
        ],
        ids=(
            "repo-conflict",
            "user-conflict",
            "org-conflict",
            "branch-conflict",
            "issue-conflict",
            "pull-request-conflict",
        ),
    )
    def test_merge_scenarios_conflicts_raise(
        left: ScenarioConfig,
        right: ScenarioConfig,
        pattern: str,
    ) -> None:
        """Conflicting definitions raise a validation error."""
        with pytest.raises(ConfigValidationError, match=pattern):
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

        assert merged.issues == (issue,), (
            f"Expected issues to be deduplicated, got {merged.issues!r}"
        )
        assert merged.pull_requests == (pull_request,), (
            f"Expected pull requests to be deduplicated, got {merged.pull_requests!r}"
        )
