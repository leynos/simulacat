# GitHub API simulator pytest fixture

This document describes a pytest fixture that uses the
`@simulacrum/github-api-simulator` package and the `github3.py` client library
to provide configurable mocking of the GitHub API.

The design has three main goals:

- start a Simulacrum GitHub API simulator on a random local TCP port,
- configure the simulator from Python via a JSON configuration object,
- expose a `github3.GitHub` instance that talks to the simulator and is
  cleaned up after the test.

## Overview

The solution consists of the following pieces:

- a Node.js entrypoint (`github-sim-server.mjs`) that starts the Simulacrum
  GitHub API simulator and prints the bound port as JSON on standard output,
- a pytest fixture pair:
  - `github_sim_config` for declaring the simulator configuration as a
    Python mapping that can be serialised to JSON,
  - `github_simulator` for starting the Node.js process, constructing a
    `github3.py` client bound to the simulator, and tearing everything down,
- helper functions that:
  - locate the Node.js entrypoint,
  - start and stop the simulator process,
  - construct a `github3.GitHub` instance targeting a custom base URL.

This document focuses on the orchestration pattern. The exact configuration
shape expected by the simulator will depend on the version of
`@simulacrum/github-api-simulator` in use.

## Node entrypoint

The Node.js entrypoint is responsible for:

- reading the simulator configuration from a JSON file path passed on the
  command line,
- instantiating the Simulacrum GitHub API simulator with that configuration,
- listening on an operating system assigned random port,
- printing a single JSON line when listening, so that the Python side can
  discover the port,
- shutting down cleanly on process signals.

Create `tests/github_sim/github-sim-server.mjs`:

```js
// tests/github_sim/github-sim-server.mjs
import { readFile } from 'node:fs/promises';
import process from 'node:process';
import { simulation } from '@simulacrum/github-api-simulator';

/**
 * Entry point:
 *
 *   node github-sim-server.mjs <config.json>
 *
 * Behaviour:
 *   - Reads JSON from <config.json>.
 *   - Passes it to the simulator as its initial configuration.
 *   - Listens on an OS-assigned random port.
 *   - Prints a single JSON line to stdout when ready:
 *         {"event":"listening","port":12345}
 *   - Shuts down cleanly on SIGINT/SIGTERM.
 */
async function main() {
  const [, , configPath] = process.argv;

  if (!configPath) {
    console.error('Usage: node github-sim-server.mjs <config.json>');
    process.exit(1);
  }

  let config = {};
  try {
    const raw = await readFile(configPath, 'utf8');
    config = JSON.parse(raw);
  } catch (err) {
    console.error('Failed to read or parse config JSON:', err);
    process.exit(1);
  }

  // The simulator is assumed to accept an options or initialState object.
  const app = simulation(config);

  const server = app.listen(0, () => {
    const address = server.address();
    const port =
      typeof address === 'object' && address && 'port' in address
        ? address.port
        : null;

    if (!port) {
      console.error('Server reported no port from server.address()');
      process.exit(1);
    }

    process.stdout.write(
      JSON.stringify({ event: 'listening', port }) + '\n',
    );
  });

  const shutdown = (signal) => {
    server.close(() => process.exit(0));
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));
}

main().catch((err) => {
  console.error('Uncaught error in simulator entrypoint:', err);
  process.exit(1);
});
```

### Assumptions

This entrypoint assumes the following:

- `@simulacrum/github-api-simulator` exports a `simulation()` function that
  returns an Express-style application with a `listen()` method,
- `simulation(config)` accepts an object that describes the initial state or
  configuration for the simulated GitHub API,
- the simulator exposes GitHub-like REST endpoints at the root path. If your
  simulator serves endpoints under a prefix such as `/api/v3`, you will need
  to reflect that when configuring the Python client.

You must ensure the appropriate version of Node.js is installed and that
`@simulacrum/github-api-simulator` is available in `node_modules`.

## Python orchestration and pytest fixtures

On the Python side, the design provides:

- a configuration fixture (`github_sim_config`) that returns a JSON-
  serialisable mapping describing the simulated GitHub state,
- a main fixture (`github_simulator`) that:
  - writes the configuration to a temporary JSON file,
  - starts the Node.js simulator process,
  - waits for a `{"event":"listening", ...}` JSON line on standard output,
  - constructs a `github3.GitHub` client bound to the simulator base URL,
  - yields the client to the test,
  - terminates the simulator process when the test completes.

### `conftest.py`

The following example `conftest.py` implements the fixtures and helpers.

```python
# tests/conftest.py
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping, Tuple

import github3
import pytest


# JSON-serialisable mapping passed to the JS entry point.
GitHubSimConfig = Mapping[str, Any]


@pytest.fixture
def github_sim_config() -> GitHubSimConfig:
    """Return the default configuration for the GitHub simulator.

    Override this fixture in tests or per module to describe the initial state
    that the simulator should expose.

    The shape of this mapping must match what the simulator expects as its
    configuration or initial state.
    """

    return {}


def _sim_entrypoint() -> Path:
    """Resolve the path to the Node.js simulator entry point.

    Adjust this helper if you place the entry point elsewhere.
    """

    here = Path(__file__).resolve().parent
    return here / "github_sim" / "github-sim-server.mjs"


class GitHubSimProcessError(RuntimeError):
    """Exception raised when the simulator process fails to start."""


def _start_sim_process(
    config: GitHubSimConfig,
    tmpdir: Path,
    node_executable: str | None = None,
    startup_timeout: float = 30.0,
) -> Tuple[subprocess.Popen[str], int]:
    """Start the Node.js simulator and return the process and port.

    The function writes the configuration to a JSON file, starts the
    simulator, and waits for a listening event. It raises
    :class:`GitHubSimProcessError` if the simulator fails to report a port
    within the timeout.
    """

    node_executable = node_executable or os.environ.get("NODE", "node")
    entrypoint = _sim_entrypoint()
    if not entrypoint.is_file():
        raise GitHubSimProcessError(
            f"GitHub simulator entry point not found at {entrypoint}",
        )

    cfg_path = tmpdir / "github-sim-config.json"
    with cfg_path.open("w", encoding="utf-8") as f:
        json.dump(config, f)

    proc = subprocess.Popen(
        [node_executable, str(entrypoint), str(cfg_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if proc.stdout is None:
        raise GitHubSimProcessError("Failed to capture simulator stdout")

    port: int | None = None
    output_lines: list[str] = []
    deadline = time.time() + startup_timeout

    while time.time() < deadline:
        line = proc.stdout.readline()
        if line == "":
            if proc.poll() is not None:
                break
            time.sleep(0.05)
            continue

        output_lines.append(line)

        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(evt, dict) and evt.get("event") == "listening":
            try:
                port = int(evt["port"])
            except (KeyError, TypeError, ValueError) as exc:
                raise GitHubSimProcessError(
                    f"Invalid listening event from simulator: {evt!r}",
                ) from exc
            break

    if port is None:
        try:
            remaining = proc.communicate(timeout=1)[0]
            if remaining:
                output_lines.append(remaining)
        except Exception:
            pass

        try:
            proc.terminate()
        except Exception:
            pass

        raise GitHubSimProcessError(
            "GitHub simulator did not report a listening port.\n"
            f"Exit code: {proc.poll()}\n"
            f"Output:\n{''.join(output_lines)}",
        )

    return proc, port


def _stop_sim_process(proc: subprocess.Popen[str], timeout: float = 5.0) -> None:
    """Terminate the simulator process if it is still running."""

    if proc.poll() is not None:
        return

    try:
        proc.terminate()
    except Exception:
        return

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass


def _make_github_client(base_url: str, token: str | None = None) -> github3.GitHub:
    """Construct a github3.GitHub client bound to a custom base URL.

    The helper mutates the underlying GitHub session's base_url, which is the
    mechanism used for GitHub Enterprise instances. If a token is supplied,
    the helper also sets an ``Authorization`` header.
    """

    gh = github3.GitHub()

    gh.session.base_url = base_url.rstrip("/")

    if token:
        gh.session.headers["Authorization"] = f"token {token}"

    return gh


@pytest.fixture
def github_simulator(
    tmp_path: Path,
    github_sim_config: GitHubSimConfig,
) -> Iterator[github3.GitHub]:
    """Yield a github3.py client bound to a Simulacrum GitHub API simulator.

    The fixture starts the Node.js simulator, waits for it to report its
    listening port, constructs a :class:`github3.GitHub` client whose base URL
    points at the simulator, and yields that client. The simulator process is
    terminated when the fixture scope ends.

    To customise the simulated GitHub state, override the
    :func:`github_sim_config` fixture in tests.
    """

    proc: subprocess.Popen[str] | None = None
    try:
        proc, port = _start_sim_process(github_sim_config, tmp_path)
        base_url = f"http://127.0.0.1:{port}"
        gh = _make_github_client(base_url)
        yield gh
    finally:
        if proc is not None:
            _stop_sim_process(proc)
```

If the simulator exposes its API under a path prefix, adjust the base URL
before constructing the client, for example:

```python
base_url = f"http://127.0.0.1:{port}/api/v3"
```

## Example test usage

The following example shows how to override the configuration fixture in a
single test module and consume the `github_simulator` fixture.

The structure of the configuration depends on the simulator's schema. The
example below illustrates the intent, but you must adapt it to the actual
configuration format that `@simulacrum/github-api-simulator` expects.

```python
# tests/test_list_repos.py
from __future__ import annotations

from typing import Any, Mapping

import pytest


GitHubSimConfig = Mapping[str, Any]


@pytest.fixture
def github_sim_config() -> GitHubSimConfig:
    """Return the initial simulator configuration for this test module."""

    return {
        "users": [
            {
                "login": "alice",
                "id": 1,
            },
        ],
        "repositories": [
            {
                "owner": "alice",
                "name": "demo-repo",
                "private": False,
                "default_branch": "main",
            },
        ],
    }


def test_repo_listing(github_simulator) -> None:
    """Repositories are listed from the simulator rather than api.github.com."""

    gh = github_simulator

    repos = list(gh.repositories())

    full_names = sorted(r.full_name for r in repos)
    assert full_names == ["alice/demo-repo"]
```

## Capabilities

This design provides the following capabilities.

- Per-test configuration of simulated GitHub state.

  Each test module, or individual test, can override `github_sim_config` to
  describe users, repositories, and other entities, subject to what the
  simulator supports.

- Real HTTP behaviour without accessing api.github.com.

  The tests exercise `github3.py` against a local HTTP server. This preserves
  request and response semantics, pagination behaviour, and error handling
  without depending on the live GitHub API.

- Random port allocation.

  The simulator binds to port `0` and receives a free port from the operating
  system. The Node.js entrypoint reports this port back to Python as a JSON
  event. Tests do not rely on a fixed port and avoid collisions.

- Clean process lifecycle.

  The fixture records the process handle, terminates the simulator on teardown,
  and escalates to `kill()` if the process does not exit within a short
  timeout. If startup fails, the fixture raises a `GitHubSimProcessError` that
  includes captured output from the simulator process.

- Extensible authentication.

  The `_make_github_client` helper supports optional token configuration via an
  `Authorization` header. This can be extended as needed to match how the
  simulator models authentication and authorisation.

## Limitations

The design has several limitations and assumptions.

- Simulator configuration schema.

  The document does not specify the exact JSON schema for
  `@simulacrum/github-api-simulator`. You must consult the simulator's
  documentation or TypeScript definitions and ensure that
  `github_sim_config` and `github-sim-server.mjs` provide configuration in the
  expected shape.

- Coverage of the GitHub API.

  The simulator is expected to implement only a subset of the GitHub REST API
  and authentication flows. Calls from `github3.py` to unimplemented endpoints
  will behave according to the simulator (for example, return `404` or `501`).

- github3.py targeting.

  The client construction relies on the ability to set
  `gh.session.base_url` to point at a custom API host. If you prefer
  alternative entry points such as `github3.login()` or `GitHubEnterprise`,
  you can wrap or adapt them, but the underlying requirement is that the
  session's base URL must target the simulator.

- Process overhead.

  The fixture starts a fresh Node.js process for each fixture scope. For large
  test suites this may be more expensive than desired. You can change the
  fixture scope to `session` or `module` and introduce simulator reset hooks
  if you want to reuse a single simulator instance across multiple tests.

These limitations do not affect the core pattern of serialising configuration
in Python, passing it into a Simulacrum-based simulator, and talking to that
simulator through a `github3.py` client bound to a random local port.

