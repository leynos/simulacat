"""Step definitions for github_sim_config behavioural tests.

These steps validate the consumer-facing behaviour of the github_sim_config
fixture, including defaults, JSON serializability, and function-level
overrides.

Feature files
-------------
The step definitions bind to scenarios in:
- tests/features/github_sim_config.feature

Running tests
-------------
Execute behavioural tests with::

    pytest tests/steps/test_github_sim_config.py -v

Or run all tests via make::

    make test

"""

from __future__ import annotations

import json
import typing as typ

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

if typ.TYPE_CHECKING:
    from simulacat.types import GitHubSimConfig

scenarios("../features/github_sim_config.feature")


class ConfigContext(typ.TypedDict):
    """Shared context for fixture scenarios."""

    config: GitHubSimConfig | None


@pytest.fixture
def config_context() -> ConfigContext:
    """Provide scenario context for github_sim_config tests."""
    return {"config": None}


@given(
    parsers.parse("a github_sim_config fixture with {count:d} users"),
    target_fixture="github_sim_config",
)
def given_fixture_with_users(count: int) -> GitHubSimConfig:
    """Return a configuration containing the requested number of users."""
    return {
        "users": [
            {
                "login": f"user{i}",
                "organizations": [],
            }
            for i in range(count)
        ]
    }


@when("the github_sim_config fixture is requested")
def when_fixture_requested(
    config_context: ConfigContext,
    github_sim_config: GitHubSimConfig,
) -> None:
    """Store the fixture value for later assertions."""
    config_context["config"] = github_sim_config


@then("the configuration is an empty mapping")
def then_configuration_empty(config_context: ConfigContext) -> None:
    """Assert that the configuration is empty."""
    assert config_context["config"] == {}


@then(parsers.parse("the configuration contains {count:d} users"))
def then_configuration_contains_users(
    config_context: ConfigContext,
    count: int,
) -> None:
    """Assert that the configuration includes the expected user count."""
    config = config_context["config"]
    assert config is not None, "Expected configuration to be set"
    users = config.get("users", [])
    assert len(users) == count


@then("the configuration can be serialized to JSON")
def then_configuration_json_serializable(config_context: ConfigContext) -> None:
    """Assert that the configuration is JSON serializable."""
    config = config_context["config"]
    assert config is not None, "Expected configuration to be set"
    json.dumps(config)
