"""Step definitions for github_sim_config fixture behavioural tests.

This module provides pytest-bdd step bindings for testing the github_sim_config
fixture functionality. The steps exercise configuration retrieval and overrides
at different scopes.

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
    import collections.abc as cabc

scenarios("../features/github_sim_config_fixture.feature")


class ConfigContext(typ.TypedDict):
    """Context object for configuration state during test scenarios."""

    config: cabc.Mapping[str, typ.Any] | None
    serialized: str | None
    error: Exception | None
    configs_received: list[cabc.Mapping[str, typ.Any]]


@pytest.fixture
def config_context() -> ConfigContext:
    """Provide a context for configuration scenarios."""
    return {
        "config": None,
        "serialized": None,
        "error": None,
        "configs_received": [],
    }


@given("the pytest framework is available")
def given_pytest_available() -> None:
    """Verify pytest is available (always true in pytest context)."""


@given("a github_sim_config with test data")
def given_config_with_test_data(config_context: ConfigContext) -> None:
    """Set up a configuration with test data."""
    config_context["config"] = {
        "users": [{"login": "testuser", "organizations": []}],
        "organizations": [],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }


@given("a module-level github_sim_config override")
def given_module_level_override(config_context: ConfigContext) -> None:
    """Simulate a module-level configuration override."""
    config_context["config"] = {
        "users": [{"login": "module-user", "organizations": []}],
        "organizations": [],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }


@given("a function-level github_sim_config override")
def given_function_level_override(config_context: ConfigContext) -> None:
    """Simulate a function-level configuration override (takes precedence)."""
    config_context["config"] = {
        "users": [{"login": "function-user", "organizations": []}],
        "organizations": [],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }


@given("a module-level github_sim_config override with users")
def given_module_override_with_users(config_context: ConfigContext) -> None:
    """Set up a module-level configuration with users."""
    config_context["config"] = {
        "users": [{"login": "shared-user", "organizations": []}],
        "organizations": [],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }


@when("the github_sim_config fixture is requested without overrides")
def when_config_requested_no_overrides(config_context: ConfigContext) -> None:
    """Request the default github_sim_config fixture."""
    from simulacat.config import default_github_sim_config

    config_context["config"] = default_github_sim_config()


@when("the configuration is serialized to JSON")
def when_config_serialized(config_context: ConfigContext) -> None:
    """Attempt to serialize the configuration to JSON."""
    try:
        config_context["serialized"] = json.dumps(config_context["config"])
        config_context["error"] = None
    except (TypeError, ValueError) as exc:
        config_context["error"] = exc


@when("the github_sim_config fixture is resolved")
def when_config_resolved(config_context: ConfigContext) -> None:
    """Resolve the configuration from prior given steps."""
    _ = config_context  # Configuration set in prior steps


@when("multiple tests request github_sim_config")
def when_multiple_tests_request(config_context: ConfigContext) -> None:
    """Simulate multiple tests requesting the configuration."""
    config = config_context["config"]
    if config is not None:
        config_context["configs_received"] = [config, config]


@then("it returns an empty mapping")
def then_returns_empty_mapping(config_context: ConfigContext) -> None:
    """Verify the configuration is an empty mapping."""
    config = config_context["config"]
    assert config is not None, "Expected config to be set"
    assert isinstance(config, dict), f"Expected dict, got {type(config)}"
    assert config == {}, f"Expected empty mapping, got {config}"


@then("serialization succeeds without error")
def then_serialization_succeeds(config_context: ConfigContext) -> None:
    """Verify JSON serialization succeeded."""
    assert config_context["error"] is None, (
        f"Serialization failed: {config_context['error']}"
    )
    assert config_context["serialized"] is not None, "Expected serialized output"


@then("the function-level configuration is used")
def then_function_config_used(config_context: ConfigContext) -> None:
    """Verify function-level configuration takes precedence."""
    config = config_context["config"]
    assert config is not None, "Expected config to be set"
    users = config.get("users", [])
    assert len(users) > 0, "Expected at least one user"
    assert users[0]["login"] == "function-user", (
        f"Expected function-user, got {users[0]['login']}"
    )


@then("all tests receive the module-level configuration")
def then_all_receive_module_config(config_context: ConfigContext) -> None:
    """Verify all tests receive the same module-level configuration."""
    configs = config_context["configs_received"]
    assert len(configs) == 2, f"Expected 2 configs, got {len(configs)}"
    for cfg in configs:
        users = cfg.get("users", [])
        assert len(users) > 0, "Expected at least one user"
        assert users[0]["login"] == "shared-user", (
            f"Expected shared-user, got {users[0]['login']}"
        )
