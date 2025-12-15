"""Step definitions for github_sim_config fixture behavioural tests.

This module provides pytest-bdd step bindings for testing the github_sim_config
fixture functionality. The steps exercise configuration retrieval and overrides
at different scopes using pytest-bdd's target_fixture mechanism for realistic
fixture injection.

Feature files
-------------
The step definitions bind to scenarios in:
- tests/features/github_sim_config_fixture.feature

Running tests
-------------
Execute the behavioural tests with::

    pytest tests/steps/test_github_sim_config_fixture.py -v

Or run all tests including these::

    make test

"""

from __future__ import annotations

import json
import typing as typ

import pytest
from pytest_bdd import given, scenarios, then, when

if typ.TYPE_CHECKING:
    from simulacat.types import GitHubSimConfig

scenarios("../features/github_sim_config_fixture.feature")


class SerializationContext(typ.TypedDict):
    """Context object for JSON serialization test state."""

    serialized: str | None
    error: Exception | None


@pytest.fixture
def serialization_context() -> SerializationContext:
    """Provide a context for serialization scenarios."""
    return {
        "serialized": None,
        "error": None,
    }


@pytest.fixture
def configs_received() -> list[GitHubSimConfig]:
    """Track configurations received by multiple test requests."""
    return []


# -----------------------------------------------------------------------------
# Given steps using target_fixture to inject configurations
# -----------------------------------------------------------------------------


@given("the pytest framework is available")
def given_pytest_available() -> None:
    """Verify pytest is available (always true in pytest context)."""


@given("a github_sim_config with test data", target_fixture="github_sim_config")
def given_config_with_test_data() -> GitHubSimConfig:
    """Set up a configuration with test data via fixture injection."""
    return {
        "users": [{"login": "testuser", "organizations": []}],
        "organizations": [],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }


@given("a module-level github_sim_config override", target_fixture="github_sim_config")
def given_module_level_override() -> GitHubSimConfig:
    """Provide a module-level configuration override via target_fixture."""
    return {
        "users": [{"login": "module-user", "organizations": []}],
        "organizations": [],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }


@given(
    "a function-level github_sim_config override", target_fixture="github_sim_config"
)
def given_function_level_override() -> GitHubSimConfig:
    """Provide a function-level configuration override (takes precedence)."""
    return {
        "users": [{"login": "function-user", "organizations": []}],
        "organizations": [],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }


@given(
    "a module-level github_sim_config override with users",
    target_fixture="github_sim_config",
)
def given_module_override_with_users() -> GitHubSimConfig:
    """Set up a module-level configuration with users via target_fixture."""
    return {
        "users": [{"login": "shared-user", "organizations": []}],
        "organizations": [],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }


# -----------------------------------------------------------------------------
# When steps that use the injected github_sim_config fixture
# -----------------------------------------------------------------------------


@when("the github_sim_config fixture is requested without overrides")
def when_config_requested_no_overrides(github_sim_config: GitHubSimConfig) -> None:
    """Request the default github_sim_config fixture (injected by pytest)."""
    # The fixture value is already available via injection
    _ = github_sim_config


@when("the configuration is serialized to JSON")
def when_config_serialized(
    github_sim_config: GitHubSimConfig, serialization_context: SerializationContext
) -> None:
    """Attempt to serialize the configuration to JSON."""
    try:
        serialization_context["serialized"] = json.dumps(github_sim_config)
        serialization_context["error"] = None
    except (TypeError, ValueError) as exc:
        serialization_context["error"] = exc


@when("the github_sim_config fixture is resolved")
def when_config_resolved(github_sim_config: GitHubSimConfig) -> None:
    """Resolve the configuration from prior given steps via fixture injection."""
    _ = github_sim_config


@when("multiple tests request github_sim_config")
def when_multiple_tests_request(
    github_sim_config: GitHubSimConfig, configs_received: list[GitHubSimConfig]
) -> None:
    """Simulate multiple tests requesting the configuration."""
    # Simulate multiple requests by recording the same fixture value twice
    configs_received.extend([github_sim_config, github_sim_config])


# -----------------------------------------------------------------------------
# Then steps that verify fixture values
# -----------------------------------------------------------------------------


@then("it returns an empty mapping")
def then_returns_empty_mapping(github_sim_config: GitHubSimConfig) -> None:
    """Verify the configuration is an empty mapping."""
    assert isinstance(github_sim_config, dict), (
        f"Expected dict, got {type(github_sim_config)}"
    )
    assert github_sim_config == {}, f"Expected empty mapping, got {github_sim_config}"


@then("serialization succeeds without error")
def then_serialization_succeeds(serialization_context: SerializationContext) -> None:
    """Verify JSON serialization succeeded."""
    assert serialization_context["error"] is None, (
        f"Serialization failed: {serialization_context['error']}"
    )
    assert serialization_context["serialized"] is not None, "Expected serialized output"


@then("the function-level configuration is used")
def then_function_config_used(github_sim_config: GitHubSimConfig) -> None:
    """Verify function-level configuration takes precedence."""
    users = github_sim_config.get("users", [])
    assert len(users) > 0, "Expected at least one user"
    assert users[0]["login"] == "function-user", (
        f"Expected function-user, got {users[0]['login']}"
    )


@then("all tests receive the module-level configuration")
def then_all_receive_module_config(configs_received: list[GitHubSimConfig]) -> None:
    """Verify all tests receive the same module-level configuration."""
    assert len(configs_received) == 2, (
        f"Expected 2 configs, got {len(configs_received)}"
    )
    for cfg in configs_received:
        users = cfg.get("users", [])
        assert len(users) > 0, "Expected at least one user"
        assert users[0]["login"] == "shared-user", (
            f"Expected shared-user, got {users[0]['login']}"
        )
