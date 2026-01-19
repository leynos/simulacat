"""Unit tests for access token scenario configuration.

These tests cover validation of token metadata and token selection behaviour.

Running tests
-------------
Execute these tests with::

    pytest simulacat/unittests/test_auth_tokens.py -v

Or run via make::

    make test

"""

from __future__ import annotations

import pytest

from simulacat import (
    AccessToken,
    ConfigValidationError,
    Repository,
    ScenarioConfig,
    User,
)


def test_token_owner_must_exist() -> None:
    """Tokens must reference a defined user or organization."""
    scenario = ScenarioConfig(
        users=(User(login="alice"),),
        tokens=(AccessToken(value="ghs_123", owner="missing"),),
    )

    with pytest.raises(ConfigValidationError, match="Token owner must be"):
        scenario.validate()


def test_token_repository_reference_must_exist() -> None:
    """Token repository scopes must reference configured repositories."""
    scenario = ScenarioConfig(
        users=(User(login="alice"),),
        repositories=(Repository(owner="alice", name="demo"),),
        tokens=(
            AccessToken(
                value="ghs_123",
                owner="alice",
                repositories=("alice/unknown",),
            ),
        ),
    )

    with pytest.raises(
        ConfigValidationError,
        match="Token repository must reference a configured repository",
    ):
        scenario.validate()


def test_token_visibility_must_be_allowed() -> None:
    """Token visibility must be one of the supported values."""
    scenario = ScenarioConfig(
        users=(User(login="alice"),),
        tokens=(
            AccessToken(
                value="ghs_123",
                owner="alice",
                repository_visibility="secret",
            ),
        ),
    )

    with pytest.raises(
        ConfigValidationError,
        match="Token repository visibility",
    ):
        scenario.validate()


def test_resolve_auth_token_prefers_default() -> None:
    """Default tokens select the Authorization header value."""
    scenario = ScenarioConfig(
        users=(User(login="alice"),),
        tokens=(
            AccessToken(value="ghs_one", owner="alice"),
            AccessToken(value="ghs_two", owner="alice"),
        ),
        default_token="ghs_two",  # noqa: S106
    )

    assert scenario.resolve_auth_token() == "ghs_two"


def test_resolve_auth_token_requires_selection_for_multiple_tokens() -> None:
    """Multiple tokens require an explicit default selection."""
    scenario = ScenarioConfig(
        users=(User(login="alice"),),
        tokens=(
            AccessToken(value="ghs_one", owner="alice"),
            AccessToken(value="ghs_two", owner="alice"),
        ),
    )

    with pytest.raises(ConfigValidationError, match="Multiple tokens configured"):
        scenario.resolve_auth_token()
