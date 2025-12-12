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

- a Bun/TypeScript entrypoint (`src/github-sim-server.ts`) that starts the
  Simulacrum GitHub API simulator and prints the bound port as JSON on standard
  output,
- a Python orchestration module (`simulacat/orchestration.py`) that:
  - locates the Bun entrypoint,
  - starts and stops the simulator process,
  - waits for the listening event and extracts the port,
- pytest fixtures (planned for Step 1.2):
  - `github_sim_config` for declaring the simulator configuration as a Python
    mapping that can be serialized to JSON,
  - `github_simulator` for starting the process, constructing a `github3.py`
    client bound to the simulator, and tearing everything down.

This document focuses on the orchestration pattern. The exact configuration
shape expected by the simulator will depend on the version of
`@simulacrum/github-api-simulator` in use.

## Design decisions

### Step 1.1 – Simulator orchestration

The following decisions were made during implementation:

1. **Bun instead of Node.js**: The entrypoint uses Bun (`#!/usr/bin/env bun`)
   rather than Node.js for faster startup and native TypeScript support without
   a build step.

2. **TypeScript over JavaScript**: The entrypoint is written in TypeScript
   (`src/github-sim-server.ts`) for type safety and better IDE support.

3. **Simulator initial state schema**: The `@simulacrum/github-api-simulator`
   package (v0.6.2) requires a specific initial state structure with these
   required arrays:
   - `users`
   - `organizations`
   - `repositories`
   - `branches`
   - `blobs`

   The Python orchestration provides a minimal valid default when required
   arrays are missing from the configuration (including when an empty config is
   passed).

4. **Error event protocol**: The server emits JSON events for both success
   (`{"event":"listening","port":N}`) and error cases
   (`{"event":"error","message":"..."}`), allowing the Python side to
   distinguish startup failures from other issues.

5. **Process management**: The `start_sim_process` function wraps
   `FileNotFoundError` from subprocess into `GitHubSimProcessError` for
   consistent error handling.

6. **Wheel includes Bun sources**: The Python distribution bundles
   `src/github-sim-server.ts` along with `package.json` and `bun.lock` so
   `sim_entrypoint()` can resolve the simulator when installed from PyPI
   without requiring the repository checkout.

### Step 1.2 – pytest fixture and client binding

The following decisions were made during implementation:

1. **Expose fixtures via a pytest plugin**: Fixtures live in
   `simulacat.pytest_plugin` and are registered under the `pytest11` entry
   point. This makes them available to consumers without requiring
   `pytest_plugins` boilerplate.

2. **Function-scoped default fixture**: `github_sim_config` is function scoped
   to keep tests isolated. Consumers may override the fixture with narrower or
   broader scopes as required.

3. **Empty default configuration**: The fixture returns `{}` by default. The
   orchestration layer already expands empty configurations into the minimal
   valid simulator state.

4. **Indirect parametrization support**: The fixture accepts
   `request.param` when parametrized with `indirect=True`, enabling concise
   per-test configuration overrides.

5. **TypedDict schema for type safety**: A `GitHubSimConfig` `TypedDict`
   describes the top-level simulator keys while allowing partial
   configurations.

## Bun entrypoint

The Bun entrypoint is responsible for:

- reading the simulator configuration from a JSON file path passed on the
  command line,
- instantiating the Simulacrum GitHub API simulator with that configuration,
- listening on an operating system assigned random port,
- printing a single JSON line when listening, so that the Python side can
  discover the port,
- shutting down cleanly on process signals.

The entrypoint is located at `src/github-sim-server.ts`:

```typescript
#!/usr/bin/env bun
import { simulation } from "@simulacrum/github-api-simulator";
import { existsSync, readFileSync } from "node:fs";

// ... reads config, starts simulator, emits listening event
```

### Simulator API

The `@simulacrum/github-api-simulator` exports a `simulation()` function that:

- accepts an options object with an `initialState` property,
- returns a `FoundationSimulator` with an async `listen()` method,
- the `listen()` method returns a promise resolving to an object with `port`
  and `ensureClose()` for cleanup.

## Python orchestration

The Python orchestration module (`simulacat/orchestration.py`) provides:

- `GitHubSimProcessError` – exception raised when the simulator fails to start
- `sim_entrypoint()` – returns the path to the TypeScript entry point
- `start_sim_process()` – starts the simulator and waits for the listening
  event
- `stop_sim_process()` – terminates the simulator process gracefully

### Usage example

```python
from pathlib import Path
from simulacat.orchestration import start_sim_process, stop_sim_process

config = {
    "users": [{"login": "alice", "organizations": []}],
    "organizations": [],
    "repositories": [],
    "branches": [],
    "blobs": [],
}

proc, port = start_sim_process(config, Path("/tmp"))
try:
    # Use the simulator at http://127.0.0.1:{port}
    pass
finally:
    stop_sim_process(proc)
```

## Capabilities

This design provides the following capabilities.

- Random port allocation.

  The simulator binds to port `0` and receives a free port from the operating
  system. The Bun entrypoint reports this port back to Python as a JSON event.
  Tests do not rely on a fixed port and avoid collisions.

- Clean process lifecycle.

  The orchestration records the process handle, terminates the simulator on
  teardown, and escalates to `kill()` if the process does not exit within a
  short timeout. If startup fails, the orchestration raises a
  `GitHubSimProcessError` that includes captured output from the simulator
  process.

- Minimal default configuration.

  When an empty configuration is passed, the orchestration provides a minimal
  valid initial state with empty arrays for all required fields.

## Limitations

The design has several limitations and assumptions.

- Simulator configuration schema.

  The `@simulacrum/github-api-simulator` requires specific fields in the
  initial state. The Python side must provide a compatible configuration.

- Coverage of the GitHub API.

  The simulator implements only a subset of the GitHub REST API. Calls to
  unimplemented endpoints will behave according to the simulator (for example,
  return `404` or `501`).

- Process overhead.

  A fresh Bun process is started for each simulator instance. For large test
  suites this may be more expensive than desired. Future work may introduce
  simulator reset hooks for reuse.

These limitations do not affect the core pattern of serializing configuration
in Python, passing it into a Simulacrum-based simulator, and talking to that
simulator through a client bound to a random local port.
