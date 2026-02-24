# Step 4.2.1 API stability and deprecation policy

This Execution Plan (ExecPlan) is a living document. The sections
"Constraints", "Tolerances", "Risks", "Progress", "Surprises & Discoveries",
"Decision Log", and "Outcomes & Retrospective" must be kept up to date as work
proceeds.

Status: COMPLETE

PLANS.md: not present in this repository.

## Purpose / big picture

Complete Step 4.2 by giving downstream consumers a predictable public API
surface and a documented deprecation lifecycle. After this work, consumers and
maintainers can see which symbols and fixtures are part of the supported API,
understand how deprecations will be communicated, and track shipped
capabilities through a changelog that links roadmap items to released behaviour.

Success is observable when:

- every symbol in `simulacat.__all__` and every registered pytest
  fixture is mapped to an explicit stability tier (stable, provisional, or
  deprecated) in a canonical source-of-truth module;
- a custom `SimulacatDeprecationWarning` subclass exists and a helper function
  emits it with migration guidance for deprecated symbols;
- a changelog at `docs/changelog.md` links roadmap phases and steps to shipped
  capabilities and describes behavioural changes;
- consumer-facing documentation in `docs/users-guide.md` explains the API
  stability tiers and the three-phase deprecation lifecycle (introduce
  alongside, warn with guidance, remove after transition period);
- design decisions are recorded in `docs/simulacat-design.md`;
- unit tests (pytest) and behaviour-driven development (BDD) tests (pytest-bdd)
  cover the new contracts;
- `make check-fmt`, `make typecheck`, `make lint`, and `make test` pass;
- Markdown validation (`make markdownlint`, `make nixie`) passes;
- Step 4.2 tasks in `docs/roadmap.md` are marked done.

## Constraints

- Follow `.rules/python-*.md` for Python code and
  `docs/documentation-style-guide.md` for documentation.
- Keep existing public fixture and scenario APIs stable. Do not change any
  existing function signatures or remove existing exports.
- Do not add new runtime dependencies for `simulacat`.
- Use pytest for unit tests and pytest-bdd for behavioural tests.
- Prefer Make targets for quality gates and preserve existing continuous
  integration (CI) conventions.
- Use `enum.StrEnum` for stability tiers (Python 3.12+ is the baseline).
- Use `from __future__ import annotations` in all new Python modules.
- Import conventions: `typing as typ`, `collections.abc as cabc`,
  `dataclasses as dc`, `enum as enum`.

## Tolerances (exception triggers)

- Scope: if implementation exceeds 15 changed files or 800 net lines, stop
  and escalate.
- Interfaces: if existing public API signatures in `simulacat/__init__.py`
  must change (beyond adding new exports), stop and escalate.
- Dependencies: if adding a new package dependency is required, stop and
  escalate.
- Iterations: if quality gates still fail after two full fix attempts, stop
  and escalate with captured logs.

## Risks

- Risk: new `api_stability.py` module must stay in sync with `__all__` and
  pytest fixtures as they evolve. Severity: medium. Likelihood: medium.
  Mitigation: unit test asserts `PUBLIC_API` covers every `__all__` symbol and
  every fixture name, so drift is caught by CI.

- Risk: deprecation warning emission must not break existing imports or
  fixture resolution. Severity: high. Likelihood: low. Mitigation: warnings are
  only emitted when `emit_deprecation_warning` is called explicitly; no
  import-time side effects.

- Risk: changelog may drift from roadmap over time.
  Severity: low. Likelihood: medium. Mitigation: BDD test asserts changelog
  references each completed phase.

## Progress

- [x] (2026-02-23 00:00Z) Draft ExecPlan for Step 4.2.1.
- [x] (2026-02-23 00:05Z) Write failing unit tests for API stability
  contracts.
- [x] (2026-02-23 00:05Z) Write failing BDD tests for API stability and
  changelog.
- [x] (2026-02-23 00:10Z) Implement `simulacat/api_stability.py` with
  stability tiers, public API registry, deprecation warning, and emission
  helper.
- [x] (2026-02-23 00:10Z) Create `docs/changelog.md` linking roadmap phases
  to capabilities.
- [x] (2026-02-23 00:12Z) Update `simulacat/__init__.py` to export new
  public symbols.
- [x] (2026-02-23 00:15Z) Update `docs/simulacat-design.md` with Step 4.2
  design decisions.
- [x] (2026-02-23 00:15Z) Update `docs/users-guide.md` with API stability
  and deprecation sections.
- [x] (2026-02-23 00:15Z) Mark Step 4.2 tasks done in `docs/roadmap.md`.
- [x] (2026-02-23 00:20Z) All quality gates pass and evidence captured.

## Surprises & discoveries

- Observation: `make fmt` reformats Markdown tables with cell padding via
  `mdtablefix`, which broke the Step 4.1 BDD test that matched exact table row
  strings. Evidence: `tests/steps/test_compatibility_matrix.py` assertion
  `| Python | 3.12 | 3.13 | >=3.12,<3.14 |` failed against padded
  `| Python                           | 3.12              | ...`. Impact:
  updated the existing test to normalize cell whitespace before comparison.

## Decision log

- Decision: create a dedicated `simulacat/api_stability.py` module rather than
  adding stability annotations inline or in `__init__.py`. Rationale: keeps the
  stability registry testable and separates stability metadata from import
  mechanics. Follows the pattern set by `compatibility_policy.py`. Date/Author:
  2026-02-23, ExecPlan author.

- Decision: use `enum.StrEnum` for `ApiStability` tiers rather than plain
  string constants. Rationale: provides type safety, IDE support, and
  exhaustive matching while remaining human-readable when serialized. StrEnum
  is available from Python 3.11+ and the project baseline is 3.12. Date/Author:
  2026-02-23, ExecPlan author.

- Decision: define `SimulacatDeprecationWarning(DeprecationWarning)` as a
  custom subclass. Rationale: allows consumers to filter simulacat-specific
  deprecation warnings independently of other library warnings using standard
  `warnings` module filters. Date/Author: 2026-02-23, ExecPlan author.

- Decision: `PUBLIC_API` is a `MappingProxyType` mapping symbol/fixture names
  to `ApiStability` values, following the `COMPATIBILITY_POLICY` pattern.
  Rationale: immutable mapping provides a canonical, testable registry. Reuses
  the `MappingProxyType` idiom already established in
  `compatibility_policy.py`. Date/Author: 2026-02-23, ExecPlan author.

- Decision: all current public symbols and fixtures are classified as `STABLE`
  since the project is establishing its first stability policy. Rationale: the
  existing API has been stable through Phases 1–4.1. Marking everything stable
  formalizes the implicit contract and provides a baseline for future
  deprecation. Date/Author: 2026-02-23, ExecPlan author.

- Decision: `DEPRECATED_APIS` is initially an empty mapping. The infrastructure
  is in place for when deprecations are needed. Rationale: establishing the
  deprecation mechanism now (with tests) means future deprecations follow a
  tested path. No symbols are currently deprecated. Date/Author: 2026-02-23,
  ExecPlan author.

- Decision: place the changelog at `docs/changelog.md` rather than the
  repository root. Rationale: keeps all documentation in the `docs/` directory,
  consistent with the existing documentation structure. Date/Author:
  2026-02-23, ExecPlan author.

## Outcomes & retrospective

Implementation complete. Step 4.2 acceptance criteria are met.

Delivered outcomes:

- Added a canonical API stability module: `simulacat/api_stability.py` with
  `ApiStability` StrEnum, `DeprecatedApi` dataclass,
  `SimulacatDeprecationWarning`, `PUBLIC_API` registry, `DEPRECATED_APIS`
  mapping, and `emit_deprecation_warning` helper.
- Added Step 4.2 unit tests:
  `simulacat/unittests/test_api_stability.py` (14 tests).
- Added Step 4.2 behavioural tests:
  `tests/features/api_stability.feature` and
  `tests/steps/test_api_stability.py` (4 scenarios).
- Created `docs/changelog.md` linking Phases 1–4 to shipped capabilities.
- Updated `simulacat/__init__.py` to export `ApiStability`,
  `SimulacatDeprecationWarning`, and `PUBLIC_API`.
- Updated consumer documentation: `docs/users-guide.md` with "API stability",
  "Deprecation policy", and "Changelog" sections.
- Updated design documentation: `docs/simulacat-design.md` with Step 4.2
  design decisions.
- Marked Step 4.2 roadmap tasks complete in `docs/roadmap.md`.
- Fixed an existing Step 4.1 BDD test that was fragile to table formatting
  changes from `mdtablefix`.

Validation evidence:

- Pre-implementation tests failed as expected:
  `/tmp/step-4-2-unit-pre.log`, `/tmp/step-4-2-bdd-pre.log`.
- Post-implementation targeted tests passed:
  `/tmp/step-4-2-targeted-post.log`.
- Full quality gates passed:
  `/tmp/step-4-2-check-fmt.log`, `/tmp/step-4-2-typecheck.log`,
  `/tmp/step-4-2-lint.log`, `/tmp/step-4-2-test.log`,
  `/tmp/step-4-2-markdownlint.log`, `/tmp/step-4-2-nixie.log`.

## Context and orientation

Relevant repository state before implementation:

- `simulacat/__init__.py` exports 22 symbols via `__all__`: configuration
  helpers (`default_github_sim_config`, `is_json_serializable`,
  `merge_configs`), scenario models (`User`, `Organization`, `Repository`,
  `Branch`, `DefaultBranch`, `Issue`, `PullRequest`, `AccessToken`,
  `GitHubApp`, `AppInstallation`), scenario management (`ScenarioConfig`,
  `ConfigValidationError`), scenario factories (`single_repo_scenario`,
  `monorepo_with_apps_scenario`, `empty_org_scenario`, `merge_scenarios`,
  `github_app_scenario`), and types (`GitHubSimConfig`).
- `simulacat/pytest_plugin.py` registers four fixtures via the `pytest11`
  entry point: `github_sim_config`, `github_simulator`,
  `simulacat_single_repo`, `simulacat_empty_org`.
- `simulacat/compatibility_policy.py` defines `COMPATIBILITY_POLICY` as a
  `MappingProxyType` and `KNOWN_INCOMPATIBILITIES` as a tuple of frozen
  dataclasses. This module is the pattern to follow for `api_stability.py`.
- No API stability markers, deprecation utilities, or changelog exist yet.
- `pyproject.toml` sets version `0.1.0` (Alpha) and `requires-python >=3.12`.
- Unit tests live in `simulacat/unittests/test_*.py` using test classes.
- BDD tests use feature files in `tests/features/*.feature` with step
  implementations in `tests/steps/test_*.py`.

Definitions used in this plan:

- Stable API: a symbol or fixture that consumers may depend on. Changes
  follow the deprecation lifecycle.
- Provisional API: a symbol or fixture that may change without the full
  deprecation lifecycle. Consumers are advised to pin versions.
- Deprecated API: a symbol or fixture that will be removed in a future
  version. Emits warnings with migration guidance.
- Deprecation lifecycle: introduce replacement alongside old API, emit
  warnings with guidance, remove only after a documented transition period.

## Plan of work

### Stage A: tests first (expected to fail before implementation)

Add tests before implementation to encode required behaviour.

Unit tests (pytest), new file `simulacat/unittests/test_api_stability.py`:

- assert `PUBLIC_API` covers every symbol in `simulacat.__all__`;
- assert `PUBLIC_API` covers the four registered fixtures;
- assert every `PUBLIC_API` entry maps to a valid `ApiStability` tier;
- assert `SimulacatDeprecationWarning` is a subclass of `DeprecationWarning`;
- assert `emit_deprecation_warning` emits the correct warning for a
  deprecated symbol (using a test-only deprecated entry);
- assert `emit_deprecation_warning` raises `ValueError` for symbols not in
  `DEPRECATED_APIS`;
- assert `docs/changelog.md` exists and references completed phases.

Behavioural tests (pytest-bdd), new files:

- `tests/features/api_stability.feature`
- `tests/steps/test_api_stability.py`

Behavioural scenarios:

- public API symbols are registered with stability tiers;
- fixtures are registered with stability tiers;
- deprecation warnings include migration guidance;
- changelog links roadmap items to capabilities.

Run targeted tests and confirm they fail before implementation.

### Stage B: implement API stability module and changelog

Implement minimal changes to satisfy failing tests:

- create `simulacat/api_stability.py` with:
  - `ApiStability` StrEnum (`STABLE`, `PROVISIONAL`, `DEPRECATED`),
  - `DeprecatedApi` frozen dataclass,
  - `SimulacatDeprecationWarning(DeprecationWarning)`,
  - `PUBLIC_API` MappingProxyType mapping all 22 `__all__` symbols plus 4
    fixture names to `ApiStability.STABLE`,
  - `DEPRECATED_APIS` empty mapping,
  - `emit_deprecation_warning(symbol_name)` function;
- create `docs/changelog.md` covering Phases 1–4;
- update `simulacat/__init__.py` to export `ApiStability`,
  `SimulacatDeprecationWarning`, and `PUBLIC_API`.

### Stage C: documentation updates

- update `docs/simulacat-design.md` with Step 4.2 design decisions;
- update `docs/users-guide.md` with:
  - "API stability" section explaining the three tiers,
  - "Deprecation policy" section describing the three-phase lifecycle,
  - "Changelog" section linking to `docs/changelog.md`.

### Stage D: finalize, harden, and close roadmap task

- mark all Step 4.2 task checkboxes as done in `docs/roadmap.md`;
- run full repository quality gates and markdown validations;
- capture command outputs and update this ExecPlan with final evidence.

## Concrete steps

1. Create failing unit tests:

       set -o pipefail
       uv run pytest simulacat/unittests/test_api_stability.py -v 2>&1 | tee /tmp/step-4-2-unit-pre.log

2. Create failing behavioural tests:

       set -o pipefail
       uv run pytest tests/steps/test_api_stability.py -v 2>&1 | tee /tmp/step-4-2-bdd-pre.log

3. Implement `simulacat/api_stability.py`, `docs/changelog.md`, and update
   exports, then rerun targeted tests:

       set -o pipefail
       uv run pytest simulacat/unittests/test_api_stability.py -v 2>&1 | tee /tmp/step-4-2-unit-post.log
       uv run pytest tests/steps/test_api_stability.py -v 2>&1 | tee /tmp/step-4-2-bdd-post.log

4. Update docs and roadmap:

   - `docs/simulacat-design.md`
   - `docs/users-guide.md`
   - `docs/roadmap.md`

5. Run full quality gates:

       set -o pipefail
       make check-fmt 2>&1 | tee /tmp/step-4-2-check-fmt.log
       make typecheck 2>&1 | tee /tmp/step-4-2-typecheck.log
       make lint 2>&1 | tee /tmp/step-4-2-lint.log
       make test 2>&1 | tee /tmp/step-4-2-test.log
       make markdownlint 2>&1 | tee /tmp/step-4-2-markdownlint.log
       make nixie 2>&1 | tee /tmp/step-4-2-nixie.log

Expected concise signals:

- pre-implementation targeted tests fail with import errors or missing-module
  assertions;
- post-implementation targeted tests pass;
- full quality gates exit with status `0`.

## Validation and acceptance

Acceptance criteria for Step 4.2 completion:

- `PUBLIC_API` in `simulacat/api_stability.py` maps every `__all__` symbol
  and every registered fixture to an `ApiStability` tier;
- `SimulacatDeprecationWarning` is a `DeprecationWarning` subclass that can
  be filtered independently;
- `emit_deprecation_warning` emits warnings with migration guidance for
  deprecated symbols and raises `ValueError` for unknown symbols;
- `docs/changelog.md` exists and links roadmap phases to capabilities;
- consumer-facing docs in `docs/users-guide.md` explain API stability tiers
  and the deprecation lifecycle;
- design decisions are recorded in `docs/simulacat-design.md`;
- new unit and behavioural tests pass;
- `make check-fmt`, `make typecheck`, `make lint`, and `make test` pass;
- `make markdownlint` and `make nixie` pass;
- Step 4.2 tasks in `docs/roadmap.md` are marked done.

## Idempotence and recovery

- All test and quality-gate commands are safe to rerun.
- If targeted tests fail after implementation, review the specific assertion
  and fix the corresponding module or test.
- Documentation updates are additive and do not remove existing content.

## Artifacts and notes

Capture and retain these logs during implementation:

- `/tmp/step-4-2-unit-pre.log`
- `/tmp/step-4-2-bdd-pre.log`
- `/tmp/step-4-2-unit-post.log`
- `/tmp/step-4-2-bdd-post.log`
- `/tmp/step-4-2-check-fmt.log`
- `/tmp/step-4-2-typecheck.log`
- `/tmp/step-4-2-lint.log`
- `/tmp/step-4-2-test.log`
- `/tmp/step-4-2-markdownlint.log`
- `/tmp/step-4-2-nixie.log`

## Interfaces and dependencies

Planned interfaces to add:

In `simulacat/api_stability.py`:

    import enum

    class ApiStability(enum.StrEnum):
        STABLE = "stable"
        PROVISIONAL = "provisional"
        DEPRECATED = "deprecated"

    @dc.dataclass(frozen=True, slots=True)
    class DeprecatedApi:
        symbol_name: str
        deprecated_since: str
        replacement: str
        removal_version: str
        guidance: str

    class SimulacatDeprecationWarning(DeprecationWarning): …

    PUBLIC_API: cabc.Mapping[str, ApiStability]
    DEPRECATED_APIS: cabc.Mapping[str, DeprecatedApi]

    def emit_deprecation_warning(symbol_name: str) -> None: …

Dependencies and tools used:

- Python standard library only (enum, warnings, dataclasses, types).
- pytest and pytest-bdd for tests.
- No new external dependencies.

## Revision note

Updated this ExecPlan from `IN PROGRESS` to `COMPLETE` after implementation.
Filled all mandatory living sections with executed timestamps, discoveries,
decisions, and quality-gate evidence. Added a surprise entry for the table
formatting issue discovered during implementation.
