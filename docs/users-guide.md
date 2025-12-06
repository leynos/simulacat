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
