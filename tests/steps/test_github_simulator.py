"""Step definitions for github_simulator behavioural tests.

These steps validate the consumer-facing behaviour of the github_simulator
fixture, including starting a simulator process and exposing a github3.py
client that can reach it.

Feature files
-------------
The step definitions bind to scenarios in:
- tests/features/github_simulator.feature

Running tests
-------------
Execute behavioural tests with::

    pytest tests/steps/test_github_simulator.py -v

Or run all tests via make::

    make test

"""

from __future__ import annotations

import typing as typ
from urllib.parse import urlparse

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests import conftest as test_conftest

pytestmark = test_conftest.bun_required

if typ.TYPE_CHECKING:
    from simulacat.types import GitHubSimConfig


scenarios("../features/github_simulator.feature")


class ClientContext(typ.TypedDict):
    """Scenario context for github_simulator steps."""

    client: object | None
    base_url: str | None


@pytest.fixture
def client_context() -> ClientContext:
    """Provide scenario context for github_simulator steps."""
    return {"client": None, "base_url": None}


def _resolve_base_url(client: object) -> str:
    """Best-effort extraction of the configured API URL from github3.py clients."""
    # Targets github3.py 4.x clients (`github3.GitHub` / `github3.GitHubEnterprise`)
    # which may expose the base URL via different attributes across client/session.
    candidates: list[object] = [
        getattr(client, attr, None) for attr in ("base_url", "url")
    ]

    session = getattr(client, "session", None)
    if session is not None:
        candidates.extend(
            getattr(session, attr, None)
            for attr in ("base_url", "_base_url", "api_url", "_api_url")
        )

    build_url = getattr(client, "_build_url", None)
    if callable(build_url):
        candidates.append(build_url(""))

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
            return candidate.rstrip("/")

    msg = f"Unable to resolve base URL from github3 client of type {type(client)}"
    raise AssertionError(msg)


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


@when("the github_simulator fixture is requested")
def when_fixture_requested(
    client_context: ClientContext,
    github_simulator: object,
) -> None:
    """Store the github_simulator fixture value for later assertions."""
    client_context["client"] = github_simulator
    client_context["base_url"] = _resolve_base_url(github_simulator)


@then("the github3 client is bound to the simulator")
def then_client_bound_to_simulator(client_context: ClientContext) -> None:
    """Assert that the client is configured to talk to the local simulator."""
    base_url = client_context["base_url"]
    assert base_url is not None, "Expected base_url to be resolved"

    parsed = urlparse(base_url)
    assert parsed.hostname in {"127.0.0.1", "localhost"}, (
        f"Expected local simulator host, got {parsed.hostname!r} ({base_url})"
    )
    assert parsed.port is not None, f"Expected simulator port in URL: {base_url}"


@then("the simulator responds to an HTTP request")
def then_simulator_responds(client_context: ClientContext) -> None:
    """Assert that github3 can perform a request against the simulator."""
    client = client_context["client"]
    assert client is not None, "Expected client to be stored in context"
    rate_limit = getattr(client, "rate_limit", None)
    assert callable(rate_limit), "Expected github3 client to expose rate_limit()"

    payload = rate_limit()
    assert isinstance(payload, dict), f"Expected dict payload, got {type(payload)}"
    assert "rate" in payload, "Expected rate_limit payload to include 'rate'"
