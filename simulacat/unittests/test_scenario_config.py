"""Unit tests for scenario configuration helpers."""

from __future__ import annotations

import pytest

from simulacat.scenario import (
    Branch,
    ConfigValidationError,
    DefaultBranch,
    Issue,
    PullRequest,
    Repository,
    ScenarioConfig,
    User,
)


class TestScenarioConfig:
    """Tests for ScenarioConfig serialization and validation."""

    @staticmethod
    def test_serializes_default_branch_metadata() -> None:
        """Default branches are added to the branch list and repo metadata."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(
                Repository(
                    owner="alice",
                    name="rocket",
                    default_branch=DefaultBranch(name="main", sha="abc123"),
                ),
            ),
            branches=(Branch(owner="alice", repository="rocket", name="dev"),),
        )

        config = scenario.to_simulator_config()

        assert config["repositories"][0]["default_branch"] == "main"
        branch_names = {branch["name"] for branch in config["branches"]}
        assert branch_names == {"dev", "main"}
        assert config["blobs"] == []

    @staticmethod
    def test_validation_rejects_unknown_repository_owner() -> None:
        """Repository owners must be known users or organizations."""
        scenario = ScenarioConfig(
            repositories=(Repository(owner="ghost", name="repo"),),
        )

        with pytest.raises(ConfigValidationError, match="ghost"):
            scenario.to_simulator_config()

    @staticmethod
    def test_validation_rejects_conflicting_default_branch() -> None:
        """Conflicting default branch metadata raises a clear error."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(
                Repository(
                    owner="alice",
                    name="rocket",
                    default_branch=DefaultBranch(name="main", sha="abc123"),
                ),
            ),
            branches=(
                Branch(
                    owner="alice",
                    repository="rocket",
                    name="main",
                    sha="deadbeef",
                ),
            ),
        )

        with pytest.raises(ConfigValidationError, match="default branch"):
            scenario.to_simulator_config()

    @staticmethod
    def test_default_branch_metadata_merges_with_branch_sha() -> None:
        """Default branch metadata merges with explicit branch data."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(
                Repository(
                    owner="alice",
                    name="rocket",
                    default_branch=DefaultBranch(name="main", is_protected=True),
                ),
            ),
            branches=(
                Branch(
                    owner="alice",
                    repository="rocket",
                    name="main",
                    sha="sha-from-branch",
                ),
            ),
        )

        config = scenario.to_simulator_config()
        branch = next(entry for entry in config["branches"] if entry["name"] == "main")

        assert branch["sha"] == "sha-from-branch"
        assert branch["protected"] is True

    @staticmethod
    def test_default_branch_metadata_merges_with_branch_protection() -> None:
        """Explicit branch protection merges with default branch metadata."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(
                Repository(
                    owner="alice",
                    name="rocket",
                    default_branch=DefaultBranch(name="main", sha="sha-from-default"),
                ),
            ),
            branches=(
                Branch(
                    owner="alice",
                    repository="rocket",
                    name="main",
                    is_protected=True,
                ),
            ),
        )

        config = scenario.to_simulator_config()
        branch = next(entry for entry in config["branches"] if entry["name"] == "main")

        assert branch["sha"] == "sha-from-default"
        assert branch["protected"] is True

    @staticmethod
    def test_include_unsupported_serializes_issues_and_pulls() -> None:
        """Issues and pull requests are included when requested."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="rocket"),),
            issues=(Issue(owner="alice", repository="rocket", number=1, title="Bug"),),
            pull_requests=(
                PullRequest(
                    owner="alice",
                    repository="rocket",
                    number=2,
                    title="Fix",
                    base_branch="main",
                    head_branch="feature",
                ),
            ),
            branches=(
                Branch(owner="alice", repository="rocket", name="main"),
                Branch(owner="alice", repository="rocket", name="feature"),
            ),
        )

        config = scenario.to_simulator_config(include_unsupported=True)

        assert config["issues"][0]["number"] == 1
        assert config["pull_requests"][0]["number"] == 2

        stripped = scenario.to_simulator_config()

        assert "issues" not in stripped
        assert "pull_requests" not in stripped

    @staticmethod
    def test_issue_with_unknown_repository_fails_validation() -> None:
        """Issues must reference repositories in the scenario."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="rocket"),),
            issues=(
                Issue(
                    owner="alice",
                    repository="unknown-repo",
                    number=1,
                    title="Bug",
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Issue refers to unknown repository alice/unknown-repo",
        ):
            scenario.to_simulator_config(include_unsupported=True)

    @staticmethod
    def test_duplicate_issue_numbers_fail_validation() -> None:
        """Duplicate issue numbers per repository are rejected."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="rocket"),),
            issues=(
                Issue(owner="alice", repository="rocket", number=1, title="First"),
                Issue(owner="alice", repository="rocket", number=1, title="Dup"),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Duplicate issue number 1 for alice/rocket",
        ):
            scenario.to_simulator_config(include_unsupported=True)

    @staticmethod
    def test_duplicate_pull_request_numbers_fail_validation() -> None:
        """Duplicate pull request numbers per repository are rejected."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="rocket"),),
            pull_requests=(
                PullRequest(
                    owner="alice",
                    repository="rocket",
                    number=2,
                    title="Feature",
                ),
                PullRequest(
                    owner="alice",
                    repository="rocket",
                    number=2,
                    title="Feature again",
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Duplicate pull request number 2 for alice/rocket",
        ):
            scenario.to_simulator_config(include_unsupported=True)

    @staticmethod
    def test_invalid_issue_state_fails_validation() -> None:
        """Issue state must be one of the supported values."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="rocket"),),
            issues=(
                Issue(
                    owner="alice",
                    repository="rocket",
                    number=1,
                    title="Bug",
                    state="merged",
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Issue state must be one of",
        ):
            scenario.to_simulator_config(include_unsupported=True)

    @staticmethod
    def test_invalid_pull_request_state_fails_validation() -> None:
        """Pull request state must be one of the supported values."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="rocket"),),
            pull_requests=(
                PullRequest(
                    owner="alice",
                    repository="rocket",
                    number=2,
                    title="Feature",
                    state="merged",
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Pull request state must be one of",
        ):
            scenario.to_simulator_config(include_unsupported=True)

    @staticmethod
    def test_pull_request_branch_validation() -> None:
        """Pull requests must reference known branches when provided."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(
                Repository(
                    owner="alice",
                    name="rocket",
                    default_branch=DefaultBranch(name="main"),
                ),
            ),
            pull_requests=(
                PullRequest(
                    owner="alice",
                    repository="rocket",
                    number=3,
                    title="Feature",
                    base_branch="main",
                    head_branch="missing",
                ),
            ),
        )

        with pytest.raises(ConfigValidationError, match="missing"):
            scenario.to_simulator_config(include_unsupported=True)
