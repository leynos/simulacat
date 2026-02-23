# simulacat Users' Guide

simulacat provides a pytest integration for running tests against a local
GitHub API simulator powered by `@simulacrum/github-api-simulator`.

## Prerequisites

- Python 3.12 or later
- Node.js 20.x or 22.x
- [Bun](https://bun.sh/) runtime installed and available in PATH
- Simulacrum dependencies installed with `bun install` in the directory that
  contains the simulacat `package.json` (see
  [Installing Simulacrum dependencies](#installing-simulacrum-dependencies))

## Installation

Install simulacat as a development dependency:

```bash
pip install simulacat
```

Or with uv:

```bash
uv add --group dev simulacat
```

## Bundled simulator assets

The published wheel ships the Bun entrypoint (`src/github-sim-server.ts`),
`package.json`, and `bun.lock`. The orchestration module resolves the
entrypoint from the installed package, so `start_sim_process` works after a
plain `pip install simulacat` without cloning the repository. Bun uses the
packaged manifest to install `@simulacrum/github-api-simulator` when the
simulator is started.

## Installing Simulacrum dependencies

Before running simulator-backed tests, install JavaScript dependencies in the
directory that contains the simulacat `package.json`:

```bash
python -m simulacat.install_simulator_deps
```

## Compatibility matrix

simulacat validates compatibility across the following dependency ranges. The
"recommended" column is the default target for CI and local development.

| Dependency                       | Minimum supported | Recommended | Supported range |
| -------------------------------- | ----------------- | ----------- | --------------- |
| Python                           | 3.12              | 3.13        | >=3.12,<3.14    |
| github3.py                       | 3.2.0             | 4.0.1       | >=3.2.0,<5.0.0  |
| Node.js                          | 20.x              | 22.x        | 20.x-22.x       |
| @simulacrum/github-api-simulator | 0.6.2             | 0.6.3       | >=0.6.2,<0.7.0  |

The compatibility workflow (`.github/workflows/compatibility-matrix.yml`) runs
reference suites across Python 3.12 and 3.13 with `github3.py` major tracks 3.x
and 4.x.

### Known incompatibilities and workarounds

- Dependency: `github3.py`
  Affected versions: `>=5.0.0,<6.0.0` Signature:
  `ERROR: Could not find a version that satisfies the requirement github3.py>=5.0.0,<6.0.0`
   Workaround: use `github3.py>=3.2.0,<5.0.0`.

- Dependency: Python
  Affected versions: `<3.12` Signature:
  `ERROR: Package 'simulacat' requires a different Python` Workaround: use
  Python 3.12 or 3.13.

## pytest Fixtures

simulacat provides pytest fixtures for configuring the GitHub API simulator in
tests.

### github_sim_config (advanced)

The `github_sim_config` fixture provides simulator configuration as a
JSON-serializable mapping. The fixture is automatically available via the
simulacat pytest plugin (registered as a `pytest11` entry point).

The default configuration is an empty dictionary. The orchestration layer
expands this to a minimal valid simulator state when the simulator starts.

#### Overriding at Module Scope

Override the fixture in a `conftest.py` file to provide shared configuration
for all tests in a module:

```python
# conftest.py
import pytest
from simulacat import GitHubSimConfig

@pytest.fixture
def github_sim_config() -> GitHubSimConfig:
    return {
        "users": [{"login": "testuser", "organizations": []}],
        "organizations": [],
        "repositories": [{"owner": "testuser", "name": "my-repo"}],
        "branches": [],
        "blobs": [],
    }
```

#### Overriding at Function Scope

Override in a specific test file or test function for fine-grained control:

```python
# test_feature.py
import pytest
from simulacat import GitHubSimConfig

@pytest.fixture
def github_sim_config() -> GitHubSimConfig:
    return {
        "users": [{"login": "feature-user", "organizations": ["my-org"]}],
        "organizations": [{"login": "my-org"}],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }

def test_with_custom_config(github_sim_config: GitHubSimConfig) -> None:
    assert github_sim_config["users"][0]["login"] == "feature-user"
```

### Helper Functions

#### is_json_serializable

Check whether a configuration value can be serialized to JSON:

```python
from simulacat import is_json_serializable

config = {"users": [{"login": "test"}]}
assert is_json_serializable(config)

from pathlib import Path
invalid = {"path": Path("/tmp")}
assert not is_json_serializable(invalid)
```

#### merge_configs

Merge multiple configuration mappings, with later values overriding earlier
ones:

```python
from simulacat import merge_configs

base = {"users": [{"login": "base"}], "organizations": []}
override = {"users": [{"login": "override"}]}

merged = merge_configs(base, override)
# Result: {"users": [{"login": "override"}], "organizations": []}
```

## Simulator Orchestration

The `simulacat.orchestration` module provides low-level control over the GitHub
API simulator process.

### Starting the Simulator

```python
from pathlib import Path
from simulacat.orchestration import start_sim_process, stop_sim_process

config = {
    "users": [{"login": "testuser", "organizations": []}],
    "organizations": [],
    "repositories": [
        {
            "owner": "testuser",
            "name": "my-repo",
        }
    ],
    "branches": [],
    "blobs": [],
}

proc, port = start_sim_process(config, Path("/tmp/sim-workdir"))
print(f"Simulator listening on port {port}")
```

### Stopping the Simulator

```python
stop_sim_process(proc)
```

By default, `stop_sim_process` waits up to 5 seconds for the process to exit
before sending `kill()`. You can adjust the timeout by passing `timeout=...`.

### Empty Configuration

When an empty dictionary is passed, simulacat provides a minimal valid
configuration:

```python
proc, port = start_sim_process({}, Path("/tmp/sim-workdir"))
```

### Error Handling

If the simulator fails to start, a `GitHubSimProcessError` is raised with
details about the failure:

```python
from simulacat.orchestration import GitHubSimProcessError

try:
    proc, port = start_sim_process(config, tmpdir)
except GitHubSimProcessError as e:
    print(f"Simulator failed: {e}")
```

### Custom Bun Executable

By default, the orchestration uses the `bun` command from PATH or the `BUN`
environment variable. Specify a custom path via the `bun_executable` parameter:

```python
proc, port = start_sim_process(
    config,
    tmpdir,
    bun_executable="/custom/path/to/bun",
)
```

## Scenario configuration helpers

For most tests, prefer the scenario configuration dataclasses. They provide a
stable, Python-friendly way to describe GitHub users, organizations,
repositories, branches, and optional issues or pull requests without relying on
the simulator's internal JSON structure.

To pass a scenario into the simulator, call `to_simulator_config()` and return
the resulting mapping from `github_sim_config`.

### Example: single repo, single user

```python
from simulacat import DefaultBranch, Repository, ScenarioConfig, User

scenario = ScenarioConfig(
    users=(User(login="alice"),),
    repositories=(
        Repository(
            owner="alice",
            name="rocket",
            default_branch=DefaultBranch(name="main"),
        ),
    ),
)

config = scenario.to_simulator_config()
```

### Example: multiple repositories with public and private visibility

```python
from simulacat import Repository, ScenarioConfig, User

scenario = ScenarioConfig(
    users=(User(login="alice"),),
    repositories=(
        Repository(owner="alice", name="public-repo"),
        Repository(owner="alice", name="private-repo", is_private=True),
    ),
)

config = scenario.to_simulator_config()
```

### Optional issues and pull requests

Issues and pull requests are modelled in the scenario schema, but they are only
serialized when requested because simulator support may vary. Pass
`include_unsupported=True` to include them in the serialized configuration.

```python
from simulacat import Issue, PullRequest, Repository, ScenarioConfig, User

scenario = ScenarioConfig(
    users=(User(login="alice"),),
    repositories=(Repository(owner="alice", name="rocket"),),
    issues=(Issue(owner="alice", repository="rocket", number=1, title="Bug"),),
    pull_requests=(
        PullRequest(
            owner="alice",
            repository="rocket",
            number=2,
            title="Fix",
        ),
    ),
)

config = scenario.to_simulator_config(include_unsupported=True)
```

### Named scenario factories

simulacat provides named scenario factories for common layouts. These live in
`simulacat.scenario` alongside the data classes:

- `single_repo_scenario(owner, name="repo", owner_is_org=False,
  default_branch="main")`
- `monorepo_with_apps_scenario(owner, repo="monorepo",
  apps=("app",), owner_is_org=False)`
- `empty_org_scenario(login)`
- `merge_scenarios(*scenarios)`

The monorepo factory represents apps as branches under `apps/<name>` because
the simulator does not model directories. The default branch is `main`.

```python
from simulacat import merge_scenarios, single_repo_scenario

base = single_repo_scenario("alice", name="alpha")
extra = single_repo_scenario("alice", name="beta")

scenario = merge_scenarios(base, extra)
config = scenario.to_simulator_config()
```

`merge_scenarios` deduplicates identical entities and raises
`ConfigValidationError` when definitions conflict (for example, two repository
definitions with the same owner and name but different visibility).

### Authentication tokens

simulacat can attach an `Authorization` header when a scenario defines access
tokens. Tokens are metadata only: the simulator does not validate token values
or enforce permissions, but the `github_simulator` fixture uses the selected
token to set the header, so clients behave as if authenticated.

Tokens are represented by `AccessToken` and stored on `ScenarioConfig` via the
`tokens` field. When more than one token is defined, `default_token` selects
the token value that should be applied automatically. `repository_visibility`
accepts `public`, `private`, or `all` to describe intended repository
visibility.

```python
import pytest

from simulacat import AccessToken, Repository, ScenarioConfig, User

scenario = ScenarioConfig(
    users=(User(login="octocat"),),
    repositories=(Repository(owner="octocat", name="demo"),),
    tokens=(
        AccessToken(
            value="ghs_test",
            owner="octocat",
            permissions=("repo",),
            repository_visibility="private",
            repositories=("octocat/demo",),
        ),
    ),
)

@pytest.fixture
def github_sim_config():
    return scenario
```

When the `github_simulator` fixture is requested, it sets
`Authorization: token ghs_test` on the underlying session.

Selecting a token without a `ScenarioConfig` requires metadata under
`__simulacat__` in the config mapping:

```python
@pytest.fixture
def github_sim_config():
    return {"__simulacat__": {"auth_token": "ghs_test"}}
```

For a full comparison of token-based authentication with real GitHub, see
[Authentication mode limitations](#authentication-mode-limitations).

### GitHub App installation metadata

simulacat can model GitHub App and installation metadata in scenarios. These
are client-side metadata only: the simulator does not expose GitHub App
endpoints or enforce installation-scoped permissions. The metadata documents
test intent and integrates with the token resolution flow.

Apps are represented by `GitHubApp` and installations by `AppInstallation`.
When an installation declares an `access_token`, it is folded into the token
resolution pool alongside standalone `AccessToken` values. The existing
`default_token` selection logic applies: a single token auto-selects; multiple
tokens require an explicit `default_token`.

```python
import pytest

from simulacat import (
    AppInstallation,
    GitHubApp,
    Repository,
    ScenarioConfig,
    User,
)

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
            access_token="ghs_installation_token",
        ),
    ),
)

@pytest.fixture
def github_sim_config():
    return scenario
```

The `github_app_scenario` factory creates a scenario with a single app and
installation:

```python
from simulacat import github_app_scenario, merge_scenarios, single_repo_scenario

app = github_app_scenario(
    "deploy-bot",
    "Deploy Bot",
    account="octocat",
    access_token="ghs_deploy",
)

repo = single_repo_scenario("octocat", name="hello-world")
combined = merge_scenarios(repo, app)
config = combined.to_simulator_config()
```

For a full comparison of GitHub App authentication with real GitHub, see
[Authentication mode limitations](#authentication-mode-limitations).

### Authentication mode limitations

The `@simulacrum/github-api-simulator` 0.6.x line does not validate tokens,
enforce permissions, or implement rate limiting. The following tables summarize
the differences between simulacat's authentication modes and real GitHub
behaviour. These limitations apply across all three modes.

#### Cross-cutting limitations

| Aspect                | Real GitHub                                         | simulacat               |
| --------------------- | --------------------------------------------------- | ----------------------- |
| Rate limiting         | 60 req/h unauthenticated, 5 000 req/h authenticated | No rate limiting        |
| Secondary rate limits | Concurrent request and content creation limits      | Not modelled            |
| Conditional requests  | ETag and Last-Modified support                      | Not implemented         |
| OAuth applications    | Full OAuth 2.0 flow                                 | Explicitly out of scope |
| Audit logging         | Authentication events logged                        | Not modelled            |
| SAML/SSO enforcement  | Organisation-level SSO requirements                 | Not modelled            |
| API versioning        | `X-GitHub-Api-Version` header                       | Not modelled            |

#### Unauthenticated mode

When no tokens are configured, the `github_simulator` fixture does not set an
`Authorization` header. The simulator responds to all implemented endpoints
regardless of authentication state.

| Aspect                    | Real GitHub                           | simulacat                                           |
| ------------------------- | ------------------------------------- | --------------------------------------------------- |
| Private repository access | Returns 404                           | No visibility enforcement; all repositories visible |
| Endpoint restrictions     | Some endpoints require authentication | All implemented endpoints respond                   |
| IP-based throttling       | Progressive throttling by IP          | No throttling                                       |

#### Token-based authentication (`AccessToken`)

When an `AccessToken` is configured, the `github_simulator` fixture sets
`Authorization: token <value>` on the `github3.py` session. The simulator
accepts the header but does not validate the token or enforce any scoping.

| Aspect                      | Real GitHub                                              | simulacat                                         |
| --------------------------- | -------------------------------------------------------- | ------------------------------------------------- |
| Token validation            | Tokens validated server-side; invalid tokens receive 401 | Any token value accepted; no validation           |
| Permission enforcement      | Token scopes limit endpoint access                       | `permissions` field is metadata only              |
| Token expiration            | Fine-grained PATs and OAuth tokens expire                | No expiration                                     |
| Token format validation     | Validates prefix format (`ghp_`, `gho_`, `ghs_`)         | No format validation                              |
| Token revocation            | Tokens can be revoked                                    | No revocation support                             |
| Repository visibility       | Token scoping controls visible repositories              | `repository_visibility` is metadata only          |
| Repository scoping          | Fine-grained PATs scope to specific repositories         | `repositories` field is metadata only             |
| Per-request token switching | One token per request                                    | One token per fixture session via `default_token` |
| Authorization header format | `Bearer <token>` or `token <token>`                      | Always `token <value>`                            |

#### GitHub App installation authentication

`GitHubApp` and `AppInstallation` models describe app metadata and
per-installation access. The simulator in the 0.6.x line does not expose GitHub
App endpoints. These models are client-side metadata only and are not
serialized into the simulator initial state.

| Aspect                           | Real GitHub                                   | simulacat                                            |
| -------------------------------- | --------------------------------------------- | ---------------------------------------------------- |
| App endpoints                    | `GET /app`, `GET /app/installations`          | No GitHub App endpoints available                    |
| Installation token exchange      | `POST /app/installations/{id}/access_tokens`  | No token exchange; `access_token` is a static string |
| JWT authentication               | App authenticates with a signed JWT           | No JWT support                                       |
| Installation-scoped permissions  | Per-installation permission enforcement       | `permissions` is metadata only                       |
| Installation-scoped repositories | Installation limited to selected repositories | `repositories` is metadata only                      |
| Webhook delivery                 | Installations receive webhooks                | No webhook delivery                                  |
| Token lifetime                   | Installation tokens expire after one hour     | No expiration                                        |
| Manifest flow                    | App creation via manifest                     | Not supported                                        |
| Suspension                       | Apps can be suspended                         | Not modelled                                         |
| Serialization                    | App data stored on GitHub servers             | Models excluded from simulator config                |

These limitations should be revisited if a future simulator release adds
authentication or GitHub App support.

## Configuration Schema

The simulator requires a specific initial state structure. The following
top-level arrays are required by the simulator:

| Field           | Type  | Description                 |
| --------------- | ----- | --------------------------- |
| `users`         | array | GitHub user objects         |
| `organizations` | array | GitHub organization objects |
| `repositories`  | array | GitHub repository objects   |
| `branches`      | array | Git branch objects          |
| `blobs`         | array | Git blob objects            |

Optional arrays, when supported by the simulator version in use:

| Field           | Type  | Description                 |
| --------------- | ----- | --------------------------- |
| `issues`        | array | GitHub issue objects        |
| `pull_requests` | array | GitHub pull request objects |

When starting the simulator with `start_sim_process`, simulacat fills any
missing required top-level arrays with empty lists. This allows callers to
provide partial configurations (for example, only `users`) without manually
including the other keys.

### User Schema

```python
{
    "login": "username",           # Required
    "organizations": ["org1"],     # Required, list of org logins
    "id": 1,                       # Optional, auto-generated
    "name": "Display Name",        # Optional
    "bio": "Profile bio",         # Optional
    "email": "user@example.com",   # Optional
}
```

### Repository Schema

```python
{
    "owner": "username",           # Required
    "name": "repo-name",           # Required
    "id": 1,                       # Optional, auto-generated
    "description": "About repo",   # Optional
    "private": False,              # Optional
    "default_branch": "main",      # Optional
}
```

### Branch Schema

```python
{
    "owner": "username",           # Required
    "repository": "repo-name",     # Required
    "name": "main",                # Required
    "sha": "abc123",               # Optional
    "protected": False,            # Optional
}
```

## Pytest fixtures

simulacat registers a pytest plugin that provides fixtures for configuring and
running the GitHub API simulator. The lowest-level fixture is
`github_sim_config`.

### Scenario fixtures

simulacat also provides higher-level fixtures that return ready-to-use
configuration mappings derived from the scenario factories:

- `simulacat_single_repo` (single repository owned by `octocat`)
- `simulacat_empty_org` (empty organization named `octo-org`)

Use these fixtures to override `github_sim_config` or to compose additional
configuration layers:

```python
import pytest

@pytest.fixture
def github_sim_config(simulacat_single_repo):
    return simulacat_single_repo
```

### github_sim_config

`github_sim_config` returns a JSON-serializable mapping describing the initial
simulator state. By default, it is an empty dictionary (`{}`); the
orchestration layer expands an empty config into the minimal valid state when
starting the simulator.

Override the fixture at different scopes using standard pytest rules:

- Function scope via indirect parametrization:

```python
import pytest


@pytest.mark.parametrize(
    "github_sim_config",
    [{"users": [{"login": "alice", "organizations": []}]}],
    indirect=True,
)
def test_uses_parametrized_config(github_sim_config):
    assert github_sim_config["users"][0]["login"] == "alice"
```

- Module scope by defining a fixture in a test module:

```python
import pytest


@pytest.fixture
def github_sim_config():
    return {"users": [{"login": "alice", "organizations": []}]}


def test_uses_module_override(github_sim_config):
    assert github_sim_config["users"][0]["login"] == "alice"
```

- Package scope by defining a fixture in `conftest.py`:

```python
# tests/conftest.py
import pytest


@pytest.fixture(scope="package")
def github_sim_config():
    return {"users": [{"login": "alice", "organizations": []}]}
```

### github_simulator

`github_simulator` starts the Bun-based GitHub API simulator using the current
`github_sim_config`, then yields a `github3.GitHub` client configured to send
requests to the local simulator.

```python
def test_rate_limit(github_simulator):
    payload = github_simulator.rate_limit()
    assert payload["rate"]["limit"] > 0
```

The simulator process is stopped after the test, even if the test fails.

simulacat patches simulator responses for common `github3.py` calls (repository
lookup and listing, issue retrieval, and pull request retrieval) so that rich
model objects can be constructed when the client sends the
`application/vnd.github.v3.full+json` accept header.

Other `github3.py` methods may still raise
`github3.exceptions.IncompleteResponse` if the simulator response is missing
fields that the client library expects. In those cases, prefer endpoints like
`rate_limit()` or use `github_simulator.session` to make raw HTTP requests.

## Environment Variables

| Variable | Description                | Default |
| -------- | -------------------------- | ------- |
| `BUN`    | Path to the Bun executable | `bun`   |

## Running tests

Use the Makefile target for the full Python + Bun suite:

```bash
make test
```

Pytest is configured with `addopts = "-m 'not slow'"`, so tests marked
`@pytest.mark.slow` (including `@pytest.mark.packaging`) are skipped by
default. Run the full set, including packaging checks, with:

```bash
pytest -m slow
```

## Continuous integration (CI) reference projects

Step 3.2 ships two minimal reference projects:

- `examples/reference-projects/basic-pytest`
- `examples/reference-projects/authenticated-pytest`

Both projects provide:

- a pytest smoke suite using simulacat fixtures,
- a GitHub Actions workflow at `.github/workflows/ci.yml`,
- standard CI setup via `actions/setup-python` and `actions/setup-node`.

The authenticated reference also demonstrates `ScenarioConfig` token metadata
and validates the resulting `Authorization` header.

## Troubleshooting

The following signatures cover common CI and local integration failures.

### Simulator startup failures

- Signature: `GitHubSimProcessError: Bun executable not found: ...`
  Cause: Bun is not installed or not visible on `PATH`. Fix: install Bun and,
  if needed, set the `BUN` environment variable to the executable path.
- Signature:
  `GitHubSimProcessError: Simulator exited before emitting listening event`
  Cause: Simulacrum dependencies were not installed where simulacat resolves
  `package.json`. Fix: run
  [Installing Simulacrum dependencies](#installing-simulacrum-dependencies)
  before starting tests.

### Configuration serialization errors

- Signature: `TypeError: github_sim_config must be a mapping`
  Cause: fixture returned a non-mapping value (for example, a string). Fix:
  return a dict-like value or `ScenarioConfig`.
- Signature: `TypeError: Object of type PosixPath is not JSON serializable`
  Cause: non-JSON values were included in `github_sim_config`. Fix: convert
  values to JSON-compatible primitives before returning fixture data.

### `github3.py` and simulator coverage mismatches

- Signature: `github3.exceptions.IncompleteResponse`
  Cause: selected endpoint response is missing fields expected by `github3.py`.
  Fix: use supported calls (for example, `repository`, `repositories_by`,
  `issue`, `pull_request`, and `rate_limit`) or use raw session requests.
- Signature: HTTP `404` / `501` from simulator-backed calls
  Cause: endpoint is not implemented by the simulator version in use. Fix:
  constrain tests to implemented endpoints or model behaviour at the
  configuration layer.

## API stability

simulacat classifies every public symbol and fixture into one of three
stability tiers. The canonical registry lives in
`simulacat.api_stability.PUBLIC_API`.

| Tier            | Meaning                                                                            | Consumer guidance                                                        |
| --------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **stable**      | Part of the supported API. Changes follow the deprecation lifecycle.               | Safe to depend on without pinning a specific patch version.              |
| **provisional** | May change without the full deprecation lifecycle.                                 | Pin your simulacat version if you depend on provisional symbols.         |
| **deprecated**  | Will be removed in a future version. Warnings are emitted with migration guidance. | Migrate to the documented replacement before the stated removal version. |

All symbols exported via `simulacat.__all__` and all fixtures registered
through the `pytest11` entry point (`github_sim_config`, `github_simulator`,
`simulacat_single_repo`, `simulacat_empty_org`) are currently classified as
**stable**.

You can inspect the stability tier of any symbol programmatically:

```python
from simulacat import PUBLIC_API

tier = PUBLIC_API["ScenarioConfig"]
print(tier)  # "stable"
```

## Deprecation policy

When a public API element needs to change, simulacat follows a three-phase
deprecation lifecycle:

1. **Introduce replacement alongside old API.** The new symbol or fixture is
   added and documented while the old one continues to work unchanged.

2. **Emit warnings with migration guidance.** The old symbol emits a
   `SimulacatDeprecationWarning` (a subclass of `DeprecationWarning`) that
   names the replacement and provides migration instructions. Consumers can
   filter these warnings independently:

   ```python
   import warnings
   from simulacat import SimulacatDeprecationWarning

   # Turn simulacat deprecation warnings into errors during CI.
   warnings.filterwarnings("error", category=SimulacatDeprecationWarning)
   ```

3. **Remove after a documented transition period.** The deprecated symbol is
   removed only after the transition period stated in the warning message. The
   removal version is recorded in `DEPRECATED_APIS` in
   `simulacat/api_stability.py` and announced in the [changelog](changelog.md).

No symbols are currently deprecated.

## Changelog

A changelog linking roadmap phases and steps to released capabilities is
maintained at [docs/changelog.md](changelog.md).
