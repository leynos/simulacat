"""BDD step definitions for authentication mode limitation behaviour.

These steps demonstrate the documented limitations of each authentication
mode compared with real GitHub. They serve as executable documentation
for the "Authentication mode limitations" section in ``docs/users-guide.md``.

Feature files
-------------
The step definitions bind to scenarios in:
- tests/features/auth_mode_limitations.feature

Running tests
-------------
Execute behavioural tests with::

    pytest tests/steps/test_auth_mode_limitations.py -v

Or run all tests via make::

    make test

"""

from __future__ import annotations

import typing as typ

import pytest
from pytest_bdd import given, scenarios, then, when

from simulacat import (
    AccessToken,
    AppInstallation,
    ConfigValidationError,
    GitHubApp,
    Repository,
    ScenarioConfig,
    User,
)

if typ.TYPE_CHECKING:
    from simulacat.types import GitHubSimConfig

scenarios("../features/auth_mode_limitations.feature")


class LimitationsContext(typ.TypedDict):
    """Shared context for authentication limitation BDD steps."""

    scenario: ScenarioConfig | None
    config: GitHubSimConfig | None
    token: str | None
    error: Exception | None


@pytest.fixture
def limitations_context() -> LimitationsContext:
    """Provide shared state for limitation steps."""
    return {
        "scenario": None,
        "config": None,
        "token": None,
        "error": None,
    }


# -- Given steps --------------------------------------------------------


@given("a scenario with a non-standard token value")
def given_nonstandard_token(limitations_context: LimitationsContext) -> None:
    """Create a scenario with a token that does not follow GitHub format."""
    limitations_context["scenario"] = ScenarioConfig(
        users=(User(login="alice"),),
        tokens=(
            AccessToken(
                value="this-is-not-a-real-github-token-format",
                owner="alice",
            ),
        ),
    )


@given("a scenario with a token that has permissions and repository scoping")
def given_token_with_permissions(
    limitations_context: LimitationsContext,
) -> None:
    """Create a scenario with a fully-scoped token."""
    limitations_context["scenario"] = ScenarioConfig(
        users=(User(login="alice"),),
        repositories=(Repository(owner="alice", name="demo"),),
        tokens=(
            AccessToken(
                value="ghs_scoped",
                owner="alice",
                permissions=("repo", "contents"),
                repositories=("alice/demo",),
            ),
        ),
    )


@given("a scenario with a token that has repository visibility metadata")
def given_token_with_visibility(
    limitations_context: LimitationsContext,
) -> None:
    """Create a scenario with a token that declares visibility scope."""
    limitations_context["scenario"] = ScenarioConfig(
        users=(User(login="alice"),),
        tokens=(
            AccessToken(
                value="ghs_vis",
                owner="alice",
                repository_visibility="private",
            ),
        ),
    )


@given("a scenario with a GitHub App and an installation with permissions")
def given_app_with_permissions(
    limitations_context: LimitationsContext,
) -> None:
    """Create a scenario with an app, installation, and permissions."""
    limitations_context["scenario"] = ScenarioConfig(
        users=(User(login="octocat"),),
        repositories=(Repository(owner="octocat", name="hello-world"),),
        apps=(GitHubApp(app_slug="limit-bot", name="Limit Bot"),),
        app_installations=(
            AppInstallation(
                installation_id=1,
                app_slug="limit-bot",
                account="octocat",
                repositories=("octocat/hello-world",),
                permissions=("contents", "pull_requests"),
            ),
        ),
    )


@given(
    "a scenario with an installation that declares a static access token",
)
def given_installation_with_static_token(
    limitations_context: LimitationsContext,
) -> None:
    """Create a scenario with an installation access token."""
    limitations_context["scenario"] = ScenarioConfig(
        users=(User(login="octocat"),),
        apps=(GitHubApp(app_slug="token-bot", name="Token Bot"),),
        app_installations=(
            AppInstallation(
                installation_id=1,
                app_slug="token-bot",
                account="octocat",
                access_token="ghs_literal_static_value",  # noqa: S106 — FIXME: use env or fixture for test tokens
            ),
        ),
    )


# -- When steps ---------------------------------------------------------


@when("the limitation scenario is validated")
def when_limitation_validated(
    limitations_context: LimitationsContext,
) -> None:
    """Validate the scenario, capturing any error."""
    scenario = limitations_context["scenario"]
    assert scenario is not None, "Expected scenario to be set"
    try:
        scenario.validate()
        limitations_context["error"] = None
    except ConfigValidationError as exc:
        limitations_context["error"] = exc


@when("the limitation scenario is validated and serialized")
def when_limitation_validated_and_serialized(
    limitations_context: LimitationsContext,
) -> None:
    """Validate and serialize the scenario."""
    scenario = limitations_context["scenario"]
    assert scenario is not None, "Expected scenario to be set"
    scenario.validate()
    limitations_context["config"] = scenario.to_simulator_config()


@when("the limitation scenario auth token is resolved")
def when_limitation_token_resolved(
    limitations_context: LimitationsContext,
) -> None:
    """Resolve the auth token from the scenario."""
    scenario = limitations_context["scenario"]
    assert scenario is not None, "Expected scenario to be set"
    limitations_context["token"] = scenario.resolve_auth_token()


# -- Then steps ---------------------------------------------------------


@then("the scenario passes validation without error")
def then_no_validation_error(
    limitations_context: LimitationsContext,
) -> None:
    """Assert that validation completed without raising an exception."""
    error = limitations_context["error"]
    assert error is None, f"Expected no validation error, got: {error!r}"


@then("the serialized output does not contain token metadata")
def then_no_token_metadata(limitations_context: LimitationsContext) -> None:
    """Assert that the serialized config excludes token metadata."""
    config = limitations_context["config"]
    assert config is not None, "Expected serialized config to be set"
    assert "tokens" not in config, "Token metadata must not appear in simulator config"
    assert "access_tokens" not in config, (
        "Token metadata must not appear under any key in simulator config"
    )


@then("the serialized output does not contain visibility metadata")
def then_no_visibility_metadata(
    limitations_context: LimitationsContext,
) -> None:
    """Assert that the serialized config excludes visibility metadata."""
    config = limitations_context["config"]
    assert config is not None, "Expected serialized config to be set"
    for key in config:
        assert "visibility" not in key.lower(), (
            f"Visibility metadata must not appear in config key {key!r}"
        )


@then("the serialized output does not contain app or installation fields")
def then_no_app_fields(limitations_context: LimitationsContext) -> None:
    """Assert that the serialized config excludes app and installation data."""
    config = limitations_context["config"]
    assert config is not None, "Expected serialized config to be set"
    assert "apps" not in config, "App metadata must not appear in simulator config"
    assert "app_installations" not in config, (
        "Installation metadata must not appear in simulator config"
    )


@then("the resolved token is the literal access token string")
def then_literal_token(limitations_context: LimitationsContext) -> None:
    """Assert that the resolved token is the literal static string."""
    token = limitations_context["token"]
    assert token == "ghs_literal_static_value", (  # noqa: S105 — FIXME: use env or fixture for test tokens
        "Expected resolved token to be the literal access_token value"
    )
