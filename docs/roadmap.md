# simulacat roadmap

This document describes the development roadmap for `simulacat`, a library that
provides configurable GitHub API simulation for Python test suites using
Simulacrum and `github3.py`.

The roadmap is structured into:

- [ ] **Phases** – strategic milestones that change the overall capability of
      the library.
- [ ] **Steps** – coherent workstreams within each phase.
- [ ] #### Tasks – execution units with clear, verifiable outcomes.

No specific dates are associated with roadmap items. Items indicate intended
ordering and dependency, not calendar commitments.

______________________________________________________________________

## Phase 1 – Core simulation and pytest integration

Establish a reliable foundation for running tests against a local GitHub API
simulator with minimal user configuration.

### Step 1.1 – Simulator orchestration ✅

Provide a stable process boundary between Python tests and the Simulacrum
GitHub API simulator.

#### Tasks (Step 1.1)

- [x] Implement a Bun/TypeScript entry point (`src/github-sim-server.ts`) that:

  - reads a JSON configuration file,
  - initializes the GitHub simulator with that configuration,
  - listens on an operating system assigned port,
  - prints a single JSON “listening” event containing the port.

- [x] Add robust process management in Python (`simulacat/orchestration.py`):

  - start the Bun process with captured stdout and stderr,
  - parse the “listening” event and extract the port,
  - fail fast with a detailed error if the simulator does not start.

- [x] Verify that the simulator shuts down cleanly:

  - `terminate` on fixture teardown,
  - `kill` only when the process does not exit within a short timeout.

### Step 1.2 – pytest fixture and client binding ✅

Expose the simulator through a `github3.py` client with clear fixture
boundaries.

#### Tasks (Step 1.2)

- [x] Provide a `github_sim_config` fixture that:

  - returns a JSON-serializable mapping,
  - can be overridden at function, module, and package scopes.
- [x] Provide a `github_simulator` fixture that:

  - writes `github_sim_config` to a temporary JSON file,
  - starts the packaged Bun simulator and waits for the listening event,
  - constructs a `github3.GitHub` client pointing at the simulator base URL,
  - yields the client and guarantees simulator teardown.

- [x] Confirm compatibility with typical `github3.py` usage patterns:

  - repository listing and lookup,
  - issue and pull request retrieval where supported by the simulator.

______________________________________________________________________

## Phase 2 – Scenario modelling and ergonomics

Make it straightforward to describe realistic GitHub states and reuse them
across test suites.

### Step 2.1 – Configuration schema and helpers

Define a stable configuration surface that hides simulator internals from test
code.

#### Tasks (Step 2.1)

- [x] Design a Python-side configuration schema for common GitHub concepts:

  - users and organizations,
  - repositories, branches, and default branch metadata,
  - pull requests and issues where supported.

- [x] Implement helper functions or data classes that:

  - construct valid configuration objects from Python structures,
  - validate configuration before serialization with clear error messages.

- [x] Document the configuration model with examples:

  - “single repo, single user” smoke test,
  - “multiple repositories with public and private visibility”.

### Step 2.2 – Reusable scenarios and fixtures

Enable reuse of common GitHub layouts across tests without duplication.

#### Tasks (Step 2.2)

- [x] Introduce named “scenario” factories, for example:

  - `single_repo_scenario(owner, name=...)`,
  - `monorepo_with_apps_scenario(...)` (subject to simulator support).

- [x] Provide higher-level fixtures that build on `github_sim_config`, such as:

  - `simulacat_single_repo`,
  - `simulacat_empty_org`.

- [x] Ensure scenarios are composable:

  - merging multiple scenario fragments into a single configuration,
  - detecting and reporting conflicting definitions (for example, duplicate
    repository names under the same owner).

______________________________________________________________________

## Phase 3 – Ecosystem integration and advanced use cases

Support more advanced workflows and integration into real project pipelines.

### Step 3.1 – Authentication and GitHub App workflows

Model authentication flows beyond simple unauthenticated calls where the
simulator supports them.

#### Tasks (Step 3.1)

- [x] Add optional token support in client construction:

  - configure `Authorization` headers based on the current scenario,
  - model per-token permissions and visibility where available.
  - acceptance: `make check-fmt`, `make typecheck`, `make lint`, and
    `make test` succeed, including the new unit tests in
    `simulacat/unittests/test_auth_tokens.py` and behavioural scenarios in
    `tests/features/github_simulator_auth.feature`.

- [x] Provide configuration helpers for GitHub Apps or OAuth applications if
      the simulator exposes these:

  - app installation metadata,
  - per-installation access to repositories and organizations.

- [x] Document the limitations of each authentication mode compared with real
      GitHub:

  - consolidated "Authentication mode limitations" section in the users'
    guide with comparison tables for unauthenticated, token-based, and
    GitHub App modes,
  - design decisions recorded in `docs/simulacat-design.md`,
  - acceptance: `make check-fmt`, `make typecheck`, `make lint`, and
    `make test` succeed, including the new unit tests in
    `simulacat/unittests/test_auth_mode_limitations.py` and behavioural
    scenarios in `tests/features/auth_mode_limitations.feature`.

### Step 3.2 – Continuous Integration (CI) usage and reference examples

Demonstrate reliable use of `simulacat` in continuous integration environments.

#### Tasks (Step 3.2)

- [x] Supply minimal reference projects that:

  - use `simulacat` in a pytest suite,
  - run under a standard Python + Node.js toolchain in CI.
  - prerequisites:
    - environment requirements are documented and executable (see the
      "Document environment requirements" checklist item below),
    - reference suites include simulator lifecycle coverage by requesting the
      `github_simulator` fixture (startup + teardown contract).
  - measurable finish lines:
    - both `examples/reference-projects/basic-pytest` and
      `examples/reference-projects/authenticated-pytest` pass `pytest -v tests`
      in CI,
    - CI green on Python 3.13 + Node.js 22, with compatibility documented for
      Python 3.12-3.13 and Node.js 20.x-22.x,
    - simulator-related modules (`simulacat/orchestration.py` and
      `simulacat/pytest_plugin.py`) maintain >=90% line coverage in CI,
    - at least one example workflow demonstrates simulator start/stop via
      `github_simulator` fixture execution.

- [x] Document environment requirements:

  - Node.js version range,
  - expected method for installing Simulacrum dependencies.
  - prerequisites:
    - reference project installation commands are finalized and validated in CI
      logs.
  - measurable finish lines:
    - exact runtime versions are documented: Python 3.12-3.13, Node.js
      20.x-22.x, and Bun runtime available on PATH,
    - verified CI execution target is documented: Linux (`ubuntu-latest`,
      x86_64),
    - install method is listed as concrete steps with commands (for example:
      `python -m pip install ...` then
      `python -m simulacat.install_simulator_deps`).

- [x] Provide troubleshooting guidance with concrete failure signatures:

  - simulator startup failures,
  - configuration serialization errors,
  - mismatches between `github3.py` calls and simulator coverage.
  - prerequisites:
    - complete environment setup first (see "Document environment
      requirements"),
    - run the reference project suites first (see "Supply minimal reference
      projects") before classifying failures as troubleshooting items.
  - measurable finish lines:
    - troubleshooting docs include exact signatures for startup failures (for
      example `GitHubSimProcessError: Bun executable not found` and simulator
      listening-event startup failures),
    - serialization guidance includes exact errors (for example
      `TypeError: github_sim_config must be a mapping` and JSON serialization
      type errors),
    - coverage-mismatch guidance includes
      `github3.exceptions.IncompleteResponse`
      and a startup latency threshold (`>30s` treated as startup failure),
    - uncovered `github3.py` compatibility-call rate is tracked with a target
      of <=10% uncovered calls in the documented reference suite.

______________________________________________________________________

## Phase 4 – Hardening and compatibility

Increase confidence in `simulacat` as a long-term dependency.

### Step 4.1 – Compatibility test matrix

Ensure the library remains stable across supported dependency versions.

#### Tasks (Step 4.1)

- [x] Define a minimum-to-recommended version range for:

  - Python,
  - `github3.py`,
  - Node.js,
  - `@simulacrum/github-api-simulator`.

- [x] Add a test matrix that runs the reference suites across:

  - multiple Python versions,
  - at least two `github3.py` major versions where relevant.

- [x] Track and document known incompatibilities and workarounds.

### Step 4.2 – API stability and deprecation policy

Provide a predictable public surface for downstream users.

#### Tasks (Step 4.2)

- [ ] Mark public modules, fixtures, and configuration helpers as part of the
      supported API.
- [ ] Document the deprecation process for any API changes:

  - introduce new APIs alongside old ones,
  - emit warnings with clear migration guidance,
  - remove deprecated APIs only after a documented transition period.

- [ ] Maintain a short changelog that links roadmap items to released
      capabilities and describes behavioural changes at the level of phases and
      steps.
