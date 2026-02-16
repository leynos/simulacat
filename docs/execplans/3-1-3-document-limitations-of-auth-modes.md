# Step 3.1.3 document limitations of authentication modes

This Execution Plan (ExecPlan) is a living document. The sections
"Constraints", "Tolerances", "Risks", "Progress", "Surprises & Discoveries",
"Decision Log", and "Outcomes & Retrospective" must be kept up to date as work
proceeds.

Status: DONE

PLANS.md: not present in this repository.

## Purpose / big picture

Complete Step 3.1 by documenting the limitations of each authentication mode
compared with real GitHub behaviour. Steps 3.1.1 and 3.1.2 implemented
token-based authentication and GitHub App installation metadata helpers. Both
noted that the simulator (`@simulacrum/github-api-simulator` v0.6.2) does not
validate tokens, enforce permissions, or support GitHub App endpoints.
Scattered limitation notes exist in `docs/users-guide.md` and
`docs/simulacat-design.md`, but no consolidated reference section exists. This
task fills that gap and backs the documentation with executable tests.

No new Python models, validation logic, or fixture behaviour is required. This
is a documentation-and-test task.

Success is observable when:

- a consolidated "Authentication mode limitations" section exists in
  `docs/users-guide.md`, comparing unauthenticated, token-based, and GitHub App
  modes with real GitHub;
- design decisions are recorded in `docs/simulacat-design.md`;
- unit tests (pytest) verify limitation-related behaviour at the model and
  configuration layer;
- behavioural tests (pytest-bdd) demonstrate the documented limitations as
  executable scenarios;
- `make check-fmt`, `make typecheck`, `make lint`, and `make test` succeed;
- the roadmap entry at `docs/roadmap.md` line 152 is marked as done.

## Constraints

- Follow the Python style rules in `.rules/python-*.md` and existing module
  conventions (frozen dataclasses with slots, clear validation errors, tuple
  storage, `from __future__ import annotations`).
- Preserve backwards-compatible behaviour for all existing public APIs.
- Do not add new runtime dependencies.
- Keep documentation compliant with `docs/documentation-style-guide.md`
  (British English with Oxford spelling, 80-column wrap, sentence-case
  headings).
- Use pytest for unit tests and pytest-bdd for behavioural tests.
- Tests must verify existing behaviour (no new models or validation logic).
- BDD step texts must not collide with steps defined in other feature files.

## Tolerances (exception triggers)

- Scope: if implementation requires changing more than 15 files or more than
  600 net lines of code, stop and escalate.
- Interfaces: if an existing public API signature must change or be removed,
  stop and escalate.
- Dependencies: if a new external dependency is required, stop and escalate.
- Iterations: if tests still fail after two full fix attempts, stop and
  escalate with the failing logs.

## Risks

- Risk: Markdown linting may flag table formatting or line wrapping issues.
  Severity: low. Likelihood: medium. Mitigation: run `make fmt` after
  documentation changes and validate with `make markdownlint`.

- Risk: BDD step texts may collide with steps in other feature files.
  Severity: medium. Likelihood: low. Mitigation: use distinct wording in the
  new feature file; verify no registration conflicts.

- Risk: documentation may become stale if a future simulator version adds
  authentication features. Severity: medium. Likelihood: low. Mitigation: note
  the simulator version (v0.6.2) prominently; BDD tests will fail if behaviour
  changes, signalling that documentation needs updating.

## Progress

- [x] (2026-02-16) Draft ExecPlan for Step 3.1.3.
- [x] (2026-02-16) Write unit tests in
  `simulacat/unittests/test_auth_mode_limitations.py`.
- [x] (2026-02-16) Write BDD feature file and step definitions.
- [x] (2026-02-16) Add consolidated "Authentication mode limitations" section
  to `docs/users-guide.md`.
- [x] (2026-02-16) Add Step 3.1.3 design decisions to
  `docs/simulacat-design.md`.
- [x] (2026-02-16) Mark Step 3.1.3 as done in `docs/roadmap.md`.
- [x] (2026-02-16) Run quality gates and confirm all pass.

## Surprises & discoveries

- The `S106` (possible hardcoded password) ruff rule does not trigger on
  `AccessToken(value=...)` because the parameter is named `value`, not
  `password` or `token`. Removed unnecessary `noqa: S106` directives from
  `value` keyword arguments; kept them on `default_token` and `access_token`
  keyword arguments where the rule does trigger.

## Decision log

- Decision: consolidate limitation documentation into a single reference
  section in the users' guide rather than scattering notes across multiple
  sections. Rationale: a single section provides a definitive reference; inline
  notes remain for discoverability and cross-reference the consolidated
  section. Date/Author: 2026-02-16, ExecPlan author.

- Decision: BDD scenarios and unit tests verify existing behaviour rather
  than testing new functionality. Rationale: unlike Steps 3.1.1 and 3.1.2, this
  task documents limitations rather than adding features. Tests serve as
  executable documentation: if a future simulator version changes behaviour,
  the tests will fail and signal that documentation needs updating.
  Date/Author: 2026-02-16, ExecPlan author.

- Decision: all limitation documentation is explicit about
  `@simulacrum/github-api-simulator` v0.6.2. Rationale: makes it clear when
  documentation needs revision after a simulator upgrade. Date/Author:
  2026-02-16, ExecPlan author.

- Decision: OAuth applications remain out of scope, listed as a scope boundary
  rather than a limitation. Rationale: follows the Step 3.1.2 decision.
  Date/Author: 2026-02-16, ExecPlan author.

- Decision: BDD tests do not require a running simulator (no `bun_required`
  mark) because all limitations can be demonstrated at the model and
  configuration layer. Rationale: keeps tests fast and avoids CI environment
  dependency on Bun for documentation-oriented scenarios. Date/Author:
  2026-02-16, ExecPlan author.

## Outcomes & retrospective

Implementation complete. All acceptance criteria met:

- 6 unit tests and 5 BDD scenarios pass.
- All quality gates pass: `make check-fmt`, `make typecheck`, `make lint`,
  `make test`, `make markdownlint`, `make nixie`.
- 7 files created or modified, within the 15-file tolerance.
- No new runtime dependencies added.
- No existing public API signatures changed.
- Documentation updated in users' guide, design document, and roadmap.
- Consolidated "Authentication mode limitations" section covers
  unauthenticated, token-based, and GitHub App modes with comparison tables
  against real GitHub behaviour.

## Context and orientation

The simulacat project provides a pytest integration for running tests against a
local GitHub API simulator. The codebase lives at the repository root with the
following key layout:

- `simulacat/scenario_models.py` – frozen dataclasses for domain concepts
  (`User`, `Organization`, `Repository`, `Branch`, `AccessToken`, `Issue`,
  `PullRequest`, `GitHubApp`, `AppInstallation`).
- `simulacat/scenario_config.py` – `ScenarioConfig` container with
  `validate()`, `to_simulator_config()`, and `resolve_auth_token()`.
- `simulacat/scenario_factories.py` – named factory functions and
  `merge_scenarios`.
- `simulacat/pytest_plugin.py` – `github_sim_config`, `github_simulator`
  fixtures. Tokens flow through `__simulacat__` metadata key and are set on the
  `github3.py` session `Authorization` header.
- `simulacat/unittests/test_auth_tokens.py` – 24 unit tests for token
  validation and selection.
- `simulacat/unittests/test_github_app.py` – 35 unit tests for GitHub App
  models and validation.
- `tests/features/github_simulator_auth.feature` – BDD scenarios for auth
  header behaviour.
- `tests/features/github_app.feature` – BDD scenarios for GitHub App
  metadata.
- `tests/steps/test_github_simulator_auth.py` – BDD steps for auth headers.
- `tests/steps/test_github_app.py` – BDD steps for GitHub Apps.
- `docs/simulacat-design.md` – design decisions document.
- `docs/users-guide.md` – consumer-facing documentation.
- `docs/roadmap.md` – development roadmap.

Existing limitation notes:

- `docs/users-guide.md` lines 302–304: tokens are metadata only, simulator
  does not validate.
- `docs/users-guide.md` lines 418–422: `AppInstallation.repositories` and
  `permissions` document test intent only.
- `docs/simulacat-design.md` lines 227–231: header-only enforcement.
- `docs/simulacat-design.md` lines 248–252: metadata-only models.

## Plan of work

### Stage A: understand and propose (no code changes)

Review existing limitation notes, authentication implementation, and test
patterns. This stage is complete via exploration that produced this ExecPlan.

### Stage B: scaffolding and tests

Write tests before documentation. These tests verify existing behaviour and
should pass immediately (not fail-first, since no new code is being
implemented).

**Unit tests** in `simulacat/unittests/test_auth_mode_limitations.py`:

- `test_arbitrary_token_value_accepted` – proves `ScenarioConfig` accepts
  non-GitHub-formatted token values without format validation.
- `test_token_metadata_excluded_from_serialized_config` – creates a scenario
  with tokens bearing permissions, repository scoping, and visibility;
  serializes via `to_simulator_config()`; asserts no token data in output.
- `test_token_visibility_excluded_from_serialized_config` – verifies
  `repository_visibility` is absent from serialized output.
- `test_installation_access_token_is_literal_value` – creates an
  `AppInstallation` with `access_token`, resolves it, asserts the resolved
  value is the literal string (no exchange or refresh).
- `test_installation_permissions_are_metadata_only` – creates two
  installations with different permissions, validates both, and shows they
  resolve identically.
- `test_single_active_token_per_session` – creates a scenario with two tokens
  and `default_token`; asserts only one value is returned by
  `resolve_auth_token()`.

**BDD tests** in `tests/features/auth_mode_limitations.feature` and
`tests/steps/test_auth_mode_limitations.py`:

1. "Arbitrary token values pass scenario validation" – creates a token with a
   non-standard format, validates, asserts success.
2. "Token permissions are not included in the serialized simulator
   configuration" – creates a scenario with permissioned tokens, serializes,
   asserts permissions absent.
3. "Token repository visibility is not included in the serialized simulator
   configuration" – same pattern for visibility.
4. "GitHub App and installation fields are excluded from simulator output" –
   creates an app + installation, serializes, asserts no app data.
5. "An installation access token resolves as a literal string value" – creates
   an installation with `access_token`, resolves, asserts literal value.

Validation: run targeted tests:

    set -o pipefail
    uv run pytest simulacat/unittests/test_auth_mode_limitations.py -v 2>&1 \
      | tee /tmp/test-limitations-unit.log |
    uv run pytest tests/steps/test_auth_mode_limitations.py -v 2>&1 \
      | tee /tmp/test-limitations-bdd.log |

Expected: all pass (since they test existing behaviour).

### Stage C: documentation

1. Add a consolidated "Authentication mode limitations" section to
   `docs/users-guide.md` after the "GitHub App installation metadata" section
   and before "Configuration Schema".
2. Add cross-reference notes at the end of the "Authentication tokens" and
   "GitHub App installation metadata" sections.
3. Add Step 3.1.3 design decisions to `docs/simulacat-design.md`.
4. Mark the roadmap entry as done in `docs/roadmap.md`.

### Stage D: hardening and quality gates

    set -o pipefail
    make check-fmt 2>&1 | tee /tmp/simulacat-check-fmt.log
    make typecheck 2>&1 | tee /tmp/simulacat-typecheck.log
    make lint 2>&1 | tee /tmp/simulacat-lint.log
    make test 2>&1 | tee /tmp/simulacat-test.log
    MDLINT=/root/.bun/bin/markdownlint-cli2 \
      make markdownlint 2>&1 | tee /tmp/simulacat-markdownlint.log
    make nixie 2>&1 | tee /tmp/simulacat-nixie.log

Expected: all exit 0.

## Concrete steps

1. Write unit tests in `simulacat/unittests/test_auth_mode_limitations.py`.

   Run targeted tests to confirm they pass:

       set -o pipefail
       uv run pytest simulacat/unittests/test_auth_mode_limitations.py -v \
         2>&1 | tee /tmp/test-limitations-unit.log

2. Write BDD feature file `tests/features/auth_mode_limitations.feature` and
   step definitions in `tests/steps/test_auth_mode_limitations.py`.

   Run targeted tests to confirm they pass:

       set -o pipefail
       uv run pytest tests/steps/test_auth_mode_limitations.py -v 2>&1 \
         | tee /tmp/test-limitations-bdd.log |

3. Add the consolidated "Authentication mode limitations" section to
   `docs/users-guide.md`.

4. Add cross-reference notes to existing auth sections in
   `docs/users-guide.md`.

5. Add Step 3.1.3 design decisions to `docs/simulacat-design.md`.

6. Mark the roadmap entry as done in `docs/roadmap.md`.

7. Run all quality gates:

       set -o pipefail
       make check-fmt 2>&1 | tee /tmp/simulacat-check-fmt.log
       make typecheck 2>&1 | tee /tmp/simulacat-typecheck.log
       make lint 2>&1 | tee /tmp/simulacat-lint.log
       make test 2>&1 | tee /tmp/simulacat-test.log
       MDLINT=/root/.bun/bin/markdownlint-cli2 \
         make markdownlint 2>&1 | tee /tmp/simulacat-markdownlint.log
       make nixie 2>&1 | tee /tmp/simulacat-nixie.log

   Expected: all exit 0.

## Validation and acceptance

Acceptance is achieved when:

- `docs/users-guide.md` contains a consolidated "Authentication mode
  limitations" section comparing all three modes with real GitHub.
- `docs/simulacat-design.md` records Step 3.1.3 design decisions.
- Unit tests pass in `simulacat/unittests/test_auth_mode_limitations.py`.
- BDD scenarios pass in `tests/steps/test_auth_mode_limitations.py`.
- Quality gates succeed:
  - `make check-fmt`
  - `make typecheck`
  - `make lint`
  - `make test`
  - `make markdownlint`
  - `make nixie`
- The roadmap entry is marked as done.

## Idempotence and recovery

The changes are additive and can be re-run safely. If a step fails, fix the
issue and re-run the same command. If documentation linting fails due to a
missing `markdownlint-cli2`, set `MDLINT=/root/.bun/bin/markdownlint-cli2` or
add `/root/.bun/bin` to `PATH`. Use `git status` to inspect and revert local
changes if a restart is required.

## Artifacts and notes

Files created or modified:

- `docs/execplans/3-1-3-document-limitations-of-auth-modes.md` (this file)
- `docs/users-guide.md` (consolidated limitations section)
- `docs/simulacat-design.md` (Step 3.1.3 design decisions)
- `docs/roadmap.md` (mark task done)
- `tests/features/auth_mode_limitations.feature` (BDD scenarios)
- `tests/steps/test_auth_mode_limitations.py` (BDD steps)
- `simulacat/unittests/test_auth_mode_limitations.py` (unit tests)

Total: 7 files (3 new, 4 modified). Within the 15-file tolerance.

## Interfaces and dependencies

No new public interfaces are introduced. Existing interfaces tested:

- `ScenarioConfig.validate()` – verifies token and app validation
- `ScenarioConfig.to_simulator_config()` – verifies serialization excludes
  token and app metadata
- `ScenarioConfig.resolve_auth_token()` – verifies token resolution behaviour
- `AccessToken`, `GitHubApp`, `AppInstallation` – verifies metadata-only
  semantics

## Revision note

- 2026-02-16: initial ExecPlan draft for Step 3.1.3 documentation of
  authentication mode limitations.
