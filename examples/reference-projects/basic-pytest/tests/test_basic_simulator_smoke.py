"""Smoke tests for the basic simulacat pytest reference project."""

from __future__ import annotations

import shutil
import typing as typ

import pytest

pytestmark = pytest.mark.skipif(
    shutil.which("bun") is None,
    reason="Bun is required for simulator tests",
)

if typ.TYPE_CHECKING:
    from simulacat.types import GitHubSimConfig


@pytest.fixture
def github_sim_config() -> GitHubSimConfig:
    """Return a minimal simulator config for repository lookup tests."""
    return typ.cast(
        "GitHubSimConfig",
        {
            "users": [{"login": "octocat", "organizations": []}],
            "organizations": [],
            "repositories": [{"owner": "octocat", "name": "demo"}],
            "branches": [],
            "blobs": [],
        },
    )


def test_repository_lookup_works(github_simulator: object) -> None:
    """The reference fixture setup supports github3 repository lookups."""
    repo = github_simulator.repository("octocat", "demo")  # type: ignore[attr-defined]
    assert getattr(repo, "full_name", None) == "octocat/demo"
