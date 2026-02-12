"""Unit tests for GitHub App and installation scenario configuration.

These tests cover validation of GitHub App metadata, installation
configuration, and token resolution integration.

Running tests
-------------
Execute these tests with::

    pytest simulacat/unittests/test_github_app.py -v

Or run via make::

    make test

"""

from __future__ import annotations

import typing as typ

import pytest

from simulacat import (
    AppInstallation,
    ConfigValidationError,
    GitHubApp,
    Repository,
    ScenarioConfig,
    User,
)


class TestGitHubAppModel:
    """Group tests for GitHubApp dataclass construction."""

    @staticmethod
    def test_github_app_basic_construction() -> None:
        """GitHubApp can be constructed with required fields."""
        app = GitHubApp(app_slug="my-bot", name="My Bot")

        assert app.app_slug == "my-bot"
        assert app.name == "My Bot"
        assert app.app_id is None
        assert app.owner is None

    @staticmethod
    def test_github_app_with_all_fields() -> None:
        """GitHubApp accepts optional app_id and owner."""
        app = GitHubApp(
            app_slug="deploy-bot",
            name="Deploy Bot",
            app_id=12345,
            owner="octocat",
        )

        assert app.app_slug == "deploy-bot"
        assert app.name == "Deploy Bot"
        assert app.app_id == 12345
        assert app.owner == "octocat"


class TestAppInstallationModel:
    """Group tests for AppInstallation dataclass construction."""

    @staticmethod
    def test_app_installation_basic_construction() -> None:
        """AppInstallation can be constructed with required fields."""
        installation = AppInstallation(
            installation_id=1,
            app_slug="my-bot",
            account="octocat",
        )

        assert installation.installation_id == 1
        assert installation.app_slug == "my-bot"
        assert installation.account == "octocat"
        assert installation.repositories == ()
        assert installation.permissions == ()
        assert installation.access_token is None

    @staticmethod
    def test_app_installation_with_all_fields() -> None:
        """AppInstallation accepts optional repositories, permissions, and token."""
        installation = AppInstallation(
            installation_id=42,
            app_slug="deploy-bot",
            account="octocat",
            repositories=("octocat/hello-world",),
            permissions=("contents", "pull_requests"),
            access_token="ghs_install_token",  # noqa: S106 # test token value
        )

        assert installation.installation_id == 42
        assert installation.repositories == ("octocat/hello-world",)
        assert installation.permissions == ("contents", "pull_requests")
        assert installation.access_token == "ghs_install_token"  # noqa: S105 # test token value

    @staticmethod
    def test_app_installation_normalises_collections() -> None:
        """AppInstallation normalises list inputs to tuples."""
        installation = AppInstallation(
            installation_id=1,
            app_slug="my-bot",
            account="octocat",
            repositories=typ.cast("tuple[str, ...]", ["octocat/repo"]),
            permissions=typ.cast("tuple[str, ...]", ["contents"]),
        )

        assert installation.repositories == ("octocat/repo",)
        assert installation.permissions == ("contents",)

    @staticmethod
    def test_app_installation_rejects_string_repositories() -> None:
        """AppInstallation rejects a bare string for repositories."""
        with pytest.raises(
            TypeError,
            match="Installation repositories must be an iterable of strings",
        ):
            AppInstallation(
                installation_id=1,
                app_slug="my-bot",
                account="octocat",
                repositories=typ.cast("tuple[str, ...]", "octocat/repo"),
            )

    @staticmethod
    def test_app_installation_rejects_string_permissions() -> None:
        """AppInstallation rejects a bare string for permissions."""
        with pytest.raises(
            TypeError,
            match="Installation permissions must be an iterable of strings",
        ):
            AppInstallation(
                installation_id=1,
                app_slug="my-bot",
                account="octocat",
                permissions=typ.cast("tuple[str, ...]", "contents"),
            )


class TestGitHubAppValidation:
    """Group tests for ScenarioConfig validation of GitHub App entries."""

    @staticmethod
    def test_app_slug_must_be_unique() -> None:
        """Duplicate app slugs must be rejected."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(
                GitHubApp(app_slug="my-bot", name="Bot One"),
                GitHubApp(app_slug="my-bot", name="Bot Two"),
            ),
        )

        with pytest.raises(ConfigValidationError, match="Duplicate app slug"):
            scenario.validate()

    @staticmethod
    def test_app_owner_must_exist_when_set() -> None:
        """App owner must reference a defined user or organisation."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot", owner="missing"),),
        )

        with pytest.raises(
            ConfigValidationError,
            match="App owner must be a defined user or organization",
        ):
            scenario.validate()

    @staticmethod
    def test_app_id_must_be_positive_when_set() -> None:
        """App ID must be a positive integer when provided."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot", app_id=-1),),
        )

        with pytest.raises(
            ConfigValidationError, match="App ID must be a positive integer"
        ):
            scenario.validate()


class TestAppInstallationValidation:
    """Group tests for ScenarioConfig validation of installation entries."""

    @staticmethod
    def test_installation_app_slug_must_reference_defined_app() -> None:
        """Installation app_slug must reference a defined GitHubApp."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="real-bot", name="Real Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="missing-bot",
                    account="alice",
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Installation app must reference a defined GitHub App",
        ):
            scenario.validate()

    @staticmethod
    def test_installation_account_must_exist() -> None:
        """Installation account must reference a defined user or organisation."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="missing",
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Installation account must be a defined user or organization",
        ):
            scenario.validate()

    @staticmethod
    def test_installation_repositories_must_reference_defined_repos() -> None:
        """Installation repository references must match defined repositories."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            repositories=(Repository(owner="alice", name="demo"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="alice",
                    repositories=("alice/unknown",),
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Installation repository must reference a configured repository",
        ):
            scenario.validate()

    @staticmethod
    def test_installation_id_must_be_positive() -> None:
        """Installation ID must be a positive integer."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=0,
                    app_slug="my-bot",
                    account="alice",
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Installation ID must be a positive integer",
        ):
            scenario.validate()

    @staticmethod
    def test_installation_id_must_be_unique() -> None:
        """Duplicate installation IDs must be rejected."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="alice",
                ),
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="alice",
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Duplicate installation ID",
        ):
            scenario.validate()

    @staticmethod
    def test_installation_permissions_must_be_unique() -> None:
        """Duplicate permissions on a single installation must be rejected."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="alice",
                    permissions=("contents", "contents"),
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Duplicate installation permission",
        ):
            scenario.validate()


class TestInstallationTokenIntegration:
    """Group tests for installation access_token and token resolution."""

    @staticmethod
    def test_installation_token_resolves_as_single_token() -> None:
        """A single installation token auto-selects for auth."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="alice",
                    access_token="ghs_install",  # noqa: S106 # test token value
                ),
            ),
        )

        assert scenario.resolve_auth_token() == "ghs_install", (
            "Expected installation token to be auto-selected"
        )

    @staticmethod
    def test_installation_token_combined_with_standalone_requires_default() -> None:
        """Multiple tokens (standalone + installation) require default_token."""
        from simulacat import AccessToken

        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot"),),
            tokens=(AccessToken(value="ghs_standalone", owner="alice"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="alice",
                    access_token="ghs_install",  # noqa: S106 # test token value
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Multiple tokens configured",
        ):
            scenario.resolve_auth_token()

    @staticmethod
    def test_installation_token_with_default_selection() -> None:
        """Default token selects between standalone and installation tokens."""
        from simulacat import AccessToken

        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot"),),
            tokens=(AccessToken(value="ghs_standalone", owner="alice"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="alice",
                    access_token="ghs_install",  # noqa: S106 # test token value
                ),
            ),
            default_token="ghs_install",  # noqa: S106 # test token value
        )

        assert scenario.resolve_auth_token() == "ghs_install", (
            "Expected default token to select the installation token"
        )

    @staticmethod
    def test_installation_token_must_not_duplicate_standalone_token() -> None:
        """Installation access_token must not duplicate a standalone token value."""
        from simulacat import AccessToken

        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot"),),
            tokens=(AccessToken(value="ghs_same", owner="alice"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="alice",
                    access_token="ghs_same",  # noqa: S106 # test token value
                ),
            ),
        )

        with pytest.raises(
            ConfigValidationError,
            match="Duplicate token value",
        ):
            scenario.validate()

    @staticmethod
    def test_no_tokens_returns_none() -> None:
        """Apps without access_token and no standalone tokens resolve to None."""
        scenario = ScenarioConfig(
            users=(User(login="alice"),),
            apps=(GitHubApp(app_slug="my-bot", name="Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="alice",
                ),
            ),
        )

        assert scenario.resolve_auth_token() is None, (
            "Expected no token when installation has no access_token"
        )


class TestGitHubAppHappyPath:
    """Group happy-path tests for GitHub App configuration."""

    @staticmethod
    def test_valid_app_and_installation_passes_validation() -> None:
        """A valid GitHub App and installation scenario passes validation."""
        scenario = ScenarioConfig(
            users=(User(login="octocat"),),
            repositories=(Repository(owner="octocat", name="hello-world"),),
            apps=(
                GitHubApp(
                    app_slug="my-bot",
                    name="My Bot",
                    app_id=12345,
                    owner="octocat",
                ),
            ),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="octocat",
                    repositories=("octocat/hello-world",),
                    permissions=("contents", "pull_requests"),
                    access_token="ghs_installation_token",  # noqa: S106 # test token value
                ),
            ),
        )

        scenario.validate()
        assert scenario.resolve_auth_token() == "ghs_installation_token", (
            "Expected configured installation token to resolve"
        )

    @staticmethod
    def test_app_without_installations_validates() -> None:
        """A GitHub App with no installations is valid."""
        scenario = ScenarioConfig(
            users=(User(login="octocat"),),
            apps=(GitHubApp(app_slug="my-bot", name="My Bot"),),
        )

        scenario.validate()

    @staticmethod
    def test_apps_not_serialized_to_simulator_config() -> None:
        """GitHub App metadata must not appear in the simulator configuration."""
        scenario = ScenarioConfig(
            users=(User(login="octocat"),),
            repositories=(Repository(owner="octocat", name="demo"),),
            apps=(GitHubApp(app_slug="my-bot", name="My Bot"),),
            app_installations=(
                AppInstallation(
                    installation_id=1,
                    app_slug="my-bot",
                    account="octocat",
                    repositories=("octocat/demo",),
                ),
            ),
        )

        config = scenario.to_simulator_config()
        assert "apps" not in config, "Apps must not be serialized to simulator config"
        assert "app_installations" not in config, (
            "Installations must not be serialized to simulator config"
        )
