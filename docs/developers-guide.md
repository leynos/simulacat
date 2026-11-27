# Developers' guide

This guide records internal conventions for maintaining simulacat.

## Coverage workflow contract

`make test-workflow-contracts` holds this shape by running
`cv005-contracts check`, the shared contract library in `leynos/shared-actions`
(`packages/cv005-contracts`), from the full commit named by
`CV005_CONTRACTS_REF` in the Makefile. The library follows local
reusable-workflow calls from every workflow a pull request can start, refuses
the CodeScene host, credential, client and uploader in that closure, and holds
the publisher, the lanes, the environment placement and the lanes' selection
parity to the CV-005 rules. A fix to a rule reaches this repository as a pin
bump. The target needs `uv`, which fetches the Python 3.13 the library runs
under. `.github/cv005.toml` holds the repository's parameters, and its
`interpreter = "3.13"` makes the library require every generate-coverage call
to pin `UV_PYTHON` to that version, inside the project's `requires-python`
(`>=3.12`), so both lanes measure on one Python. The decision is recorded in
[ADR 001](adrs/adr-0001-adopt-the-shared-cv005-contract-library.md).
`tests/workflow_contracts/test_cv005_wiring.py` fails if the pin is not a full
commit, the target stops running the pinned checker, the repository parameter
is wrong, `make all` drops the target or CI stops running it.

## Running uv through the helper

Every `uv` call in the Makefile goes through `scripts/uv_gate.py`, a copy of
the helper in
[shared-actions](https://github.com/leynos/shared-actions/tree/main/uv_gate),
with one exception: the spelling baseline requires typos-config-builder at a
release tag to be called directly, so that call does not use the helper. It
cleans the environment, uses the global uv cache, runs offline first, and goes
online at most once, only when uv proves a cache entry, a managed Python or a
Git source is missing. The copy is vendored byte for byte and is never edited
in place: the concordat `uv-gate-baseline` rule audits its digest, so the
repository's file-length and scripting-stack conventions do not apply to it,
and Ruff excludes it. `make prepare` installs the locked environment, and every
gate that runs the project depends on it. A caller's `UV=/path/to/uv` is
honoured by putting that uv's directory on `PATH`, so the executable must be
named `uv`. A Git-sourced tool that is not cached yet needs uv 0.11.28 or
newer; with an older uv, running the tool once with `uvx` warms the cache.
`uv.lock` changes only through a manual `uv lock`; the gates never change it.

## YAML lint

`make lint` runs `make yamllint` and `make actionlint` as prerequisites.
`make yamllint` runs `yamllint --strict` over every tracked `.yml` and `.yaml`
file, reading `.yamllint.yml`, which extends the estate base
`.yamllint-estate.yml` (a verbatim copy of the concordat canon; do not edit
it). The base ignores Helm chart templates (`**/charts/**/templates/`), so a
tracked file there is passed to yamllint but not checked, and a local `ignore`
in `.yamllint.yml` replaces that entry rather than adding to it. Run it from
the repository root, because yamllint resolves `extends` against the current
directory. `make actionlint` checks the GitHub Actions workflows, accepting the
runner labels in `.github/actionlint.yaml`, and runs ShellCheck over their Bash
and `sh` `run:` scripts when it is on `PATH` (it skips PowerShell steps).

Install the tools locally at the versions CI uses:
`uv tool install yamllint==1.38.0`, and the `actionlint` 1.7.12 and
`shellcheck` 0.11.0 release binaries (a package manager's builds can differ and
change what the lint reports). CI installs the same pinned versions with the
`install-yaml-lint` action of `leynos/shared-actions` before it runs
`make lint`. The `YAMLLINT` and `ACTIONLINT` variables name the commands when
they are not on `PATH`.
