# Step 3.1 optional token support in client construction

This Execution Plan (ExecPlan) is a living document. The sections
"Constraints", "Tolerances", "Risks", "Progress", "Surprises & Discoveries",
"Decision Log", and "Outcomes & Retrospective" must be kept up to date as work
proceeds.

Status: COMPLETE

PLANS.md: not present in this repository.

## Purpose / big picture

Enable tests to model authenticated GitHub API access when the simulator
supports it. After this change, consumers can define access tokens and their
permissions in the scenario configuration, and the `github_simulator` fixture
will send the appropriate `Authorization` header based on the selected scenario
token. Success is observable when:

- a scenario that declares a token can be used to construct a client with an
  `Authorization` header set;
- per-token visibility or permission rules are honoured when the simulator
  exposes them (and limitations are documented if not supported);
- unit tests (pytest) and behavioural tests (pytest-bdd) cover the token
  selection and visibility logic;
- `make check-fmt`, `make typecheck`, `make lint`, and `make test` succeed;
- documentation and roadmap updates reflect the new behaviour.

## Constraints

- Follow the Python style rules in `.rules/python-*.md` and existing module
  conventions (frozen dataclasses, clear validation errors, tuple storage).
- Preserve backwards-compatible behaviour for existing public APIs in
  `simulacat.scenario`, `simulacat.config`, and pytest fixtures.
- Do not add new runtime dependencies.
- Keep documentation compliant with `docs/documentation-style-guide.md`
  (British spelling, 80-column wrap, sentence-case headings).
- Keep simulator orchestration behaviour unchanged unless explicitly required.
- Use pytest for unit tests and pytest-bdd for behavioural tests.
- If the simulator does not expose token or permission support, document the
  limitation rather than inventing server-side enforcement.

## Tolerances (exception triggers)

- Scope: if implementation requires changing more than 15 files or more than
  600 net lines of code, stop and escalate.
- Interfaces: if an existing public API signature must change or be removed,
  stop and escalate.
- Dependencies: if a new external dependency is required, stop and escalate.
- Iterations: if tests still fail after two full fix attempts, stop and
  escalate with the failing logs.
- Ambiguity: if the simulator documentation or code suggests multiple valid
  authentication models that materially affect outcomes, stop and present
  options with trade-offs.

## Risks

- Risk: the simulator may not support token-aware visibility checks.
  Severity: medium Likelihood: medium Mitigation: inspect the simulator schema
  and runtime behaviour, wire client headers only, and document limits
  explicitly in `docs/users-guide.md` and `docs/simulacat-design.md`.
- Risk: adding token metadata to `ScenarioConfig` may complicate validation.
  Severity: medium Likelihood: low Mitigation: keep token definitions minimal,
  validate identifiers and permissions with clear errors, and add unit tests
  for invalid scenarios.
- Risk: `github3.py` authentication APIs may require a specific header format.
  Severity: low Likelihood: medium Mitigation: confirm how `GitHubSession`
  expects token auth and test header output in unit tests.

## Progress

- [x] (2026-01-19 01:10Z) Draft ExecPlan for Step 3.1.1 optional token
  support.
- [x] (2026-01-19 01:20Z) Inspected simulator auth support and captured
  findings.
- [x] (2026-01-19 01:40Z) Added unit and behavioural tests; confirmed
  pre-implementation failures.
- [x] (2026-01-19 02:10Z) Implemented access token modelling and client header
  configuration.
- [x] (2026-01-19 02:30Z) Updated documentation, design notes, and roadmap.
- [x] (2026-01-19 02:45Z) Ran required quality gates and recorded results.

## Surprises & discoveries

- Observation: the simulator explicitly does not validate tokens or
  permissions. Evidence:
  `node_modules/@simulacrum/github-api-simulator/README.md` states tokens are
  accepted but not verified. Impact: token handling is client-side only;
  documentation calls out the limitation.

## Decision log

- Decision: model access tokens as `AccessToken` dataclasses on
  `ScenarioConfig`, with optional permissions and visibility metadata.
  Rationale: keeps token intent close to scenarios without coupling to the
  simulator schema. Date/Author: 2026-01-19, Codex.
- Decision: apply tokens by setting `Authorization: token <value>` on the
  `github3.py` session, and omit token data from simulator initial state.
  Rationale: the simulator does not enforce auth, so the header is sufficient
  for client behaviour while avoiding unsupported server config. Date/Author:
  2026-01-19, Codex.
- Decision: use `__simulacat__` metadata to carry auth tokens through
  `github_sim_config` mappings and strip it before launching the simulator.
  Rationale: preserves backwards compatibility while enabling optional
  authentication without server changes. Date/Author: 2026-01-19, Codex.

## Outcomes & retrospective

Delivered optional token support via scenario models and fixture headers,
backed by unit and behavioural tests. Documentation and design notes now
describe token metadata, selection rules, and the simulator's lack of token
enforcement. All required quality gates passed. If future simulator releases
add auth enforcement, the metadata model should be revisited to align with the
server schema.

## Context and orientation

Relevant modules and tests:

- `simulacat/pytest_plugin.py` defines the `github_simulator` fixture and
  constructs the `github3.GitHub` client.
- `simulacat/scenario_models.py` and `simulacat/scenario_config.py` define and
  validate scenario dataclasses and serialization.
- `simulacat/types.py` defines the `GitHubSimConfig` TypedDict for simulator
  configuration.
- `simulacat/scenario_factories.py` provides reusable scenario constructors.
- Unit tests live under `simulacat/unittests/` (notably
  `simulacat/unittests/test_github_simulator.py`).
- Behavioural tests use pytest-bdd in `tests/features/` and `tests/steps/`.
- Design decisions live in `docs/simulacat-design.md` and user-facing behaviour
  in `docs/users-guide.md`.

The new functionality is expected to live in Python modules only unless the
simulator requires a change to the Bun entrypoint. Any server-side auth logic
must be grounded in what `@simulacrum/github-api-simulator` actually supports.

## Plan of work

Stage A: understand and propose (no code changes).

Inspect the simulator package to determine whether it supports tokens, per
-token permissions, or visibility filters. Read any schema, types, or README
files in the installed `node_modules/@simulacrum/github-api-simulator` folder,
then inspect how it expects authentication data in `initialState`. Confirm how
`github3.py` expects token authentication to be configured on a `GitHubSession`
(for example, header format or helper methods). Summarise the findings in the
plan and decide the exact configuration shape to model in Python.

Validation: no code changes; produce a short summary of simulator support and
proposed token schema in `Decision Log`.

Stage B: scaffolding and tests (small, verifiable diffs).

Write unit tests before implementation that cover:

- scenario validation for token definitions (missing owner, invalid
  permissions, or invalid visibility rules should raise
  `ConfigValidationError`);
- token selection logic used by the `github_simulator` fixture (for example,
  when multiple tokens exist, the selected token controls the session
  `Authorization` header);
- compatibility with existing fixtures when no token is provided (header is
  absent and behaviour unchanged).

Write behavioural tests (pytest-bdd) that:

- start the simulator with a scenario including a token and verify the client
  sends the expected `Authorization` header (capture via monkeypatched
  `GitHubSession` or by reading the request headers from a controlled test
  endpoint if the simulator exposes them);
- verify visibility or permission differences when the simulator supports
  them (for example, accessing a private repository without a token yields a
  `404` or `403` and succeeds with the token). If simulator support is absent,
  the behavioural test should assert the documented limitation instead.

Validation: run targeted pytest for the new unit and BDD tests and confirm they
fail before implementation.

Stage C: implementation (minimal change to satisfy tests).

- Extend the scenario model to represent access tokens, owners, and permission
  scopes (add a dataclass in `simulacat/scenario_models.py` and include it in
  `ScenarioConfig`).
- Update `simulacat/scenario_config.py` to validate token ownership, scope
  values, and any visibility constraints supported by the simulator.
- Extend `simulacat/types.py` and serialization logic (likely in
  `ScenarioConfig.to_simulator_config`) to emit token data into the simulator
  configuration when supported.
- Update `simulacat/pytest_plugin.py` to configure the `github3.GitHub`
  session or headers with the selected token, based on the scenario or
  `github_sim_config` input, without breaking the unauthenticated default.
- If needed, add a small helper function to centralise token selection and
  header formatting (keep it internal and unit tested).

Validation: re-run the new unit and behavioural tests; they should now pass.

Stage D: hardening, documentation, cleanup.

- Update `docs/users-guide.md` with new token configuration examples and
  describe limitations (for example, when the simulator does not enforce
  per-token permissions).
- Record design decisions under Step 3.1 in `docs/simulacat-design.md`.
- Mark the Step 3.1 token task as done in `docs/roadmap.md` once all tests
  and quality gates pass.
- Run all required quality gates: `make check-fmt`, `make typecheck`,
  `make lint`, `make test`, plus `make markdownlint` and `make nixie` for the
  documentation changes.

## Concrete steps

1. Inspect simulator authentication support.

```shell
rg -n "token|auth|permission|visibility" \
  node_modules/@simulacrum/github-api-simulator
rg -n "auth|token" src/github-sim-server.ts simulacat
```

   Capture findings in the Decision Log (what fields are supported, expected
   shapes, and any limitations).

1. Add unit tests first.

```shell
touch simulacat/unittests/test_github_auth_tokens.py
```

   Populate tests for scenario validation and token selection for
   `github_simulator`. Run targeted tests and confirm failure before
   implementation:

```shell
pytest simulacat/unittests/test_github_auth_tokens.py -v
```

1. Add behavioural tests first.

```shell
touch tests/features/github_auth_tokens.feature
touch tests/steps/test_github_auth_tokens.py
pytest tests/steps/test_github_auth_tokens.py -v
```

   Confirm these fail before implementation.

1. Implement token-aware scenario configuration and client construction.

   Update scenario models, validation, serialization, and `github_simulator`
   logic. Re-run targeted tests until they pass.

2. Update documentation and roadmap.

   Edit:

   - `docs/users-guide.md`
   - `docs/simulacat-design.md`
   - `docs/roadmap.md`

3. Run quality gates (capture logs to avoid truncation).

```shell
set -o pipefail
make check-fmt | tee /tmp/simulacat-check-fmt.log
make typecheck | tee /tmp/simulacat-typecheck.log
make lint | tee /tmp/simulacat-lint.log
make test | tee /tmp/simulacat-test.log
MDLINT=/root/.bun/bin/markdownlint-cli2 \
  make markdownlint | tee /tmp/simulacat-markdownlint.log
make nixie | tee /tmp/simulacat-nixie.log
```

   Expected result: each command exits 0 and logs report success.

## Validation and acceptance

Acceptance is achieved when:

- Scenario configuration can include access tokens with defined scopes or
  visibility, and invalid definitions raise `ConfigValidationError`.
- The `github_simulator` fixture configures the `Authorization` header based
  on the active scenario token without affecting unauthenticated defaults.
- Behavioural tests demonstrate the header usage and, when supported,
  permission-based visibility differences.
- Unit tests and behavioural tests pass, with new tests failing before
  implementation and passing after.
- Quality gates succeed:
  - `make check-fmt`
  - `make typecheck`
  - `make lint`
  - `make test`
  - `make markdownlint`
  - `make nixie`

## Idempotence and recovery

The changes are additive and can be re-run safely. If a step fails, fix the
issue and re-run the same command. If documentation linting fails due to a
missing `markdownlint-cli2`, set `MDLINT=/root/.bun/bin/markdownlint-cli2` or
add `/root/.bun/bin` to `PATH`. Use `git status` to inspect and revert local
changes if a restart is required.

## Artifacts and notes

Example (expected to work after implementation):

```python
from simulacat import AccessToken, ScenarioConfig, User

scenario = ScenarioConfig(
    users=(User(login="octocat"),),
    tokens=(AccessToken(value="ghs_123", owner="octocat"),),
)

config = scenario.to_simulator_config()
```

Example fixture override with token selection:

```python
import pytest


@pytest.fixture
def github_sim_config(simulacat_single_repo, simulacat_token_config):
    return simulacat_token_config
```

## Interfaces and dependencies

If the simulator supports tokens, define an access token dataclass in
`simulacat/scenario_models.py` and add it to `ScenarioConfig` with a tuple
field. A tentative interface (subject to simulator capabilities):

```python
class AccessToken(dc.dataclass(frozen=True)):
    value: str
    owner: str
    permissions: tuple[str, ...] = ()
    repo_visibility: str | None = None

class ScenarioConfig:
    tokens: tuple[AccessToken, ...] = ()
```

Update `ScenarioConfig.to_simulator_config()` to serialise tokens into the
simulator config only when supported. If the simulator does not accept tokens,
keep the token data in the scenario model and use it only to configure the
client headers, documenting the limitation.

## Revision note

- 2026-01-19: initial ExecPlan draft for Step 3.1.1 optional token support.
- 2026-01-19: marked plan complete after implementation, documentation, and
  quality gates.
