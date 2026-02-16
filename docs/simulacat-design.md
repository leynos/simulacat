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
- pytest fixtures:
  - `github_sim_config` for declaring the simulator configuration as a Python
    mapping that can be serialized to JSON (Step 1.2),
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

The following decisions were made during implementation of the
`github_sim_config` fixture:

1. **Empty default configuration**: The `github_sim_config` fixture returns an
   empty dictionary by default. The orchestration layer expands this to a
   minimal valid simulator state when the simulator is started. This keeps the
   fixture simple while ensuring valid configuration at runtime.

2. **TypedDict for configuration**: A `GitHubSimConfig` TypedDict in
   `simulacat/types.py` describes the top-level simulator keys while allowing
   partial configurations. This allows consumers to annotate their override
   fixtures and helper functions with a consistent type that provides IDE
   support for known fields.

3. **JSON serializability validation**: The `is_json_serializable()` helper
   function allows tests to verify that configuration values can be passed to
   the simulator. This catches common mistakes like including `Path` objects or
   functions in configuration dictionaries.

4. **Configuration merging**: The `merge_configs()` helper supports layering
   configurations from package, module, and function scopes. Later
   configurations override earlier ones using shallow dictionary update
   semantics.

5. **Fixture override pattern**: The fixture is designed to be overridden at
   any pytest scope (function, module, or package) using standard pytest
   fixture mechanics. Users define their own `github_sim_config` fixture in
   their `conftest.py` or test module, and pytest's fixture resolution selects
   the most specific definition.

6. **No automatic registration as pytest plugin**: The fixture is defined in
   `simulacat/fixtures.py` and must be imported or the module must be
   registered in `conftest.py`. This avoids implicit behaviour and makes the
   dependency explicit. The following decisions were made during implementation:

7. **Expose fixtures via a pytest plugin**: Fixtures live in
   `simulacat.pytest_plugin` and are registered under the `pytest11` entry
   point. This makes them available to consumers without requiring
   `pytest_plugins` boilerplate.

8. **Function-scoped default fixture**: `github_sim_config` is function scoped
   to keep tests isolated. Consumers may override the fixture with narrower or
   broader scopes as required.

9. **Empty default configuration**: The fixture returns `{}` by default. The
   orchestration layer already expands empty configurations into the minimal
   valid simulator state.

10. **Indirect parametrization support**: The fixture accepts
   `request.param` when parametrized with `indirect=True`, enabling concise
   per-test configuration overrides.

11. **TypedDict schema for type safety**: A `GitHubSimConfig` `TypedDict`
   describes the top-level simulator keys while allowing partial configurations.

#### github_simulator fixture

The following decisions were made during implementation of the
`github_simulator` fixture:

1. **Use `github3.GitHub` with a custom session**: The Simulacrum simulator
   serves the REST API at the server root (for example, `/rate_limit`) rather
   than the GitHub Enterprise `/api/v3` prefix. The fixture constructs
   `github3.GitHub(session=GitHubSession(...))` and sets
   `GitHubSession.base_url` to the simulator base URL to ensure generated URLs
   match simulator routes.

2. **Skip on missing Bun**: If Bun cannot be located (based on the configured
   `BUN` environment variable or the `bun` executable on `PATH`), the fixture
   calls `pytest.skip()` with a clear message rather than failing with a
   subprocess error.

3. **Lifecycle managed via orchestration**: The fixture delegates startup and
   port discovery to `start_sim_process()` and always invokes
   `stop_sim_process()` in a `finally` block so teardown runs even if the test
   body fails.

4. **Compatibility is handled explicitly for common calls**: The Bun entrypoint
   extends the simulator's OpenAPI handlers for a small set of endpoints that
   `github3.py` exercises heavily:

   - repository lookup and listing,
   - issue and pull request retrieval.

   The handlers start from OpenAPI examples and patch response fields that
   `github3.py` expects when sending the `application/vnd.github.v3.full+json`
   accept header (for example, `language`, `body_html`, and `body_text`).

5. **OpenAPI response validation is avoided in these handlers**: The upstream
   GitHub OpenAPI schema includes constructs (notably `nullable`) that can
   trigger Ajv compilation errors when validating responses. The handlers write
   directly to the Express response and return `undefined` to avoid the
   validation hook and prevent connection resets on keep-alive sessions.

### Step 2.1 – Configuration schema and helpers

The following decisions were made during implementation of the scenario
configuration schema:

1. **Dataclass-based scenario schema**: A new scenario layer uses dataclasses
   (`User`, `Organization`, `Repository`, `Branch`, `DefaultBranch`, `Issue`,
   `PullRequest`, and `ScenarioConfig`) to provide a stable, Python-friendly
   surface that hides simulator internals from test code.

2. **Centralized validation with clear errors**: `ScenarioConfig.validate()`
   raises `ConfigValidationError` with explicit messages when owners,
   repositories, branches, or state values are inconsistent. This ensures
   invalid scenarios fail before JSON serialization.

3. **Default branch metadata propagation**: Repositories expose a
   `default_branch` field. When serialized, this metadata is emitted into both
   the repository object (`default_branch`) and the branch list, merging with
   explicit branches when present.

4. **Optional serialization for issues and pull requests**: Issues and pull
   requests are part of the scenario schema, but they are only included in the
   simulator configuration when `include_unsupported=True`, acknowledging that
   simulator support can vary by version.

### Step 2.2 – Reusable scenarios and fixtures

The following decisions were made during implementation of reusable scenario
factories and fixtures.

1. **Named scenario factories**: Common layouts live in
   `simulacat/scenario_factories.py` and are re-exported from
   `simulacat.scenario` to keep the public API consistent.

2. **Monorepo representation**: `monorepo_with_apps_scenario` models apps as
   branches under `apps/<name>` and sets the default branch to `main` because
   the simulator does not model directory structure.

3. **Scenario composition**: `merge_scenarios` merges fragments left to right,
   deduplicates identical entities by identity key, and raises
   `ConfigValidationError` when conflicting definitions are encountered.

4. **Higher-level fixtures**: `simulacat_single_repo` and `simulacat_empty_org`
   return simulator-ready mappings derived from the factories, so consumers can
   override `github_sim_config` without manual serialization.

### Step 3.1 – Authentication and GitHub App workflows

The following decisions were made during implementation of optional token
support.

1. **Access token modelling**: Access tokens are represented by the
   `AccessToken` dataclass on `ScenarioConfig`. Tokens capture the owner, token
   value, and optional metadata for permissions, repository visibility, and
   repository scoping.

2. **Header-only enforcement**: The simulator does not validate tokens or
   permissions, so tokens are not serialized into the simulator initial state.
   Instead, `github_simulator` reads token metadata and sets the
   `Authorization` header on the `github3.py` session to mimic authenticated
   requests.

3. **Explicit token selection**: When multiple tokens are configured,
   `ScenarioConfig.default_token` selects which token is applied for the client
   header. Attempting to resolve a token without a default selection raises
   `ConfigValidationError` to avoid ambiguous authentication.

#### Step 3.1.2 – GitHub App installation metadata

The following decisions were made during implementation of configuration
helpers for GitHub Apps.

1. **GitHub Apps only; OAuth applications are out of scope**: The simulator
   (v0.6.2) supports neither GitHub App nor OAuth endpoints. GitHub Apps with
   installations are the richer model, and OAuth apps are a simpler, distinct
   flow that can be added in a future step if needed.

2. **Metadata-only models**: `GitHubApp` and `AppInstallation` follow the
   `AccessToken` precedent from Step 3.1.1. They are not serialized into the
   simulator initial state because the simulator does not expose App
   endpoints. The `to_simulator_config()` method omits `apps` and
   `app_installations` from the output.

3. **Installation access token integration**: `AppInstallation` carries an
   optional `access_token` field. When set, the token is folded into the
   token resolution pool alongside `ScenarioConfig.tokens`. The existing
   `_select_auth_token_value()` logic applies: a single token auto-selects;
   multiple tokens require `default_token`. This design is a convenience
   alias and may need revisiting if the simulator adds support for
   per-request token switching or installation token exchange.

4. **Validation ordering**: App and installation validation runs after token
   validation and before branch validation. Installation validation depends
   on the app slug index, user/organization logins, and the repository
   index. The `default_token` validation is deferred to after installation
   validation so that installation access tokens are included in the
   candidate pool.

5. **Merge support**: `merge_scenarios` merges apps by `app_slug` and
   installations by `installation_id`, following the `_MergeSpec` pattern
   established in Step 2.2.

6. **Factory helper**: `github_app_scenario()` creates a scenario with a
   single `GitHubApp`, one `AppInstallation`, and the account user or
   organization. It returns a `ScenarioConfig` that can be merged with other
   scenarios.

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
  short timeout (5 seconds by default). If startup fails, the orchestration
  raises a `GitHubSimProcessError` that includes captured output from the
  simulator process.

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
