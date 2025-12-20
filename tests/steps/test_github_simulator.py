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

    client: GitHubClient | None
    base_url: str | None


class GitHubClient(typ.Protocol):
    """Protocol for the subset of github3.GitHub used in behavioural tests."""

    def issue(self, owner: str, repository: str, number: int) -> object:
        """Return a single issue by number."""

    def organization(self, login: str) -> object:
        """Return an organization object by login."""

    def pull_request(self, owner: str, repository: str, number: int) -> object:
        """Return a single pull request by number."""

    def rate_limit(self) -> dict[str, object]:
        """Return the rate limit payload."""

    def repositories_by(self, username: str) -> typ.Iterable[object]:
        """Iterate over repositories owned by a user/org."""

    def repository(self, owner: str, repository: str) -> object:
        """Return a repository by owner/name."""


class OrganizationClient(typ.Protocol):
    """Protocol for the subset of github3 Organization used in behavioural tests."""

    def repositories(self) -> typ.Iterable[object]:
        """Iterate over repositories in this organization."""


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


@given(
    "a github_sim_config fixture with a user and repositories",
    target_fixture="github_sim_config",
)
def given_fixture_with_repos() -> GitHubSimConfig:
    """Return a configuration containing users, orgs, and repositories."""
    return {
        "users": [{"login": "alice", "organizations": ["acme"]}],
        "organizations": [{"login": "acme"}],
        "repositories": [
            {"owner": "alice", "name": "repo1"},
            {"owner": "acme", "name": "orgrepo"},
        ],
    }


def _repo_full_name(repo: object) -> str:
    """Best-effort extraction of an owner/name full_name from github3 repos."""
    full_name = getattr(repo, "full_name", None)
    if isinstance(full_name, str):
        return full_name

    owner = getattr(repo, "owner", None)
    owner_login = getattr(owner, "login", owner) if owner is not None else None
    name = getattr(repo, "name", None)
    if isinstance(owner_login, str) and isinstance(name, str):
        return f"{owner_login}/{name}"

    msg = f"Unable to resolve repository full_name from github3 repo {repo!r}"
    raise AssertionError(msg)


def _require_github3_client(client_context: ClientContext) -> GitHubClient:
    """Return the stored github3 client or fail with a clear assertion."""
    client = client_context["client"]
    assert client is not None, "Expected github3 client to be stored in context"
    return client


@then(parsers.parse('the github3 client can look up repository "{full_name}"'))
def then_repo_lookup_works(client_context: ClientContext, full_name: str) -> None:
    """Assert that github3 repository lookup works against the simulator."""
    client = _require_github3_client(client_context)
    owner, name = full_name.split("/", 1)

    repo = client.repository(owner, name)
    assert _repo_full_name(repo) == full_name


@then(parsers.parse('the github3 client can list repositories for user "{login}"'))
def then_user_repo_listing_works(client_context: ClientContext, login: str) -> None:
    """Assert that github3 can list repositories for a user."""
    client = _require_github3_client(client_context)
    repos = list(client.repositories_by(login))
    assert repos, f"Expected at least one repository listed for user {login!r}"


@then(
    parsers.parse('the github3 client can list repositories for organization "{login}"')
)
def then_org_repo_listing_works(client_context: ClientContext, login: str) -> None:
    """Assert that github3 can list repositories for an organization."""
    client = _require_github3_client(client_context)
    org = typ.cast("OrganizationClient", client.organization(login))
    repos = list(org.repositories())
    assert repos, f"Expected at least one repository listed for org {login!r}"


@then(parsers.parse('the repository listing includes "{full_name}"'))
def then_listing_contains_repo(client_context: ClientContext, full_name: str) -> None:
    """Assert that either user or org repo listing includes the target repository."""
    client = _require_github3_client(client_context)
    owner, _name = full_name.split("/", 1)

    full_names: set[str] = set()
    full_names.update(_repo_full_name(repo) for repo in client.repositories_by(owner))

    if not full_names:
        org = typ.cast("OrganizationClient", client.organization(owner))
        full_names.update(_repo_full_name(repo) for repo in org.repositories())

    assert full_name in full_names, f"Expected {full_name!r} in {sorted(full_names)!r}"


@then(
    parsers.parse('the github3 client can retrieve issue {number:d} for "{full_name}"')
)
def then_issue_retrieval_works(
    client_context: ClientContext,
    number: int,
    full_name: str,
) -> None:
    """Assert that github3 Issue retrieval works and includes rich body fields."""
    client = _require_github3_client(client_context)
    owner, name = full_name.split("/", 1)
    issue = client.issue(owner, name, number)
    assert getattr(issue, "number", None) == number
    assert isinstance(getattr(issue, "body_html", None), str)
    assert isinstance(getattr(issue, "body_text", None), str)


@then(
    parsers.parse(
        'the github3 client can retrieve pull request {number:d} for "{full_name}"'
    )
)
def then_pull_request_retrieval_works(
    client_context: ClientContext,
    number: int,
    full_name: str,
) -> None:
    """Assert that github3 PullRequest retrieval works and includes rich body fields."""
    client = _require_github3_client(client_context)
    owner, name = full_name.split("/", 1)
    pr = client.pull_request(owner, name, number)
    assert getattr(pr, "number", None) == number
    assert isinstance(getattr(pr, "body_html", None), str)
    assert isinstance(getattr(pr, "body_text", None), str)


@when("the github_simulator fixture is requested")
def when_fixture_requested(
    client_context: ClientContext,
    github_simulator: GitHubClient,
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
    client = _require_github3_client(client_context)
    payload = client.rate_limit()
    assert isinstance(payload, dict), f"Expected dict payload, got {type(payload)}"
    assert "rate" in payload, "Expected rate_limit payload to include 'rate'"
