# Step 2.2 named scenario factories and fixtures

This Execution Plan (ExecPlan) is a living document. The sections
"Constraints", "Tolerances", "Risks", "Progress", "Surprises & Discoveries",
"Decision Log", and "Outcomes & Retrospective" must be kept up to date as work
proceeds.

Status: COMPLETE

PLANS.md: not present in this repository.

## Purpose / big picture

Deliver reusable, named scenario factories and composable scenario fragments so
that tests can describe realistic GitHub states without repetitive boilerplate.
Success is observable when:

- tests can call `single_repo_scenario(...)` (and other factories) to obtain a
  `ScenarioConfig`;
- multiple scenario fragments can be merged into one validated scenario with
  clear conflict errors;
- higher-level fixtures like `simulacat_single_repo` and
  `simulacat_empty_org` are available and documented for use with
  `github_sim_config`;
- `make check-fmt`, `make typecheck`, `make lint`, and `make test` succeed.

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

## Tolerances (exception triggers)

- Scope: if implementation requires changing more than 12 files or more than
  500 net lines of code, stop and escalate.
- Interfaces: if an existing public API signature must change or be removed,
  stop and escalate.
- Dependencies: if a new external dependency is required, stop and escalate.
- Iterations: if tests still fail after two full fix attempts, stop and
  escalate with the failing logs.
- Ambiguity: if "monorepo with apps" cannot be represented without ambiguous
  semantics, stop and ask for guidance before proceeding.

## Risks

- Risk: "monorepo with apps" may not map cleanly to the simulator state.
  Severity: medium Likelihood: medium Mitigation: inspect simulator
  expectations, define a minimal representation (for example, branches per
  app), and document limitations in the users' guide.
- Risk: composing scenarios with shared users or organizations could lead to
  false conflict errors. Severity: medium Likelihood: medium Mitigation: merge
  by identity keys and deduplicate identical entities while raising on true
  conflicts; cover with unit tests.
- Risk: fixtures may be confusing to consumers if they do not integrate with
  `github_simulator` as expected. Severity: low Likelihood: medium Mitigation:
  document recommended fixture usage and add behavioural tests.

## Progress

- [x] (2026-01-17 06:00Z) Drafted ExecPlan for Step 2.2.
- [x] (2026-01-17 06:20Z) Received approval to proceed with implementation.
- [x] (2026-01-17 06:45Z) Added unit and behavioural tests for scenario
  factories and merging.
- [x] (2026-01-17 07:05Z) Implemented scenario factories, merge helper, and
  fixtures, plus a compat module for optional extensions.
- [x] (2026-01-17 07:30Z) Updated documentation and roadmap; ran quality gates.

## Surprises & discoveries

- Observation: linting flagged non-reexport logic inside
  `simulacat/__init__.py`. Evidence: `make lint` reported RUF067 in
  `simulacat/__init__.py`. Impact: moved optional Rust extension loading into
  `simulacat/compat.py`.

## Decision log

- Decision: implement named scenario factories in a new module
  `simulacat/scenario_factories.py`, re-exported via `simulacat/scenario` and
  `simulacat/__init__.py`. Rationale: keeps public API stable while isolating
  factory logic. Date/Author: 2026-01-17, Codex.
- Decision: provide a `merge_scenarios(*scenarios)` helper that deduplicates
  identical entities by key and raises `ConfigValidationError` on conflicts.
  Rationale: enables composition while still catching conflicting definitions.
  Date/Author: 2026-01-17, Codex.
- Decision: add pytest fixtures in `simulacat/pytest_plugin.py` that return
  `GitHubSimConfig` mappings derived from scenario factories, and expose them
  through `simulacat/fixtures.py`. Rationale: aligns with existing fixture
  expectations and simplifies usage. Date/Author: 2026-01-17, Codex.
- Decision: remove the placeholder `hello` compatibility export and its helper
  modules because it is not required by the library. Rationale: keep the public
  API focused and avoid dead code. Date/Author: 2026-01-17, Codex.

## Outcomes & retrospective

Delivered reusable scenario factories, composition helpers, and higher-level
fixtures with unit and behavioural coverage. Updated the users' guide, design
notes, and roadmap, and ran all quality gates successfully. One gap: the
pre-implementation failing-test check could not be demonstrated because
`pytest` was not on PATH before the virtual environment was created; the full
suite was executed via `make test` after implementation. Removed the
placeholder `hello` compatibility export in a follow-up cleanup.

## Context and orientation

Relevant modules and tests:

- `simulacat/scenario_models.py` defines scenario dataclasses.
- `simulacat/scenario_config.py` validates `ScenarioConfig` and serializes to
  simulator configuration.
- `simulacat/scenario.py` is the public scenario API re-export.
- `simulacat/config.py` hosts config helpers like `merge_configs`.
- `simulacat/pytest_plugin.py` defines `github_sim_config` and
  `github_simulator` fixtures.
- `simulacat/fixtures.py` lazily exposes fixtures to avoid a hard pytest
  dependency.
- Unit tests live under `simulacat/unittests/`.
- Behavioural tests use pytest-bdd in `tests/features/` and
  `tests/steps/`.

The new functionality will be Python-only, should not touch TypeScript code,
and must respect the existing scenario validation rules.

## Plan of work

Stage A: understand and propose (no code changes).

Review the current scenario model and fixture behaviour, confirm how
`ScenarioConfig` validation handles duplicates, and inspect the simulator state
shape to decide how to represent "monorepo with apps". If the simulator cannot
model per-app layout, plan for a minimal representation and document the
limitation.

Validation: no code changes; confirm understanding by listing expected new
functions and their signatures.

Stage B: scaffolding and tests (small, verifiable diffs).

Write unit tests before implementation for:

- factory outputs (`single_repo_scenario`, `monorepo_with_apps_scenario`,
  `empty_org_scenario`) using expected `ScenarioConfig` contents;
- merging behaviour that deduplicates identical users/orgs and raises
  `ConfigValidationError` on conflicts (for example, mismatched repo metadata
  for the same owner/name);
- fixture outputs for `simulacat_single_repo` and `simulacat_empty_org`.

Write behavioural tests (pytest-bdd) that:

- build a scenario using a named factory and verify serialized config output;
- merge multiple factory scenarios and assert no duplicates for shared owners;
- demonstrate a conflict (duplicate repo name under the same owner) and assert
  the error message.

Validation: run targeted pytest for the new unit and BDD tests and ensure they
fail before implementation.

Stage C: implementation (minimal change to satisfy tests).

- Add `simulacat/scenario_factories.py` with factory functions and
  `merge_scenarios`.
- Re-export new functions in `simulacat/scenario.py` and
  `simulacat/__init__.py`.
- Add fixtures in `simulacat/pytest_plugin.py` that build on
  `github_sim_config` by returning `GitHubSimConfig` mappings derived from the
  factories (use `ScenarioConfig.to_simulator_config()`), and expose them via
  `simulacat/fixtures.py`.
- Ensure `merge_scenarios` performs key-based deduplication for users,
  organizations, repositories, branches, issues, and pull requests. For each
  key, keep one entry if identical; otherwise raise `ConfigValidationError`
  with a clear conflict message.

Validation: re-run the new unit and behavioural tests; they should now pass.

Stage D: hardening, documentation, cleanup.

- Update `docs/users-guide.md` with factory and fixture usage examples, and
  explain scenario composition and conflict behaviour.
- Record design decisions in `docs/simulacat-design.md` under Step 2.2.
- Mark the Step 2.2 task as done in `docs/roadmap.md` once all tests pass.
- Run all required quality gates: `make check-fmt`, `make typecheck`,
  `make lint`, `make test`, plus `make markdownlint` and `make nixie` for the
  documentation changes.

## Concrete steps

1. Review relevant code and documentation.

    rg -n "ScenarioConfig" simulacat tests
    rg -n "github_sim_config" simulacat/pytest_plugin.py
    rg -n "scenario" docs/users-guide.md docs/simulacat-design.md

2. Add unit tests first.

    touch simulacat/unittests/test_scenario_factories.py

   Populate tests for factory outputs and `merge_scenarios` conflicts. Run
   targeted tests and confirm failure before implementation:

    pytest simulacat/unittests/test_scenario_factories.py -v

3. Add behavioural tests first.

    touch tests/features/scenario_factories.feature
    touch tests/steps/test_scenario_factories.py
    pytest tests/steps/test_scenario_factories.py -v

   Confirm these fail because factories and merge helpers are missing.

4. Implement scenario factories and merge helper.

   Add `simulacat/scenario_factories.py`, update re-exports, and add fixtures.
   Re-run targeted tests until they pass.

5. Update documentation and roadmap.

   Edit:

   - `docs/users-guide.md`
   - `docs/simulacat-design.md`
   - `docs/roadmap.md`

6. Run quality gates (capture logs to avoid truncation).

    set -o pipefail
    make check-fmt | tee /tmp/simulacat-check-fmt.log
    make typecheck | tee /tmp/simulacat-typecheck.log
    make lint | tee /tmp/simulacat-lint.log
    make test | tee /tmp/simulacat-test.log
    MDLINT=/root/.bun/bin/markdownlint-cli2 \
      make markdownlint | tee /tmp/simulacat-markdownlint.log
    make nixie | tee /tmp/simulacat-nixie.log

   Expected result: each command exits 0 and logs report success.

## Validation and acceptance

Acceptance is achieved when:

- `single_repo_scenario`, `monorepo_with_apps_scenario`, and
  `empty_org_scenario` return a valid `ScenarioConfig` with the documented
  defaults.
- `merge_scenarios` combines fragments with shared owners and organizations
  without duplication and raises `ConfigValidationError` for conflicts.
- `simulacat_single_repo` and `simulacat_empty_org` fixtures return
  `GitHubSimConfig` mappings suitable for `github_sim_config` overrides.
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
changes if you need to restart.

## Artifacts and notes

Example usage (expected to work after implementation):

    from simulacat import merge_scenarios, single_repo_scenario

    combined = merge_scenarios(
        single_repo_scenario("alice", name="alpha"),
        single_repo_scenario("alice", name="beta"),
    )
    config = combined.to_simulator_config()

Fixture override example:

    @pytest.fixture
    def github_sim_config(simulacat_single_repo):
        return simulacat_single_repo

## Interfaces and dependencies

New module `simulacat/scenario_factories.py` should define:

    def single_repo_scenario(
        owner: str,
        name: str = "repo",
        *,
        owner_is_org: bool = False,
        default_branch: str = "main",
    ) -> ScenarioConfig

    def empty_org_scenario(login: str) -> ScenarioConfig

    def monorepo_with_apps_scenario(
        owner: str,
        repo: str = "monorepo",
        apps: tuple[str, …] = ("app",),
        *,
        owner_is_org: bool = False,
    ) -> ScenarioConfig

    def merge_scenarios(*scenarios: ScenarioConfig) -> ScenarioConfig

Public exports in `simulacat/scenario.py` and `simulacat/__init__.py` should
include these functions.

Fixtures added in `simulacat/pytest_plugin.py`:

- `simulacat_single_repo` -> returns a `GitHubSimConfig` built from
  `single_repo_scenario`.
- `simulacat_empty_org` -> returns a `GitHubSimConfig` built from
  `empty_org_scenario`.

If `monorepo_with_apps_scenario` requires a different representation, document
that in `docs/users-guide.md` and `docs/simulacat-design.md`.

## Revision note

- 2026-01-17: marked plan as in progress after approval to implement.
- 2026-01-17: marked plan complete, updated outcomes, and refreshed interfaces
  to match delivered signatures.
- 2026-01-17: removed placeholder `hello` compatibility export and helper
  module references.
