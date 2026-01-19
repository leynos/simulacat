"""Step definitions for github_simulator authentication behaviour.

These steps validate the Authorization header behaviour of the
`github_simulator` fixture when tokens are provided.

Feature files
-------------
The step definitions bind to scenarios in:
- tests/features/github_simulator_auth.feature

Running tests
-------------
Execute behavioural tests with::

    pytest tests/steps/test_github_simulator_auth.py -v

Or run all tests via make::

    make test

"""

from __future__ import annotations

import collections.abc as cabc
import typing as typ

import pytest
from pytest_bdd import given, scenarios, then, when

from tests import conftest as test_conftest

pytestmark = test_conftest.bun_required

if typ.TYPE_CHECKING:
    from simulacat.types import GitHubSimConfig


scenarios("../features/github_simulator_auth.feature")


class ClientContext(typ.TypedDict):
    """Scenario context for github_simulator auth steps."""

    client: object | None


@pytest.fixture
def client_context() -> ClientContext:
    """Provide scenario context for github_simulator auth steps."""
    return {"client": None}


@given(
    "a github_sim_config fixture with an auth token",
    target_fixture="github_sim_config",
)
def given_config_with_auth_token() -> GitHubSimConfig:
    """Return configuration with metadata that includes an auth token."""
    return typ.cast(
        "GitHubSimConfig",
        {
            "__simulacat__": {"auth_token": "test-token"},
        },
    )


@given(
    "a github_sim_config fixture without an auth token",
    target_fixture="github_sim_config",
)
def given_config_without_auth_token() -> GitHubSimConfig:
    """Return configuration without auth metadata."""
    return typ.cast("GitHubSimConfig", {})


@given(
    "a github_sim_config fixture with malformed auth metadata",
    target_fixture="github_sim_config",
)
def given_config_with_malformed_auth_metadata() -> GitHubSimConfig:
    """Return configuration with malformed simulacat auth metadata."""
    return typ.cast(
        "GitHubSimConfig",
        {
            "__simulacat__": "not-a-mapping",
        },
    )


@when("the github_simulator fixture is requested")
def when_github_simulator_requested(
    github_simulator: object,
    client_context: ClientContext,
) -> None:
    """Store the github_simulator fixture value for later assertions."""
    client_context["client"] = github_simulator


def _resolve_authorization_header(client: object) -> str | None:
    """Resolve the Authorization header value from a github3 client."""
    session = getattr(client, "session", None) or getattr(client, "_session", None)
    headers = getattr(session, "headers", None)
    if isinstance(headers, cabc.Mapping):
        return typ.cast("str | None", headers.get("Authorization"))

    msg = "Unable to resolve Authorization header from github3 client"
    raise AssertionError(msg)


@then('the github3 client Authorization header is "token test-token"')
def then_authorization_header_present(client_context: ClientContext) -> None:
    """Assert that the Authorization header is set."""
    client = client_context["client"]
    assert client is not None, "Expected github3 client to be stored in context"
    assert _resolve_authorization_header(client) == "token test-token", (
        "Expected Authorization header to be set to test-token"
    )


@then("the github3 client Authorization header is absent")
def then_authorization_header_absent(client_context: ClientContext) -> None:
    """Assert that the Authorization header is not set."""
    client = client_context["client"]
    assert client is not None, "Expected github3 client to be stored in context"
    assert _resolve_authorization_header(client) is None, (
        "Expected Authorization header to be absent"
    )


@then("requesting the github_simulator fixture raises a TypeError")
def then_github_simulator_raises_type_error(
    request: pytest.FixtureRequest,
) -> None:
    """Assert that constructing github_simulator fails with a TypeError."""
    with pytest.raises(TypeError):
        request.getfixturevalue("github_simulator")
