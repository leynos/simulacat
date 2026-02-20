# Step 3.2.1 CI reference projects

This Execution Plan (ExecPlan) is a living document. The sections
"Constraints", "Tolerances", "Risks", "Progress", "Surprises & Discoveries",
"Decision Log", and "Outcomes & Retrospective" must be kept up to date as work
proceeds.

Status: COMPLETE

PLANS.md: not present in this repository.

## Purpose / big picture

Deliver Step 3.2 by adding minimal, runnable reference projects that show how
to use `simulacat` in pytest suites under CI with a standard Python and Node.js
toolchain. The feature is complete when consumers can copy these projects, run
them locally, and run them in CI with predictable results.

Success is observable when:

- at least two minimal reference projects exist and both use `simulacat` in
  pytest;
- each reference project includes CI wiring that sets up Python and Node.js,
  then runs the pytest suite;
- users' guide documentation covers environment requirements (Node.js version
  range and dependency installation method) and troubleshooting signatures;
- design decisions are recorded in `docs/simulacat-design.md`;
- unit tests (pytest) and behavioural tests (pytest-bdd) cover the new Step
  3.2 behaviour;
- `make check-fmt`, `make typecheck`, `make lint`, and `make test` succeed;
- Markdown validation (`make markdownlint`, `make nixie`) succeeds;
- Step 3.2 tasks in `docs/roadmap.md` are marked done when implementation is
  complete.

## Constraints

- Follow existing Python and documentation conventions in `.rules/python-*.md`
  and `docs/documentation-style-guide.md`.
- Do not change existing public Python APIs unless explicitly required by
  failing tests.
- Keep reference projects minimal and focused on CI integration, not feature
  breadth.
- Do not add new runtime dependencies to the `simulacat` library for this
  task.
- Use pytest for unit tests and pytest-bdd for behavioural tests.
- Keep CI examples compatible with a standard Python + Node.js setup (GitHub
  Actions `actions/setup-python` and `actions/setup-node`).
- Keep roadmap semantics intact: mark Step 3.2 entries done only after all
  acceptance criteria pass.

## Tolerances (exception triggers)

- Scope: if implementation requires changes in more than 20 files or more than
  900 net lines, stop and escalate.
- Interface: if any existing public API in `simulacat` must change, stop and
  escalate.
- Dependencies: if a new library runtime dependency is required for
  `simulacat`, stop and escalate.
- Iterations: if quality gates still fail after two full fix attempts, stop
  and escalate with logs.
- CI behaviour: if the reference project requires non-standard CI runners or
  privileged containers, stop and escalate.

## Risks

- Risk: Reference project tests may be slow or flaky because they execute
  subprocess-based workflows. Severity: medium. Likelihood: medium. Mitigation:
  keep projects tiny, reuse existing simulator fixtures, and avoid unnecessary
  network steps in tests.

- Risk: CI examples may drift from repository CI practices over time.
  Severity: medium. Likelihood: medium. Mitigation: add tests that validate
  reference project workflow files and smoke-run the reference pytest suite.

- Risk: Toolchain expectations may be unclear (Node.js versus Bun runtime).
  Severity: medium. Likelihood: medium. Mitigation: document Node.js range
  explicitly, document Bun installation method explicitly, and include concrete
  failure signatures.

## Progress

- [x] (2026-02-20 00:00Z) Draft ExecPlan for Step 3.2.1.
- [x] (2026-02-20 08:16Z) Define the final reference project folder structure
  and naming.
- [x] (2026-02-20 08:20Z) Add unit tests for reference project contracts.
- [x] (2026-02-20 08:21Z) Add behavioural tests (pytest-bdd) for reference
  project execution and CI wiring.
- [x] (2026-02-20 08:26Z) Add reference project files and CI workflows.
- [x] (2026-02-20 08:31Z) Update `docs/users-guide.md` with CI requirements
  and troubleshooting.
- [x] (2026-02-20 08:32Z) Update `docs/simulacat-design.md` with Step 3.2
  design decisions.
- [x] (2026-02-20 08:32Z) Mark Step 3.2 tasks done in `docs/roadmap.md`.
- [x] (2026-02-20 08:50Z) Run all quality gates and record outcomes.

## Surprises & discoveries

- The repository already has a main CI workflow in `.github/workflows/ci.yml`
  and extensive fixture coverage, but no dedicated reference-project artefacts
  for consumers.
- `make test` already exercises both Python and Bun tests, which provides a
  stable gate for this work once reference-project tests are added.
- Running subprocess pytest from behavioural tests is more stable when using
  `sys.executable -m pytest` than shelling out to `uv run pytest`, which avoids
  nested toolchain setup overhead inside worker processes.
- Pytest test collection raised an import-file mismatch when both reference
  projects used the same test module basename (`test_simulator_smoke.py`).
  Fix: use unique filenames per project (`test_basic_simulator_smoke.py` and
  `test_authenticated_simulator_smoke.py`).

## Decision log

- Decision: provide two reference projects rather than one.
  Rationale: Step 3.2 says "projects" and two examples let us show a baseline
  and an authenticated variant while staying minimal. Date/Author: 2026-02-20,
  ExecPlan author.

- Decision: store reference projects under `examples/reference-projects/`.
  Rationale: keeps end-user examples outside package internals and aligns with
  discoverable "copy this example" workflows. Date/Author: 2026-02-20, ExecPlan
  author.

- Decision: validate this feature with both unit tests and pytest-bdd tests.
  Rationale: unit tests lock structure and contracts; behavioural tests prove
  user-observable CI and pytest workflows. Date/Author: 2026-02-20, ExecPlan
  author.

- Decision: resolve the `bun install` working directory from
  `simulacat.orchestration.sim_entrypoint()` in CI examples and docs.
  Rationale: this works for both editable/source layouts and installed wheel
  layouts without hard-coding package paths. Date/Author: 2026-02-20, ExecPlan
  author.

## Outcomes & retrospective

Implementation complete. Step 3.2 acceptance criteria were met with the
following outcomes:

- Added two runnable reference projects:
  - `examples/reference-projects/basic-pytest`
  - `examples/reference-projects/authenticated-pytest`
- Added Step 3.2 validation tests:
  - `simulacat/unittests/test_reference_projects.py`
  - `tests/features/reference_projects.feature`
  - `tests/steps/test_reference_projects.py`
- Updated consumer documentation with:
  - Node.js version range (20.x / 22.x),
  - explicit Simulacrum dependency installation method,
  - troubleshooting signatures for startup, serialization, and coverage
    mismatches.
- Added Step 3.2 design decisions to `docs/simulacat-design.md`.
- Marked Step 3.2 task entries done in `docs/roadmap.md`.

Validation evidence:

- Pre-implementation tests failed as expected:
  - `uv run pytest simulacat/unittests/test_reference_projects.py -v`
  - `uv run pytest tests/steps/test_reference_projects.py -v`
- Post-implementation targeted tests passed:
  - 4 unit tests passed in `test_reference_projects.py`,
  - 3 behavioural scenarios passed in `reference_projects.feature`.
- Full quality gates passed:
  - `make check-fmt`,
  - `make typecheck`,
  - `make lint`,
  - `make test`,
  - `make markdownlint`,
  - `make nixie`.

## Context and orientation

Relevant existing files and directories:

- `docs/roadmap.md` defines Step 3.2 tasks:
  - supply minimal reference projects for pytest + CI,
  - document environment requirements,
  - add troubleshooting signatures.
- `docs/users-guide.md` already documents fixtures, auth limitations, and basic
  environment variables, but does not yet include dedicated CI reference
  projects.
- `docs/simulacat-design.md` currently records decisions through Step 3.1.3.
- `.github/workflows/ci.yml` is the current repository CI baseline.
- `tests/features/` and `tests/steps/` contain existing pytest-bdd patterns.
- `simulacat/unittests/` contains existing unit test style and naming
  conventions.

Proposed new implementation targets:

- `examples/reference-projects/basic-pytest/`:
  - minimal unauthenticated `simulacat` usage;
  - pytest smoke test against `github_simulator`;
  - CI workflow using Python + Node.js setup.
- `examples/reference-projects/authenticated-pytest/`:
  - minimal token-enabled scenario usage;
  - pytest smoke test for auth header behaviour;
  - CI workflow using Python + Node.js setup.
- `simulacat/unittests/test_reference_projects.py`:
  - unit checks for reference project structure and essential metadata.
- `tests/features/reference_projects.feature` and
  `tests/steps/test_reference_projects.py`:
  - behavioural checks that run the reference suites and verify CI workflow
    expectations.

## Plan of work

### Stage A: finalise reference project contract (no functional edits)

Define the minimum contract each project must satisfy:

- pytest suite uses `simulacat` fixtures;
- local command to run tests is explicit and documented;
- CI file sets up Python and Node.js, installs dependencies, and runs tests.

Go/no-go:

- Go when file layout and command contract are stable enough to encode in
  failing tests.
- No-go if "standard Python + Node.js toolchain" is ambiguous in a way that
  affects workflow semantics; escalate with options.

### Stage B: tests first (expected to fail before implementation)

Add unit tests first:

- verify both reference project directories and key files exist;
- verify `pyproject.toml` and workflow files contain required keys and
  commands;
- verify each project has a pytest test that imports/uses `simulacat`.

Add behavioural tests first (pytest-bdd):

- scenario: baseline reference project pytest suite runs successfully;
- scenario: authenticated reference project pytest suite runs successfully;
- scenario: CI workflow files include Python and Node.js setup and test
  execution.

Run new tests and confirm failures before implementation.

### Stage C: implement reference projects and documentation

Create reference projects and wiring:

- add project files (pytest tests, config files, CI workflows, README snippets)
  under `examples/reference-projects/`;
- keep the projects minimal, deterministic, and copy-paste friendly;
- ensure command lines in project readmes and workflows match actual files.

Update documentation:

- `docs/users-guide.md`: add "CI reference projects" guidance with:
  - supported Node.js version range,
  - expected method to install Simulacrum dependencies,
  - troubleshooting section with concrete failure signatures for:
    - simulator startup failures,
    - JSON serialization failures,
    - mismatches between `github3.py` calls and simulator coverage.
- `docs/simulacat-design.md`: add Step 3.2 decisions and rationale.
- `docs/roadmap.md`: mark Step 3.2 tasks done when all acceptance criteria
  pass.

### Stage D: hardening and gates

Run all required gates and capture logs via `tee`:

    set -o pipefail
    make check-fmt 2>&1 | tee /tmp/simulacat-check-fmt.log
    make typecheck 2>&1 | tee /tmp/simulacat-typecheck.log
    make lint 2>&1 | tee /tmp/simulacat-lint.log
    make test 2>&1 | tee /tmp/simulacat-test.log
    make markdownlint 2>&1 | tee /tmp/simulacat-markdownlint.log
    make nixie 2>&1 | tee /tmp/simulacat-nixie.log

Go/no-go:

- Go to completion only when all commands exit with status 0.
- No-go if any command fails twice after targeted fixes; escalate with logs.

## Concrete steps

1. Create test files first:
   - `simulacat/unittests/test_reference_projects.py`
   - `tests/features/reference_projects.feature`
   - `tests/steps/test_reference_projects.py`

2. Run targeted tests to confirm pre-implementation failure:

       set -o pipefail
       uv run pytest simulacat/unittests/test_reference_projects.py -v \
         2>&1 | tee /tmp/step-3-2-unit-pre.log
       uv run pytest tests/steps/test_reference_projects.py -v \
         2>&1 | tee /tmp/step-3-2-bdd-pre.log

3. Implement reference project files under `examples/reference-projects/`.

4. Re-run targeted tests until both pass:

       set -o pipefail
       uv run pytest simulacat/unittests/test_reference_projects.py -v \
         2>&1 | tee /tmp/step-3-2-unit-post.log
       uv run pytest tests/steps/test_reference_projects.py -v \
         2>&1 | tee /tmp/step-3-2-bdd-post.log

5. Update documentation files:
   - `docs/users-guide.md`
   - `docs/simulacat-design.md`
   - `docs/roadmap.md`

6. Run full gates (including Markdown gates) and verify all pass.

## Validation and acceptance

Functional acceptance:

- both reference projects run with pytest and use `simulacat`;
- both reference project CI workflows are valid and invoke Python + Node.js
  setup plus test execution;
- users' guide documents required environment and troubleshooting signatures;
- design document records Step 3.2 decisions;
- roadmap Step 3.2 entries are checked as done.

Quality acceptance:

- `make check-fmt` passes.
- `make typecheck` passes.
- `make lint` passes.
- `make test` passes.
- `make markdownlint` passes.
- `make nixie` passes.

Behavioural evidence:

- pytest-bdd scenarios execute and pass for the reference project workflows.

## Idempotence and recovery

- All commands in this plan are safe to re-run.
- Reference project tests should be deterministic and not depend on external
  mutable state.
- If a workflow edit causes failures, restore the workflow and rerun targeted
  tests before rerunning full gates.
- Keep logs in `/tmp/step-3-2-*.log` and `/tmp/simulacat-*.log` for failure
  diagnosis.

## Artifacts and notes

Expected implementation artifacts:

- two runnable reference project directories under
  `examples/reference-projects/`;
- one unit test module and one pytest-bdd feature/steps pair covering Step
  3.2;
- users-guide and design-document updates;
- roadmap checkboxes moved to done for Step 3.2.

Expected log artifacts:

- `/tmp/step-3-2-unit-pre.log`
- `/tmp/step-3-2-bdd-pre.log`
- `/tmp/step-3-2-unit-post.log`
- `/tmp/step-3-2-bdd-post.log`
- `/tmp/simulacat-check-fmt.log`
- `/tmp/simulacat-typecheck.log`
- `/tmp/simulacat-lint.log`
- `/tmp/simulacat-test.log`
- `/tmp/simulacat-markdownlint.log`
- `/tmp/simulacat-nixie.log`

## Interfaces and dependencies

Required interfaces and tools for this milestone:

- pytest fixtures from `simulacat.pytest_plugin` (especially
  `github_sim_config` and `github_simulator`);
- pytest-bdd feature and step registration via existing `tests/steps/`
  patterns;
- GitHub Actions setup steps using:
  - `actions/setup-python`,
  - `actions/setup-node`,
  - existing dependency installation commands for Python and Node ecosystems.

Dependency expectations:

- Python remains within supported project range (`>=3.12`).
- Node.js is documented with an explicit supported CI range (to be codified in
  `docs/users-guide.md` during implementation).
- No new runtime dependency is required for the `simulacat` library itself.

Revision note (2026-02-20):

- Initial draft created for Step 3.2.1 planning.
- This revision defines scope, tolerances, and a test-first implementation
  sequence without applying code changes yet.

Revision note (2026-02-20, implementation update):

- Updated Status from `DRAFT` to `COMPLETE`.
- Recorded completed progress steps and final validation evidence.
- Added implementation discoveries and a path-resolution design decision.
- Captured delivered artifacts, documentation updates, and roadmap completion.
