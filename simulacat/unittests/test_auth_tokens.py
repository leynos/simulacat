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

import typing as typ

import pytest

from simulacat import (
    AccessToken,
    ConfigValidationError,
    Repository,
    ScenarioConfig,
    User,
)


class TestAuthTokens:
    """Group basic token validation and selection tests."""

    @staticmethod
    def test_token_owner_must_exist() -> None:
        """Tokens must reference a defined user or organization."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            tokens=(AccessToken(value="ghs_123", owner="missing"),),
        )

        with pytest.raises(ConfigValidationError, match="Token owner must be"):
            scenario.validate()

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def test_resolve_auth_token_prefers_default() -> None:
        """Default tokens select the Authorization header value."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            tokens=(
                AccessToken(value="ghs_one", owner="alice"),
                AccessToken(value="ghs_two", owner="alice"),
            ),
            default_token="ghs_two",  # noqa: S106 # TODO(simulacat#123): test token value
        )

        assert scenario.resolve_auth_token() == "ghs_two", (
            "expected default token to be selected"
        )

    @staticmethod
    def test_resolve_auth_token_requires_selection_for_multiple_tokens() -> None:
        """Multiple tokens require an explicit default selection."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            tokens=(
                AccessToken(value="ghs_one", owner="alice"),
                AccessToken(value="ghs_two", owner="alice"),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Multiple tokens configured",
        ):
            scenario.resolve_auth_token()

    @staticmethod
    def test_token_values_must_be_unique() -> None:
        """Duplicate token values must be rejected."""
        scenario = ScenarioConfig(
            users=(User(login="alice"), User(login="bob")),
            tokens=(
                AccessToken(value="ghs_dup", owner="alice"),
                AccessToken(value="ghs_dup", owner="bob"),
            ),
        )

        with pytest.raises(ConfigValidationError, match="Duplicate token value"):
            scenario.validate()

    @staticmethod
    def test_token_permissions_must_be_unique_per_token() -> None:
        """Duplicate permissions on a single token must be rejected."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            tokens=(
                AccessToken(
                    value="ghs_perm",
                    owner="alice",
                    permissions=("repo", "repo"),
                ),
            ),
        )

        with pytest.raises(ConfigValidationError, match="Duplicate token permission"):
            scenario.validate()

    @staticmethod
    def test_token_repositories_must_be_unique_per_token() -> None:
        """Duplicate repository references on a single token must be rejected."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo1"),),
            tokens=(
                AccessToken(
                    value="ghs_repos",
                    owner="alice",
                    repositories=("alice/repo1", "alice/repo1"),
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Duplicate token repository reference",
        ):
            scenario.validate()

    @staticmethod
    def test_token_repository_reference_requires_owner_and_name() -> None:
        """Repository references must include owner and name."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="repo1"),),
            tokens=(
                AccessToken(
                    value="ghs_bad_repo",
                    owner="alice",
                    repositories=("alice/repo1", "owneronly"),
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Token repository must be in the form",
        ):
            scenario.validate()

    @staticmethod
    def test_access_token_normalises_collections() -> None:
        """AccessToken should normalize permissions and repositories to tuples."""
        token = AccessToken(
            value="ghs_norm",
            owner="alice",
            permissions=typ.cast("tuple[str, ...]", ["repo"]),
            repositories=typ.cast("tuple[str, ...]", ["alice/repo1"]),
        )

        assert token.permissions == ("repo",), (
            "Expected permissions to be normalized to a tuple"
        )
        assert token.repositories == ("alice/repo1",), (
            "Expected repositories to be normalized to a tuple"
        )

    @staticmethod
    def test_access_token_rejects_string_collections() -> None:
        """AccessToken should reject string values for collection fields."""
        with pytest.raises(
            TypeError,
            match="Token permissions must be an iterable of strings",
        ):
            AccessToken(
                value="ghs_perm",
                owner="alice",
                permissions=typ.cast("tuple[str, ...]", "repo"),
            )

        with pytest.raises(
            TypeError,
            match="Token repositories must be an iterable of strings",
        ):
            AccessToken(
                value="ghs_repo",
                owner="alice",
                repositories=typ.cast("tuple[str, ...]", "alice/repo"),
            )

    @staticmethod
    def test_resolve_auth_token_returns_none_without_tokens() -> None:
        """No tokens configured should return None."""
        scenario = ScenarioConfig(users=(User(login="alice"),))

        assert scenario.resolve_auth_token() is None, (
            "Expected no token to resolve when none are configured"
        )

    @staticmethod
    def test_resolve_auth_token_uses_single_token() -> None:
        """Single token without a default should be selected."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            tokens=(AccessToken(value="ghs_one", owner="alice"),),
        )

        assert scenario.resolve_auth_token() == "ghs_one", (
            "Expected single token to be selected"
        )

    @staticmethod
    def test_default_token_must_match_configured_tokens() -> None:
        """Default tokens must reference a configured value."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            tokens=(AccessToken(value="ghs_one", owner="alice"),),
            default_token="ghs_missing",  # noqa: S106 # TODO(simulacat#123): add secure token value
        )

        with pytest.raises(
            ConfigValidationError,
            match="Default token must match one of the configured tokens",
        ):
            scenario.validate()

        with pytest.raises(
            ConfigValidationError,
            match="Default token must match one of the configured tokens",
        ):
            scenario.resolve_auth_token()

    @staticmethod
    def test_token_validation_happy_path() -> None:
        """A valid token configuration should pass validation and resolve."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="demo-repo"),),
            tokens=(
                AccessToken(
                    value="ghs_123",
                    owner="alice",
                    permissions=("repo",),
                    repositories=("alice/demo-repo",),
                    repository_visibility="private",
                ),
            ),
        )

        scenario.validate()
        assert scenario.resolve_auth_token() == "ghs_123", (
            "Expected configured token to resolve"
        )
