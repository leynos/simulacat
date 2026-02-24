# Changelog

This changelog links roadmap phases and steps to released capabilities and
describes behavioural changes. Entries are ordered from newest to oldest.

______________________________________________________________________

## Phase 4 – hardening and compatibility

### Step 4.2 – API stability and deprecation policy

- Introduced `ApiStability` enum (`stable`, `provisional`, `deprecated`) and
  a `PUBLIC_API` registry mapping every public symbol and fixture to a
  stability tier.
- Added `SimulacatDeprecationWarning` subclass and `emit_deprecation_warning`
  helper for future deprecation communication.
- Established the deprecation lifecycle: introduce replacement alongside old
  API, emit warnings with migration guidance, remove only after a documented
  transition period.
- Added this changelog.

### Step 4.1 – compatibility test matrix

- Defined minimum-to-recommended version ranges for Python, `github3.py`,
  Node.js, and `@simulacrum/github-api-simulator` in
  `simulacat/compatibility_policy.py`.
- Added a dedicated continuous integration (CI) compatibility workflow
  (`.github/workflows/compatibility-matrix.yml`) running reference suites
  across Python 3.12/3.13 and `github3.py` major tracks 3.x/4.x.
- Documented known incompatibilities and workarounds for `github3.py >=5.0.0`
  and Python `<3.12`.

______________________________________________________________________

## Phase 3 – ecosystem integration and advanced use cases

### Step 3.2 – continuous integration (CI) usage and reference examples

- Shipped two reference projects (`basic-pytest` and `authenticated-pytest`)
  under `examples/reference-projects/`.
- Documented environment requirements, installation steps, and
  troubleshooting signatures for common CI failures.

### Step 3.1 – authentication and GitHub App workflows

- Added optional `AccessToken` support in client construction with
  `Authorization` header injection via the `github_simulator` fixture.
- Added `GitHubApp` and `AppInstallation` metadata models and the
  `github_app_scenario` factory.
- Documented authentication mode limitations across unauthenticated,
  token-based, and GitHub App installation modes.

______________________________________________________________________

## Phase 2 – scenario modelling and ergonomics

### Step 2.2 – reusable scenarios and fixtures

- Introduced named scenario factories (`single_repo_scenario`,
  `monorepo_with_apps_scenario`, `empty_org_scenario`) and the
  `merge_scenarios` composition helper.
- Added higher-level fixtures `simulacat_single_repo` and
  `simulacat_empty_org`.

### Step 2.1 – configuration schema and helpers

- Designed the scenario data-class schema (`User`, `Organization`,
  `Repository`, `Branch`, `DefaultBranch`, `Issue`, `PullRequest`,
  `ScenarioConfig`) with validation via `ConfigValidationError`.
- Added `merge_configs`, `is_json_serializable`, and
  `default_github_sim_config` configuration helpers.

______________________________________________________________________

## Phase 1 – core simulation and pytest integration

### Step 1.2 – pytest fixture and client binding

- Exposed the `github_sim_config` and `github_simulator` fixtures via the
  `pytest11` entry point, enabling zero-boilerplate simulator integration.
- Supported fixture override at function, module, and package scopes with
  indirect parametrization.

### Step 1.1 – simulator orchestration

- Implemented the Bun/TypeScript entry point (`src/github-sim-server.ts`) for
  starting the `@simulacrum/github-api-simulator` on a random port.
- Added Python process management (`simulacat/orchestration.py`) with
  `start_sim_process` and `stop_sim_process` for robust lifecycle control.
