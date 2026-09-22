# Simulacat developers' guide

This guide covers workflows and conventions for contributors working on
simulacat itself, starting with the mutation-testing workflow contract tests.

## Mutation-testing workflow contract tests

This repository runs scheduled, informational mutation testing through a thin
caller workflow,
[`.github/workflows/mutation-testing.yml`](../.github/workflows/mutation-testing.yml),
which delegates to the shared reusable workflow
`leynos/shared-actions/.github/workflows/mutation-mutmut.yml`. The heavy
lifting — running `mutmut` and summarising survivors — lives in
`shared-actions`; this repository carries only declarative configuration. The
run is **informational only**: it never gates a pull request. Survivors are
reported through the job summary and downloadable artefacts so they can be
triaged into tests, not enforced as a blocking check. The mutation targets and
test selection themselves are configured in `[tool.mutmut]` in
`pyproject.toml` (`source_paths`, `pytest_add_cli_args_test_selection`,
`do_not_mutate`).

The workflow runs in two modes. A **daily schedule** fires a change-scoped run
that mutates only the source files touched within the detection window, so
quiet days are cheap no-ops. A **manual dispatch** (the Actions "Run
workflow" control) mutates the whole package; select a branch in that
control to exercise a feature branch.

The caller passes two configuration inputs:

- `paths` — set to `simulacat/`, the change-detection glob that decides
  whether a scheduled run has anything to mutate. It bounds the scheduled run
  to the flat package layout, where mutable source lives in `simulacat/`
  rather than `src/` (`src/` holds the TypeScript simulator, which mutmut
  cannot mutate).
- `module-prefix-strip` — set to an empty string, because the flat package
  layout needs no prefix stripped when mapping mutated file paths back to
  importable modules.

The `uses:` reference pins the shared workflow to a full 40-character commit
SHA rather than a branch or tag, so a force-push upstream cannot silently
change what runs here. The contract test asserts only that the pin is a full
commit SHA, not a particular value, so Dependabot bumps it automatically
without any accompanying test edit.

Because the caller is configuration rather than code, a contract test in
`tests/workflow_contracts/test_mutation_testing.py` pins the shape it must
uphold, failing the pull request when the caller drifts — repointing the pin
at a branch, widening the token scope, or dropping a configuration input —
rather than letting the breakage surface only in a scheduled run. Unlike
callers that skip this test inside mutmut's own sandbox, simulacat's
`[tool.mutmut]` configuration lists `.github/workflows` under `also_copy`, so
the workflow file is present when mutmut runs the suite against a mutant and
the contract test runs there too; it carries no `skipif` guard. Run it
locally with:

```bash
uv run pytest tests/workflow_contracts -q
```

The test validates:

- the `uses:` reference targets `mutation-mutmut.yml` pinned to a full commit
  SHA;
- the `with:` block carries exactly the expected configuration (`paths` and
  `module-prefix-strip` above);
- job permissions are least-privilege (`contents: read`, `id-token: write`)
  and the workflow-level default token scope is empty;
- `concurrency` serialises runs per ref without cancelling one in progress;
  and
- the triggers keep the daily schedule and a plain `workflow_dispatch` with
  no legacy branch input.
