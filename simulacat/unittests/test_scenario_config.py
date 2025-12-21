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
        """Repository owners must be known users or organisations."""
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
            scenario.to_simulator_config()
