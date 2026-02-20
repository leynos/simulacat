"""Smoke tests for authenticated simulacat pytest reference usage."""

from __future__ import annotations

import collections.abc as cabc
import shutil
import typing as typ

import pytest

from simulacat import AccessToken, Repository, ScenarioConfig, User

pytestmark = pytest.mark.skipif(
    shutil.which("bun") is None,
    reason="Bun is required for simulator tests",
)


@pytest.fixture
def github_sim_config() -> ScenarioConfig:
    """Return an authenticated scenario with one repository."""
    return ScenarioConfig(
        users=(User(login="octocat"),),
        repositories=(Repository(owner="octocat", name="demo"),),
        tokens=(AccessToken(value="ghs_reference_token", owner="octocat"),),
    )


def _authorization_header(client: object) -> str | None:
    """Return the Authorization header from the github3 session when present."""
    session = getattr(client, "session", None) or getattr(client, "_session", None)
    headers = getattr(session, "headers", None)
    if isinstance(headers, cabc.Mapping):
        return typ.cast("str | None", headers.get("Authorization"))
    return None


def test_reference_auth_header_is_applied(github_simulator: object) -> None:
    """The selected scenario token is applied to the client session."""
    assert _authorization_header(github_simulator) == "token ghs_reference_token"


def test_authenticated_repository_lookup_works(github_simulator: object) -> None:
    """Authenticated reference setup still supports repository lookup."""
    repo = github_simulator.repository("octocat", "demo")  # type: ignore[attr-defined]
    assert getattr(repo, "full_name", None) == "octocat/demo"
