"""Unit tests for documented authentication mode limitations.

These tests verify observable limitation behaviour at the model and
configuration layer. They serve as executable documentation: if a future
simulator version changes behaviour, these tests may need updating alongside
the limitation documentation in ``docs/users-guide.md``.

Running tests
-------------
Execute these tests with::

    pytest simulacat/unittests/test_auth_mode_limitations.py -v

Or run via make::

    make test

"""

from __future__ import annotations

from simulacat import (
    AccessToken,
    AppInstallation,
    GitHubApp,
    Repository,
    ScenarioConfig,
    User,
)


class TestTokenLimitationBehaviour:
    """Verify token limitation behaviour documented in the users' guide."""

    @staticmethod
    def test_arbitrary_token_value_accepted() -> None:
        """ScenarioConfig accepts arbitrary token values without format checks.

        Real GitHub validates token prefixes (``ghp_``, ``gho_``, ``ghs_``).
        The simulator accepts any string.
        """
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            tokens=(
                AccessToken(
                    value="not-a-github-token",
                    owner="alice",
                ),
            ),
        )

        scenario.validate()
        assert scenario.resolve_auth_token() == "not-a-github-token", (
            "Expected arbitrary token value to be accepted"
        )

    @staticmethod
    def test_token_metadata_excluded_from_serialized_config() -> None:
        """Token metadata is not serialized to the simulator configuration.

        The simulator does not validate tokens, so token data (permissions,
        repository scoping, visibility) is excluded from the serialized
        output. Tokens flow through the ``Authorization`` header only.
        """
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="demo"),),
            tokens=(
                AccessToken(
                    value="ghs_test",
                    owner="alice",
                    permissions=("repo", "contents"),
                    repositories=("alice/demo",),
                    repository_visibility="private",
                ),
            ),
        )

        config = scenario.to_simulator_config()

        assert "tokens" not in config, (
            "Token metadata must not appear in simulator config"
        )
        assert "access_tokens" not in config, (
            "Token metadata must not appear under any key in simulator config"
        )

    @staticmethod
    def test_token_visibility_excluded_from_serialized_config() -> None:
        """Repository visibility metadata is not serialized to the simulator.

        The ``repository_visibility`` field on ``AccessToken`` documents test
        intent only; the simulator does not enforce visibility rules.
        """
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            tokens=(
                AccessToken(
                    value="ghs_vis",
                    owner="alice",
                    repository_visibility="private",
                ),
            ),
        )

        config = scenario.to_simulator_config()

        # Verify no visibility-related keys appear anywhere in the config.
        for key in config:
            assert "visibility" not in key.lower(), (
                f"Visibility metadata must not appear in config key {key!r}"
            )


class TestGitHubAppLimitationBehaviour:
    """Verify GitHub App limitation behaviour documented in the users' guide."""

    @staticmethod
    def test_installation_access_token_is_literal_value() -> None:
        """Installation access tokens resolve as literal strings.

        Real GitHub exchanges a JWT for a short-lived installation token
        via ``POST /app/installations/{id}/access_tokens``. In simulacat
        the ``access_token`` field is a static literal value with no
        exchange or refresh mechanism.
        """
        scenario = ScenarioConfig(
            users=(User(login="octocat"),),
            apps=(GitHubApp(app_slug="test-bot", name="Test Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="test-bot",
                    account="octocat",
                    access_token="ghs_static_literal",  # noqa: S106 — test token value
                ),
            ),
        )

        resolved = scenario.resolve_auth_token()

        assert resolved == "ghs_static_literal", (
            "Expected installation access token to resolve as the literal value"
        )

    @staticmethod
    def test_installation_permissions_are_metadata_only() -> None:
        """Installation permissions do not affect token resolution.

        Real GitHub enforces per-installation permissions. In simulacat
        the ``permissions`` field documents test intent only; two
        installations with different permissions resolve identically when
        their access tokens are the same.
        """
        scenario_narrow = ScenarioConfig(
            users=(User(login="octocat"),),
            apps=(GitHubApp(app_slug="test-bot", name="Test Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="test-bot",
                    account="octocat",
                    permissions=("contents",),
                    access_token="ghs_same",  # noqa: S106 — test token value
                ),
            ),
        )

        scenario_broad = ScenarioConfig(
            users=(User(login="octocat"),),
            apps=(GitHubApp(app_slug="test-bot", name="Test Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="test-bot",
                    account="octocat",
                    permissions=("contents", "pull_requests", "admin"),
                    access_token="ghs_same",  # noqa: S106 — test token value
                ),
            ),
        )

        assert (
            scenario_narrow.resolve_auth_token() == scenario_broad.resolve_auth_token()
        ), "Expected permissions to have no effect on token resolution"

    @staticmethod
    def test_single_active_token_per_session() -> None:
        """Only one token is active per fixture session.

        Real GitHub accepts a different token per request. In simulacat
        the ``default_token`` field selects a single token that is set
        on the ``github3.py`` session for the entire fixture lifetime.
        ``resolve_auth_token()`` returns exactly one value.
        """
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            tokens=(
                AccessToken(value="ghs_first", owner="alice"),
                AccessToken(value="ghs_second", owner="alice"),
            ),
            default_token="ghs_first",  # noqa: S106 — test default token
        )

        resolved = scenario.resolve_auth_token()

        assert resolved == "ghs_first", (
            "Expected exactly one token to be resolved per session"
        )
        assert isinstance(resolved, str), (
            "Expected resolve_auth_token to return a single string, not a collection"
        )
