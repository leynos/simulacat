# Step 3.1.2 configuration helpers for GitHub Apps

This Execution Plan (ExecPlan) is a living document. The sections
"Constraints", "Tolerances", "Risks", "Progress", "Surprises & Discoveries",
"Decision Log", and "Outcomes & Retrospective" must be kept up to date as work
proceeds.

Status: DONE

PLANS.md: not present in this repository.

## Purpose / big picture

Enable tests to model GitHub App installation metadata and per-installation
repository and organization access when working with the simulacat GitHub API
simulator. After this change, consumers can:

- declare a `GitHubApp` with an app ID, slug, and optional owner;
- attach `AppInstallation` objects that describe which user or organization
  account an app is installed on, which repositories are accessible, and what
  permissions are granted;
- optionally link an installation to an access token value so the
  `github_simulator` fixture sends the appropriate `Authorization` header;
- compose app-aware scenarios using existing factory and merge patterns.

Success is observable when:

- a scenario that declares a GitHub App and one or more installations passes
  validation and can be serialized;
- invalid configurations (missing app reference, unknown account, unknown
  repository) raise `ConfigValidationError` with clear messages;
- the optional `access_token` field on `AppInstallation` integrates with the
  existing token resolution flow in `github_simulator`;
- unit tests (pytest) and behavioural tests (pytest-bdd) cover both valid and
  invalid configurations;
- `make check-fmt`, `make typecheck`, `make lint`, and `make test` succeed;
- documentation and roadmap updates reflect the new behaviour.

The simulator (`@simulacrum/github-api-simulator` v0.6.2) does not support
GitHub App endpoints or installation token exchange. These models are therefore
**client-side metadata only**, following the same pattern established by
`AccessToken` in Step 3.1.1. This limitation must be documented clearly.

## Constraints

- Follow the Python style rules in `.rules/python-*.md` and existing module
  conventions (frozen dataclasses with slots, clear validation errors, tuple
  storage, `from __future__ import annotations`).
- Preserve backwards-compatible behaviour for all existing public APIs in
  `simulacat.scenario`, `simulacat.config`, and pytest fixtures.
- Do not add new runtime dependencies.
- Keep documentation compliant with `docs/documentation-style-guide.md`
  (British English with Oxford spelling, 80-column wrap, sentence-case
  headings).
- Keep simulator orchestration behaviour unchanged; new models must not be
  serialized into the simulator initial state.
- Use pytest for unit tests and pytest-bdd for behavioural tests.
- OAuth application modelling is explicitly out of scope (decision: GitHubApp
  only).

## Tolerances (exception triggers)

- Scope: if implementation requires changing more than 15 files or more than
  600 net lines of code, stop and escalate.
- Interfaces: if an existing public API signature must change or be removed,
  stop and escalate.
- Dependencies: if a new external dependency is required, stop and escalate.
- Iterations: if tests still fail after two full fix attempts, stop and
  escalate with the failing logs.
- Ambiguity: if the `access_token` linkage between `AppInstallation` and the
  existing `AccessToken` flow creates irreconcilable conflicts, stop and
  present options with trade-offs.

## Risks

- Risk: the `access_token` field on `AppInstallation` may create confusion
  about whether it replaces or supplements `ScenarioConfig.tokens`.
  Severity: medium Likelihood: medium Mitigation: document clearly that
  `AppInstallation.access_token` is a convenience alias; it is folded into
  the token resolution flow alongside `ScenarioConfig.tokens`. If both an
  installation token and a standalone token are present, the existing
  `default_token` selection rule applies. Record this as a design decision
  and note in the roadmap that a future revision may introduce per-request
  token switching when the simulator supports it.

- Risk: adding two new tuple fields (`apps`, `app_installations`) to
  `ScenarioConfig` may complicate the merge logic.
  Severity: medium Likelihood: low Mitigation: follow the established
  `_MergeSpec` pattern in `scenario_factories.py` and add merge specs for
  both new entity types. Identity keys: `app_slug` for `GitHubApp`,
  `installation_id` for `AppInstallation`.

- Risk: validation ordering may need adjustment because app installation
  validation depends on both app definitions and user/org/repo indexes.
  Severity: low Likelihood: low Mitigation: insert app validation in
  `_build_indexes()` after users, organizations, and repositories are
  validated but before branches (mirroring the position of token validation).

## Progress

- [x] (2026-02-12 10:00Z) Draft ExecPlan for Step 3.1.2.
- [x] (2026-02-12) Add unit tests for `GitHubApp` and `AppInstallation`
  models and validation.
- [x] (2026-02-12) Add behavioural tests (pytest-bdd) for GitHub App
  scenario composition.
- [x] (2026-02-12) Implement `GitHubApp` and `AppInstallation` dataclasses.
- [x] (2026-02-12) Extend `ScenarioConfig` with `apps` and
  `app_installations` fields.
- [x] (2026-02-12) Add validation logic for apps and installations.
- [x] (2026-02-12) Integrate installation `access_token` with token
  resolution.
- [x] (2026-02-12) Update `merge_scenarios` to handle apps and
  installations.
- [x] (2026-02-12) Add `github_app_scenario` factory helper.
- [x] (2026-02-12) Update public API exports (`scenario.py`,
  `__init__.py`).
- [x] (2026-02-12) Update `docs/users-guide.md` with GitHub App
  configuration section.
- [x] (2026-02-12) Record design decisions in `docs/simulacat-design.md`.
- [x] (2026-02-12) Mark Step 3.1.2 as done in `docs/roadmap.md`.
- [x] (2026-02-12) Run quality gates and confirm all pass.

## Surprises & discoveries

- The `_validate_tokens` method called `_select_auth_token_value` with only
  standalone tokens. When `default_token` referenced an installation
  `access_token`, this failed validation prematurely. Fixed by deferring the
  `default_token` validation to a new `_validate_default_token` method called
  after `_validate_app_installations`, so the full token pool is available.

## Decision log

- Decision: model GitHub Apps only; OAuth applications are out of scope.
  Rationale: the simulator supports neither, and GitHub Apps with
  installations are the richer model. OAuth apps are a simpler, distinct flow
  that can be added later. Date/Author: 2026-02-12, user direction.

- Decision: `AppInstallation` carries an optional `access_token` field that
  integrates with the existing `Authorization` header flow.
  Rationale: lets tests express "this installation token is used for auth" in
  a single place. The token value is folded into the token resolution flow
  alongside `ScenarioConfig.tokens`. This design may need revisiting if
  future simulator versions support per-request token switching or
  installation token exchange. Date/Author: 2026-02-12, user direction.

- Decision: new models are metadata-only and are NOT serialized into the
  simulator initial state, following the `AccessToken` precedent from Step
  3.1.1. Rationale: the simulator does not expose GitHub App endpoints.
  Date/Author: 2026-02-12, ExecPlan author.

## Outcomes & retrospective

Implementation complete. All acceptance criteria met:

- 24 unit tests and 4 behaviour-driven development (BDD) scenarios pass.
- All quality gates pass: `make check-fmt`, `make typecheck`, `make lint`,
  `make test`, `make markdownlint`, `make nixie`.
- 11 files modified, within the 15-file tolerance.
- No new runtime dependencies added.
- No existing public API signatures changed.
- Documentation updated in users' guide, design document, and roadmap.

Key implementation note: the `default_token` validation was moved to a
dedicated `_validate_default_token` method called after both
`_validate_tokens` and `_validate_app_installations` to allow `default_token`
to reference installation access tokens.

## Context and orientation

The simulacat project provides a pytest integration for running tests against
a local GitHub API simulator. The codebase lives at the repository root with
the following key layout:

- `simulacat/scenario_models.py` – frozen dataclasses for domain concepts
  (`User`, `Organization`, `Repository`, `Branch`, `AccessToken`, `Issue`,
  `PullRequest`). Each model uses `@dc.dataclass(frozen=True, slots=True)`.
- `simulacat/scenario_config.py` – `ScenarioConfig` container with
  `validate()`, `to_simulator_config()`, and `resolve_auth_token()`. Contains
  `ConfigValidationError` and all validation helpers.
- `simulacat/scenario_factories.py` – named factory functions
  (`single_repo_scenario`, `monorepo_with_apps_scenario`,
  `empty_org_scenario`) and `merge_scenarios` with `_MergeSpec`-based
  conflict detection.
- `simulacat/scenario.py` – public re-exports of models, config, and
  factories.
- `simulacat/__init__.py` – top-level re-exports for `from simulacat import`.
- `simulacat/pytest_plugin.py` – `github_sim_config`, `github_simulator`,
  `simulacat_single_repo`, `simulacat_empty_org` fixtures. Tokens flow
  through `__simulacat__` metadata key and are set on the `github3.py`
  session `Authorization` header.
- `simulacat/fixtures.py` – lazy `__getattr__` imports to avoid hard pytest
  dependency.
- `simulacat/types.py` – TypedDict definitions for the simulator JSON schema.
- `simulacat/unittests/` – co-located unit tests (notably
  `test_auth_tokens.py`).
- `tests/features/` – BDD feature files for pytest-bdd.
- `tests/steps/` – BDD step implementations.
- `docs/simulacat-design.md` – design decisions document.
- `docs/users-guide.md` – consumer-facing documentation.
- `docs/roadmap.md` – development roadmap with task status.

The existing `AccessToken` (Step 3.1.1) established the pattern this plan
follows: tokens are metadata-only, not sent to the simulator, and applied as
`Authorization` headers on the `github3.py` session. The `__simulacat__`
metadata key in config mappings carries auth tokens through the fixture
pipeline. Token selection uses `ScenarioConfig.resolve_auth_token()` with
single-token auto-selection and explicit `default_token` for multiple tokens.

## Plan of work

### Stage A: understand and propose (no code changes)

Review the existing `AccessToken` implementation, `ScenarioConfig` validation
pipeline, `merge_scenarios` mechanics, and BDD test patterns. Confirm the
approach. This stage is now complete via the exploration work that produced
this ExecPlan.

Validation: no code changes; the ExecPlan itself serves as the deliverable.

### Stage B: scaffolding and tests (small, verifiable diffs)

Write failing tests before implementation:

**Unit tests** in `simulacat/unittests/test_github_app.py`:

- `GitHubApp` construction with `app_slug`, `name`, and optional `app_id`
  and `owner`.
- `GitHubApp` rejects blank `app_slug` and `name`.
- `AppInstallation` construction with `installation_id`, `app_slug`,
  `account`, and optional `repositories`, `permissions`, `access_token`.
- `AppInstallation` normalises collection fields to tuples and rejects string
  arguments (following `AccessToken.__post_init__` pattern).
- `ScenarioConfig` validation: installation `app_slug` must reference a
  defined `GitHubApp`.
- `ScenarioConfig` validation: installation `account` must reference a defined
  user or organization.
- `ScenarioConfig` validation: installation `repositories` must reference
  defined repositories (in `owner/repo` format).
- `ScenarioConfig` validation: installation `installation_id` must be a
  positive integer and unique across installations.
- `ScenarioConfig` validation: app `app_slug` must be unique across apps.
- `ScenarioConfig` validation: installation `access_token` integrates with
  token resolution (acts as an additional token in the pool).
- Happy-path test: valid app + installation scenario validates and resolves.

**BDD tests** in `tests/features/github_app.feature` and
`tests/steps/test_github_app.py`:

- Scenario: a GitHub App scenario includes app metadata after serialization.
- Scenario: an app installation with an access token sets the Authorization
  header.
- Scenario: app scenarios can be merged with repository scenarios.
- Scenario: invalid installation references raise a validation error.

Validation: run `pytest simulacat/unittests/test_github_app.py -v` and
`pytest tests/steps/test_github_app.py -v`; expect failures because the
models and validation do not yet exist.

### Stage C: implementation (minimal change to satisfy tests)

**C1. Data models** (`simulacat/scenario_models.py`):

Add two new frozen dataclasses after `AccessToken`:

    @dc.dataclass(frozen=True, slots=True)
    class GitHubApp:
        app_slug: str
        name: str
        app_id: int | None = None
        owner: str | None = None

    @dc.dataclass(frozen=True, slots=True)
    class AppInstallation:
        installation_id: int
        app_slug: str
        account: str
        repositories: tuple[str, ...] = dc.field(default_factory=tuple)
        permissions: tuple[str, ...] = dc.field(default_factory=tuple)
        access_token: str | None = None

`AppInstallation.__post_init__` normalises `repositories` and `permissions`
to tuples and rejects bare string arguments, following the `AccessToken`
pattern. Update `__all__` to include both new classes.

**C2. ScenarioConfig fields** (`simulacat/scenario_config.py`):

Add two new tuple fields to `ScenarioConfig`:

    apps: tuple[GitHubApp, ...] = dc.field(default_factory=tuple)
    app_installations: tuple[AppInstallation, ...] = dc.field(
        default_factory=tuple
    )

Normalize both in `__post_init__`. No changes to `to_simulator_config()`
since these are metadata-only and must not be serialized.

**C3. Validation** (`simulacat/scenario_config.py`):

Add `_validate_apps()` and `_validate_app_installations()` methods:

- `_validate_apps()`: validate `app_slug` is non-empty text, `name` is
  non-empty text, `app_id` (if set) is a positive integer, `owner` (if set)
  references a defined user or organization. Ensure `app_slug` is unique
  across all apps.
- `_validate_app_installations()`: validate `installation_id` is a positive
  integer and unique, `app_slug` references a defined `GitHubApp`,
  `account` references a defined user or organization, `repositories` entries
  are in `owner/repo` format and reference defined repositories,
  `permissions` are unique per installation, `access_token` (if set) is
  non-empty text.

Call both in `_build_indexes()` after `_validate_tokens()` and before
`_validate_branches()`. Store the app slug set in `_ScenarioIndexes` for
downstream use.

**C4. Token integration** (`simulacat/scenario_config.py`):

Update `resolve_auth_token()` to include installation access tokens in the
candidate pool. When an `AppInstallation` declares an `access_token`, its
value is appended to the token values list alongside `ScenarioConfig.tokens`.
The existing `_select_auth_token_value()` logic then applies: single token
auto-selects, multiple tokens require `default_token`. Validation must also
check that installation access token values do not duplicate standalone token
values.

**C5. Merge support** (`simulacat/scenario_factories.py`):

Add two `_merge_entries` calls in `merge_scenarios`:

- Apps merged by `app_slug` identity key.
- Installations merged by `installation_id` identity key.

Pass merged apps and installations to the returned `ScenarioConfig`.

**C6. Factory helper** (`simulacat/scenario_factories.py`):

Add `github_app_scenario()`:

    def github_app_scenario(
        app_slug: str,
        name: str,
        *,
        account: str,
        account_is_org: bool = False,
        repositories: tuple[str, ...] = (),
        permissions: tuple[str, ...] = (),
        access_token: str | None = None,
        app_id: int | None = None,
    ) -> ScenarioConfig:

This factory creates a `GitHubApp`, an `AppInstallation`, the account
user/org, and any referenced repositories. It returns a `ScenarioConfig`
that can be merged with other scenarios.

**C7. Public API exports**:

- `simulacat/scenario_models.py` `__all__`: add `GitHubApp`,
  `AppInstallation`.
- `simulacat/scenario.py`: import and re-export `GitHubApp`,
  `AppInstallation`, `github_app_scenario`.
- `simulacat/__init__.py`: import and re-export `GitHubApp`,
  `AppInstallation`, `github_app_scenario`.
- `simulacat/scenario_factories.py` `__all__`: add `github_app_scenario`.

Validation: re-run the new unit and behavioural tests; they should now pass.
Run `make check-fmt`, `make typecheck`, `make lint`, `make test`.

### Stage D: hardening, documentation, cleanup

**D1. Users' guide** (`docs/users-guide.md`):

Add a new section "GitHub App installation metadata" after the existing
"Authentication tokens" section. Include:

- explanation that GitHub App models are metadata-only (simulator does not
  support App endpoints);
- example showing `GitHubApp` + `AppInstallation` with an `access_token`;
- example showing the `github_app_scenario` factory;
- note that `access_token` on installations integrates with the existing
  `default_token` selection logic;
- clear limitation note: the simulator does not enforce installation-scoped
  permissions or repository access; these fields document test intent only.

**D2. Design document** (`docs/simulacat-design.md`):

Add a subsection under "Step 3.1 – Authentication and GitHub App workflows"
documenting:

- the decision to model GitHub Apps only (not OAuth apps);
- the metadata-only pattern following `AccessToken`;
- the `access_token` linkage design and its limitations;
- the note that this design should be revisited if the simulator adds
  GitHub App support in a future release.

**D3. Roadmap** (`docs/roadmap.md`):

Mark the Step 3.1.2 task (line 146) as done: change `- [ ]` to `- [x]`.

**D4. Quality gates**:

Run all required quality gates and capture logs:

    set -o pipefail
    make check-fmt 2>&1 | tee /tmp/simulacat-check-fmt.log
    make typecheck 2>&1 | tee /tmp/simulacat-typecheck.log
    make lint 2>&1 | tee /tmp/simulacat-lint.log
    make test 2>&1 | tee /tmp/simulacat-test.log
    MDLINT=/root/.bun/bin/markdownlint-cli2 \
      make markdownlint 2>&1 | tee /tmp/simulacat-markdownlint.log
    make nixie 2>&1 | tee /tmp/simulacat-nixie.log

Expected result: all exit 0.

## Concrete steps

1. Write unit tests in `simulacat/unittests/test_github_app.py`.

   Run targeted tests to confirm they fail:

       set -o pipefail
       uv run pytest simulacat/unittests/test_github_app.py -v 2>&1 \
         | tee /tmp/test-github-app-pre.log

   Expected: import errors or `AttributeError` because models do not exist
   yet.

2. Write BDD feature file `tests/features/github_app.feature` and step
   definitions in `tests/steps/test_github_app.py`.

   Run targeted tests to confirm they fail:

       set -o pipefail
       uv run pytest tests/steps/test_github_app.py -v 2>&1 \
         | tee /tmp/test-github-app-bdd-pre.log

   Expected: import errors because `GitHubApp` and `AppInstallation` are
   not yet defined.

3. Implement `GitHubApp` and `AppInstallation` in
   `simulacat/scenario_models.py`.

4. Extend `ScenarioConfig` in `simulacat/scenario_config.py` with new fields,
   validation methods, and updated token resolution.

5. Update `merge_scenarios` in `simulacat/scenario_factories.py` and add the
   `github_app_scenario` factory.

6. Update public API exports in `simulacat/scenario.py`,
   `simulacat/__init__.py`, and `simulacat/scenario_factories.py`.

7. Run targeted tests to confirm they pass:

       set -o pipefail
       uv run pytest simulacat/unittests/test_github_app.py -v 2>&1 \
         | tee /tmp/test-github-app-post.log
       uv run pytest tests/steps/test_github_app.py -v 2>&1 \
         | tee /tmp/test-github-app-bdd-post.log

   Expected: all new tests pass.

8. Update documentation:
   - `docs/users-guide.md`
   - `docs/simulacat-design.md`
   - `docs/roadmap.md`

9. Run all quality gates:

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

- `ScenarioConfig` can include `GitHubApp` and `AppInstallation` entries, and
  invalid configurations raise `ConfigValidationError` with descriptive
  messages.
- An `AppInstallation` with an `access_token` integrates with
  `resolve_auth_token()` and, via `github_simulator`, sets the
  `Authorization` header on the `github3.py` session.
- `github_app_scenario(...)` returns a valid `ScenarioConfig` that can be
  merged with other scenarios via `merge_scenarios`.
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

Example usage (expected to work after implementation):

    from simulacat import (
        AppInstallation,
        GitHubApp,
        Repository,
        ScenarioConfig,
        User,
    )

    scenario = ScenarioConfig(
        users=(User(login="octocat"),),
        repositories=(Repository(owner="octocat", name="hello-world"),),
        apps=(
            GitHubApp(app_slug="my-bot", name="My Bot", app_id=12345),
        ),
        app_installations=(
            AppInstallation(
                installation_id=1,
                app_slug="my-bot",
                account="octocat",
                repositories=("octocat/hello-world",),
                permissions=("contents", "pull_requests"),
                access_token="ghs_installation_token",
            ),
        ),
    )

    scenario.validate()
    token = scenario.resolve_auth_token()
    # token == "ghs_installation_token"

Factory example:

    from simulacat import github_app_scenario, single_repo_scenario
    from simulacat import merge_scenarios

    app = github_app_scenario(
        "deploy-bot",
        "Deploy Bot",
        account="octocat",
        repositories=("octocat/hello-world",),
        permissions=("contents",),
        access_token="ghs_deploy",
    )

    repo = single_repo_scenario("octocat", name="hello-world")
    combined = merge_scenarios(repo, app)
    config = combined.to_simulator_config()

Fixture override example:

    import pytest
    from simulacat import github_app_scenario

    @pytest.fixture
    def github_sim_config():
        return github_app_scenario(
            "my-app",
            "My App",
            account="test-org",
            account_is_org=True,
            access_token="ghs_app_token",
        )

## Interfaces and dependencies

New dataclasses in `simulacat/scenario_models.py`:

    @dc.dataclass(frozen=True, slots=True)
    class GitHubApp:
        app_slug: str
        name: str
        app_id: int | None = None
        owner: str | None = None

    @dc.dataclass(frozen=True, slots=True)
    class AppInstallation:
        installation_id: int
        app_slug: str
        account: str
        repositories: tuple[str, ...] = dc.field(default_factory=tuple)
        permissions: tuple[str, ...] = dc.field(default_factory=tuple)
        access_token: str | None = None

        def __post_init__(self) -> None:
            # Normalise collections; reject bare strings.
            ...

New fields on `ScenarioConfig`:

    apps: tuple[GitHubApp, ...] = dc.field(default_factory=tuple)
    app_installations: tuple[AppInstallation, ...] = dc.field(
        default_factory=tuple
    )

New factory in `simulacat/scenario_factories.py`:

    def github_app_scenario(
        app_slug: str,
        name: str,
        *,
        account: str,
        account_is_org: bool = False,
        repositories: tuple[str, ...] = (),
        permissions: tuple[str, ...] = (),
        access_token: str | None = None,
        app_id: int | None = None,
    ) -> ScenarioConfig

New public exports added to `simulacat/scenario.py` and
`simulacat/__init__.py`:

- `GitHubApp`
- `AppInstallation`
- `github_app_scenario`

Files modified (expected):

- `simulacat/scenario_models.py` (add models)
- `simulacat/scenario_config.py` (add fields, validation, token integration)
- `simulacat/scenario_factories.py` (add factory, update merge)
- `simulacat/scenario.py` (add re-exports)
- `simulacat/__init__.py` (add re-exports)
- `simulacat/unittests/test_github_app.py` (new unit tests)
- `tests/features/github_app.feature` (new BDD feature)
- `tests/steps/test_github_app.py` (new BDD steps)
- `docs/users-guide.md` (new section)
- `docs/simulacat-design.md` (new design decisions)
- `docs/roadmap.md` (mark task done)

Total: 11 files (within the 15-file tolerance).

## Revision note

- 2026-02-12: initial ExecPlan draft for Step 3.1.2 configuration helpers for
  GitHub Apps. Scope limited to GitHubApp only (no OAuth). AppInstallation
  includes optional access_token field linked to the existing token resolution
  flow.
