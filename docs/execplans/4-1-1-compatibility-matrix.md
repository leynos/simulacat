# Step 4.1.1 compatibility matrix

This Execution Plan (ExecPlan) is a living document. The sections
"Constraints", "Tolerances", "Risks", "Progress", "Surprises & Discoveries",
"Decision Log", and "Outcomes & Retrospective" must be kept up to date as work
proceeds.

Status: COMPLETE

PLANS.md: not present in this repository.

## Purpose / big picture

Complete Step 4.1 by making compatibility support explicit, testable, and easy
to maintain as dependencies evolve. After this work, maintainers and consumers
can see a clear minimum-to-recommended version range for Python, `github3.py`,
Node.js, and `@simulacrum/github-api-simulator`, and they can verify the claim
from automated matrix jobs that execute the reference suites.

Success is observable when:

- version ranges are documented in consumer and design docs with one canonical
  source of truth;
- CI runs reference suites across multiple Python versions and at least two
  `github3.py` major versions when both are supportable;
- known incompatibilities and workarounds are tracked in a dedicated section;
- unit tests (`pytest`) and behavioural tests (`pytest-bdd`) cover the new
  compatibility policy and matrix contracts;
- `make check-fmt`, `make typecheck`, `make lint`, and `make test` pass;
- Markdown validation (`make markdownlint`, `make nixie`) passes;
- Step 4.1 tasks in `docs/roadmap.md` are marked done.

## Constraints

- Follow `.rules/python-*.md` for Python code and
  `docs/documentation-style-guide.md` for docs.
- Keep existing public fixture and scenario APIs stable unless explicit failing
  tests prove a compatibility bug that requires change.
- Do not add new runtime dependencies for `simulacat`.
- Use pytest for unit tests and pytest-bdd for behavioural tests.
- Prefer Make targets for quality gates and preserve existing CI conventions.
- Keep compatibility documentation precise about exact version bounds and
  whether a bound is "supported", "recommended", or "known incompatible".

## Tolerances (exception triggers)

- Scope: if implementation exceeds 18 changed files or 900 net lines, stop and
  escalate.
- Interfaces: if public API signatures in `simulacat/__init__.py` must change,
  stop and escalate.
- Dependencies: if adding a new package dependency is required, stop and
  escalate.
- Matrix breadth: if CI runtime growth exceeds 2x current baseline duration,
  stop and escalate with pruning options.
- Iterations: if quality gates still fail after two full fix attempts, stop
  and escalate with captured logs.

## Risks

- Risk: `github3.py` major versions may have incompatible Python support
  windows.
  Severity: high.
  Likelihood: medium.
  Mitigation: probe available versions first and explicitly encode exclusions.

- Risk: matrix jobs may become flaky because simulator startup depends on Bun
  and subprocess timing.
  Severity: medium.
  Likelihood: medium.
  Mitigation: keep matrix focused on reference suites and isolate compatibility
  jobs from unrelated test load.

- Risk: documentation drift between CI matrix and users' guide.
  Severity: medium.
  Likelihood: medium.
  Mitigation: add tests that assert docs and workflow mention the same policy
  values.

## Progress

- [x] (2026-02-20 23:10Z) Draft ExecPlan for Step 4.1.1.
- [x] (2026-02-21 00:05Z) Baseline dependency/version discovery completed and
  documented.
- [x] (2026-02-21 00:08Z) Unit tests added first for compatibility-policy
  contracts.
- [x] (2026-02-21 00:08Z) Behavioural tests added first for matrix workflow
  and docs behaviour.
- [x] (2026-02-21 00:13Z) Compatibility matrix workflow implemented and passing.
- [x] (2026-02-21 00:15Z) Users' guide and design documentation updated.
- [x] (2026-02-21 00:15Z) Known incompatibilities and workarounds documented.
- [x] (2026-02-21 00:15Z) Step 4.1 roadmap tasks marked done.
- [x] (2026-02-21 00:25Z) All quality gates pass and evidence captured.

## Surprises & discoveries

- Observation: repository CI currently runs only Python 3.13 in
  `.github/workflows/ci.yml`; no compatibility matrix exists yet.
  Evidence: workflow inspection on 2026-02-20.
  Impact: Step 4.1 requires new matrix workflow or matrix expansion.

- Observation: `pyproject.toml` currently pins `github3.py>=4.0.0,<5.0.0`.
  Evidence: `[project.dependencies]` in `pyproject.toml`.
  Impact: supporting two majors may require range expansion or explicit
  incompatibility documentation if v5 is not viable.

- Observation: users' guide already states Python 3.12+ and Node.js 20.x/22.x.
  Evidence: `docs/users-guide.md` prerequisites section.
  Impact: plan must align existing claims with tested matrix evidence.

- Observation: `github3.py` major 5 is not yet published, so two-major
  compatibility coverage must use 3.x and 4.x.
  Evidence: package index query (`python -m pip index versions github3.py`)
  and targeted compatibility runs.
  Impact: workflow matrix uses `>=3.2.0,<4.0.0` and `>=4.0.0,<5.0.0`.

- Observation: compatibility tests pass for both `github3.py` 3.2.0 and 4.0.1
  against `tests/test_github3_compat.py`.
  Evidence: `/tmp/step-4-1-github3-v3-compat.log` and
  `/tmp/step-4-1-github3-v4-compat.log`.
  Impact: `pyproject.toml` dependency range expanded to include both majors.

## Decision log

- Decision: create a dedicated Step 4.1 ExecPlan that treats compatibility as
  a first-class tested contract rather than only a docs update.
  Rationale: roadmap asks for both policy definition and automated verification.
  Date/Author: 2026-02-20, ExecPlan author.

- Decision: include quality-gate commands for both code and markdown.
  Rationale: this task modifies CI/docs/tests and must keep repository health
  gates green.
  Date/Author: 2026-02-20, ExecPlan author.

- Decision: define `github3.py` support as `>=3.2.0,<5.0.0` with 4.0.1 as the
  recommended version.
  Rationale: both major tracks are currently relevant and validated; 5.x is
  not published.
  Date/Author: 2026-02-21, ExecPlan author.

- Decision: add `.github/workflows/compatibility-matrix.yml` instead of
  overloading `.github/workflows/ci.yml`.
  Rationale: keeps compatibility sweeps isolated and explicit while preserving
  existing CI latency expectations for the primary workflow.
  Date/Author: 2026-02-21, ExecPlan author.

- Decision: upgrade simulator dependency to `@simulacrum/github-api-simulator`
  `^0.6.3` while retaining a documented minimum of 0.6.2.
  Rationale: aligns recommended version with latest 0.6 patch release and keeps
  compatibility notes forward-looking in the 0.6 line.
  Date/Author: 2026-02-21, ExecPlan author.

## Outcomes & retrospective

Implementation complete. Step 4.1 acceptance criteria are met.

Delivered outcomes:

- Added a canonical policy module:
  `simulacat/compatibility_policy.py`.
- Added Step 4.1 unit tests:
  `simulacat/unittests/test_compatibility_matrix_policy.py`.
- Added Step 4.1 behavioural tests:
  `tests/features/compatibility_matrix.feature` and
  `tests/steps/test_compatibility_matrix.py`.
- Added a dedicated CI compatibility workflow:
  `.github/workflows/compatibility-matrix.yml`.
- Expanded `github3.py` dependency range in `pyproject.toml` to
  `>=3.2.0,<5.0.0`.
- Updated simulator dependency in `package.json` to `^0.6.3` and refreshed
  `bun.lock`.
- Updated consumer and design documentation:
  `docs/users-guide.md` and `docs/simulacat-design.md`.
- Marked Step 4.1 roadmap tasks complete in `docs/roadmap.md`.

Validation evidence:

- Fail-first tests captured in:
  - `/tmp/step-4-1-unit-pre.log`
  - `/tmp/step-4-1-bdd-pre.log`
- Post-implementation targeted tests passed:
  - `/tmp/step-4-1-unit-post.log`
  - `/tmp/step-4-1-bdd-post.log`
- Full quality gates passed:
  - `/tmp/step-4-1-check-fmt.log`
  - `/tmp/step-4-1-typecheck.log`
  - `/tmp/step-4-1-lint.log`
  - `/tmp/step-4-1-test.log`
  - `/tmp/step-4-1-markdownlint.log`
  - `/tmp/step-4-1-nixie.log`

## Context and orientation

Relevant repository state before implementation:

- `pyproject.toml` sets `requires-python = ">=3.12"` and supports
  `github3.py>=3.2.0,<5.0.0`.
- `package.json` tracks `@simulacrum/github-api-simulator` with `^0.6.3`.
- `docs/users-guide.md` already documents Python 3.12+, Node.js 20.x/22.x, and
  Bun on `PATH`.
- `.github/workflows/ci.yml` currently runs a single Python version (3.13).
- `tests/test_github3_compat.py` covers core compatibility calls against the
  simulator.
- Step 3.2 introduced reference projects and tests:
  - `examples/reference-projects/basic-pytest`
  - `examples/reference-projects/authenticated-pytest`
  - `simulacat/unittests/test_reference_projects.py`
  - `tests/features/reference_projects.feature`
  - `tests/steps/test_reference_projects.py`

Definitions used in this plan:

- Minimum version: oldest version that remains supported.
- Recommended version: default version maintainers and users should target.
- Compatibility matrix: CI matrix axes used to execute reference suites across
  version combinations.
- Known incompatibility: a version combination that fails with a reproducible
  signature and documented workaround.

## Plan of work

### Stage A: establish compatibility policy inputs (no behaviour change)

Collect version candidate ranges from existing constraints and live package
availability:

- Python: derive minimum from `pyproject.toml`, recommended from current CI,
  and tested range from matrix scope.
- `github3.py`: inspect available major versions and Python requirements,
  identify whether two majors are relevant, and list explicit exclusions if not.
- Node.js: confirm current documented range remains valid for simulator runs.
- `@simulacrum/github-api-simulator`: inspect available versions and choose a
  minimum-to-recommended policy that preserves current behaviour.

Go/no-go:

- Go when a draft compatibility policy (min/recommended/tested) exists for all
  four dependencies with rationale.
- No-go when package metadata cannot establish support bounds reliably; escalate
  with options.

### Stage B: tests first (expected to fail before implementation)

Add tests before implementation to encode required behaviour.

Unit tests (pytest), new file
`simulacat/unittests/test_compatibility_matrix_policy.py`:

- assert compatibility policy includes Python, `github3.py`, Node.js, and
  simulator package ranges;
- assert minimum and recommended values are internally consistent;
- assert known incompatibility entries require both a failure signature and a
  workaround string.

Behavioural tests (pytest-bdd), new files:

- `tests/features/compatibility_matrix.feature`
- `tests/steps/test_compatibility_matrix.py`

Behavioural scenarios:

- matrix workflow includes multiple Python versions;
- matrix workflow includes two `github3.py` major-version tracks when relevant
  (or explicit exclusion entry with reason);
- users' guide compatibility section exposes the policy and known
  incompatibilities.

Run targeted tests and confirm they fail before code/doc/workflow changes.

### Stage C: implement compatibility matrix and documentation

Implement minimal changes to satisfy failing tests:

- add a compatibility policy source in code (for example
  `simulacat/compatibility_policy.py`) that records ranges and known
  incompatibilities in a typed, testable shape;
- add or update CI workflow (for example
  `.github/workflows/compatibility-matrix.yml`) to run reference suites across
  matrix combinations:
  - multiple Python versions (at least 3.12 and 3.13),
  - at least two `github3.py` major tracks when relevant;
- ensure matrix job installs the selected `github3.py` constraint explicitly
  before running reference suites;
- update user-facing docs in `docs/users-guide.md` with:
  - minimum-to-recommended version table for all four dependencies,
  - known incompatibilities and workarounds section;
- update design decisions in `docs/simulacat-design.md` documenting why ranges,
  exclusions, and matrix dimensions were chosen.

### Stage D: finalize, harden, and close roadmap task

- mark all Step 4.1 task checkboxes as done in `docs/roadmap.md` once
  validation passes;
- run full repository quality gates and markdown validations;
- capture command outputs and update this ExecPlan `Progress`,
  `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective`
  with final evidence.

## Concrete steps

1. Create failing unit tests:

       set -o pipefail
       uv run pytest simulacat/unittests/test_compatibility_matrix_policy.py -v 2>&1 | tee /tmp/step-4-1-unit-pre.log

2. Create failing behavioural tests:

       set -o pipefail
       uv run pytest tests/steps/test_compatibility_matrix.py -v 2>&1 | tee /tmp/step-4-1-bdd-pre.log

3. Implement compatibility policy module and matrix workflow, then rerun
   targeted tests:

       set -o pipefail
       uv run pytest simulacat/unittests/test_compatibility_matrix_policy.py -v 2>&1 | tee /tmp/step-4-1-unit-post.log
       uv run pytest tests/steps/test_compatibility_matrix.py -v 2>&1 | tee /tmp/step-4-1-bdd-post.log

4. Update docs and roadmap:

   - `docs/users-guide.md`
   - `docs/simulacat-design.md`
   - `docs/roadmap.md`

5. Run full quality gates:

       set -o pipefail
       make check-fmt 2>&1 | tee /tmp/step-4-1-check-fmt.log
       make typecheck 2>&1 | tee /tmp/step-4-1-typecheck.log
       make lint 2>&1 | tee /tmp/step-4-1-lint.log
       make test 2>&1 | tee /tmp/step-4-1-test.log
       make markdownlint 2>&1 | tee /tmp/step-4-1-markdownlint.log
       make nixie 2>&1 | tee /tmp/step-4-1-nixie.log

Expected concise signals:

- pre-implementation targeted tests fail with missing-policy/missing-workflow
  assertions;
- post-implementation targeted tests pass;
- full quality gates exit with status `0`.

## Validation and acceptance

Acceptance criteria for Step 4.1 completion:

- compatibility policy defines minimum and recommended versions for:
  - Python,
  - `github3.py`,
  - Node.js,
  - `@simulacrum/github-api-simulator`;
- reference suites run in CI across multiple Python versions and at least two
  `github3.py` major-version tracks where relevant;
- known incompatibilities and workarounds are documented for consumers;
- new unit and behavioural tests pass;
- `make check-fmt`, `make typecheck`, `make lint`, and `make test` pass;
- `make markdownlint` and `make nixie` pass;
- Step 4.1 tasks in `docs/roadmap.md` are marked done.

## Idempotence and recovery

- All test and quality-gate commands are safe to rerun.
- If matrix jobs fail for a single version combination, record the exact
  signature in the known incompatibility list before narrowing support.
- If documentation and workflow drift, treat the tests as the source of
  reconciliation and update either docs or workflow in the same change.

## Artifacts and notes

Capture and retain these logs during implementation:

- `/tmp/step-4-1-unit-pre.log`
- `/tmp/step-4-1-bdd-pre.log`
- `/tmp/step-4-1-unit-post.log`
- `/tmp/step-4-1-bdd-post.log`
- `/tmp/step-4-1-check-fmt.log`
- `/tmp/step-4-1-typecheck.log`
- `/tmp/step-4-1-lint.log`
- `/tmp/step-4-1-test.log`
- `/tmp/step-4-1-markdownlint.log`
- `/tmp/step-4-1-nixie.log`

## Interfaces and dependencies

Planned interfaces to add or update:

- compatibility policy module (new): exposes typed version-range policy and
  known incompatibilities for tests and docs.
- compatibility matrix workflow (new or updated): executes reference suites for
  each supported compatibility axis combination.

Dependencies and tools used:

- Python toolchain via `uv` and pytest/pytest-bdd for tests.
- GitHub Actions workflow matrix for compatibility execution.
- existing Bun/Node setup for simulator runtime.

## Revision note

Updated this ExecPlan from `DRAFT` to `COMPLETE` after implementation. Filled
all mandatory living sections with executed timestamps, discoveries, decisions,
and quality-gate evidence. Updated context to match shipped dependency ranges
and workflow changes so future maintainers can resume from current state
without external context.
