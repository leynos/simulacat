# simulacat Users' Guide

simulacat provides a pytest integration for running tests against a local
GitHub API simulator powered by `@simulacrum/github-api-simulator`.

## Prerequisites

- Python 3.10 or later
- [Bun](https://bun.sh/) runtime installed and available in PATH
- Node.js dependencies installed (`bun install` in the installed package
  directory)

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

## pytest Fixtures

simulacat provides pytest fixtures for configuring the GitHub API simulator in
tests.

### github_sim_config

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

## Configuration Schema

The simulator requires a specific initial state structure. All top-level arrays
are required:

| Field           | Type  | Description                 |
| --------------- | ----- | --------------------------- |
| `users`         | array | GitHub user objects         |
| `organizations` | array | GitHub organization objects |
| `repositories`  | array | GitHub repository objects   |
| `branches`      | array | Git branch objects          |
| `blobs`         | array | Git blob objects            |

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
}
```

## Pytest fixtures

simulacat registers a pytest plugin that provides fixtures for configuring and
running the GitHub API simulator. The lowest-level fixture is
`github_sim_config`.

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
