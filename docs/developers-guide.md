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
[ADR 001](adr-001-adopt-the-shared-cv005-contract-library.md).
`tests/workflow_contracts/test_cv005_wiring.py` fails if the pin is not a full
commit, the target stops running the pinned checker, the repository parameter
is wrong, `make all` drops the target or CI stops running it.
