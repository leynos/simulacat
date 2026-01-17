"""Integration tests for github3.py compatibility.

These tests validate that the simulator responses work with common github3.py
usage patterns when accessed via the `github_simulator` fixture.
"""

from __future__ import annotations

import typing as typ

import pytest

from tests import conftest as test_conftest

pytestmark = test_conftest.bun_required

if typ.TYPE_CHECKING:
    from simulacat import GitHubSimConfig


@pytest.fixture
def github_sim_config() -> GitHubSimConfig:
    """Provide a minimal configuration with a user, org, and repositories."""
    return {
        "users": [{"login": "alice", "organizations": ["acme"]}],
        "organizations": [{"login": "acme"}],
        "repositories": [
            {"owner": "alice", "name": "repo1"},
            {"owner": "acme", "name": "orgrepo"},
        ],
    }


def test_repository_lookup_returns_configured_repository(
    github_simulator: object,
) -> None:
    """github3.GitHub.repository can look up repositories on the simulator."""
    repo = github_simulator.repository("alice", "repo1")  # type: ignore[attr-defined]
    assert getattr(repo, "full_name", None) == "alice/repo1"
    language = getattr(repo, "language", None)
    assert language is None or isinstance(language, str)

    owner = getattr(repo, "owner", None)
    assert owner is not None
    assert getattr(owner, "login", None) == "alice"


def test_repository_listing_returns_configured_user_repositories(
    github_simulator: object,
) -> None:
    """github3.GitHub.repositories_by returns repositories from the simulator."""
    repos = list(github_simulator.repositories_by("alice"))  # type: ignore[attr-defined]
    full_names = {getattr(repo, "full_name", "") for repo in repos}
    assert "alice/repo1" in full_names
    for repo in repos:
        language = getattr(repo, "language", None)
        assert language is None or isinstance(language, str)

        owner = getattr(repo, "owner", None)
        assert owner is not None
        assert getattr(owner, "login", None) == "alice"


def test_repository_listing_returns_configured_org_repositories(
    github_simulator: object,
) -> None:
    """github3 Organization repositories can be listed against the simulator."""
    org = github_simulator.organization("acme")  # type: ignore[attr-defined]
    repos = list(org.repositories())
    full_names = {getattr(repo, "full_name", "") for repo in repos}
    assert "acme/orgrepo" in full_names
    for repo in repos:
        language = getattr(repo, "language", None)
        assert language is None or isinstance(language, str)

        owner = getattr(repo, "owner", None)
        assert owner is not None
        assert getattr(owner, "login", None) == "acme"


def test_issue_and_pull_request_retrieval_exposes_rich_body_fields(
    github_simulator: object,
) -> None:
    """github3 Issue / PullRequest retrieval includes body_html/body_text."""
    issue = github_simulator.issue("alice", "repo1", 1)  # type: ignore[attr-defined]
    assert getattr(issue, "number", None) == 1
    assert isinstance(getattr(issue, "body_html", None), str)
    assert isinstance(getattr(issue, "body_text", None), str)

    pr = github_simulator.pull_request("alice", "repo1", 1)  # type: ignore[attr-defined]
    assert getattr(pr, "number", None) == 1
    assert isinstance(getattr(pr, "body_html", None), str)
    assert isinstance(getattr(pr, "body_text", None), str)
