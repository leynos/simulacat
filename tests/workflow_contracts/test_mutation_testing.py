"""Contract tests for the mutation-testing caller workflow.

The executable logic lives in the ``leynos/shared-actions`` reusable
workflow, which carries its own unit and integration tests; simulacat's
caller is declarative configuration. These tests parse the caller with
PyYAML and pin the contract it must uphold, so drift (repointing the pin
at a branch, widening permissions, or losing the caller configuration)
fails CI on the pull request rather than surfacing in a scheduled or
manual run.

The test asserts the caller references the correct reusable workflow at a
commit SHA; it does not pin which SHA. Dependabot owns the SHA value, so a
routine bump PR must not fail this contract.
"""

from __future__ import annotations

import re
import typing as typ
from pathlib import Path

import yaml

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "mutation-testing.yml"
)

USES_RE = re.compile(
    r"^leynos/shared-actions/\.github/workflows/mutation-mutmut\.yml@[0-9a-f]{40}$"
)

EXPECTED_WITH = {
    "paths": "simulacat/",
    "module-prefix-strip": "",
}

EXPECTED_CRON = "20 6 * * *"


def _load() -> dict[typ.Any, typ.Any]:
    """Parse the workflow file.

    Returns
    -------
    dict
        The parsed workflow document.

    """
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _triggers(workflow: dict[typ.Any, typ.Any]) -> dict[typ.Any, typ.Any]:
    """Return the ``on:`` mapping (PyYAML parses the bare key as True).

    Parameters
    ----------
    workflow
        The parsed workflow document.

    Returns
    -------
    dict
        The trigger mapping declared under ``on:``.

    """
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict), "the workflow must declare an on: mapping"
    return triggers


def _mutation_job(workflow: dict[typ.Any, typ.Any]) -> dict[typ.Any, typ.Any]:
    """Return the single calling job.

    Parameters
    ----------
    workflow
        The parsed workflow document.

    Returns
    -------
    dict
        The ``mutation`` job mapping.

    """
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "the workflow must declare a jobs mapping"
    assert jobs, "the workflow must declare at least one job"
    assert list(jobs) == ["mutation"], (
        f"expected a single job named 'mutation', found {sorted(jobs)}"
    )
    return jobs["mutation"]


def test_uses_reference_is_pinned_to_a_commit_sha() -> None:
    """The job must call the shared workflow, pinned to a full commit SHA.

    Dependabot owns the pinned commit value; this test only asserts the
    shape of the reference (correct reusable workflow path, pinned to a
    40-hex commit SHA rather than a mutable branch or tag).
    """
    uses = _mutation_job(_load()).get("uses")
    assert uses is not None, "jobs.mutation.uses is missing"
    assert USES_RE.match(uses), (
        f"jobs.mutation.uses must reference mutation-mutmut.yml pinned to a "
        f"40-character commit SHA, got {uses!r}"
    )


def test_job_permissions_are_exactly_least_privilege() -> None:
    """The job grants contents: read and id-token: write, nothing broader."""
    permissions = _mutation_job(_load()).get("permissions")
    assert permissions == {"contents": "read", "id-token": "write"}, (
        "jobs.mutation.permissions must be exactly "
        f"{{'contents': 'read', 'id-token': 'write'}}, got {permissions!r}"
    )


def test_workflow_default_permissions_are_empty() -> None:
    """The workflow-level default token scope is empty."""
    workflow = _load()
    assert workflow.get("permissions") == {}, (
        f"top-level permissions must be an empty mapping, got "
        f"{workflow.get('permissions')!r}"
    )


def test_concurrency_serializes_per_ref_without_cancelling() -> None:
    """Runs queue per ref instead of cancelling one another."""
    concurrency = _load().get("concurrency")
    assert isinstance(concurrency, dict), "the workflow must declare concurrency"
    assert concurrency.get("group") == "mutation-testing-${{ github.ref }}", (
        f"concurrency.group must key on the triggering ref, got "
        f"{concurrency.get('group')!r}"
    )
    assert concurrency.get("cancel-in-progress") is False, (
        f"concurrency.cancel-in-progress must be false, got "
        f"{concurrency.get('cancel-in-progress')!r}"
    )


def test_triggers_keep_schedule_and_plain_dispatch() -> None:
    """The daily schedule stays; dispatch declares no inputs."""
    triggers = _triggers(_load())
    schedule = triggers.get("schedule")
    assert schedule == [{"cron": EXPECTED_CRON}], (
        f"on.schedule must be the daily 06:20 UTC cron, got {schedule!r}"
    )
    assert "workflow_dispatch" in triggers, "on.workflow_dispatch is missing"
    dispatch = triggers.get("workflow_dispatch") or {}
    inputs = dispatch.get("inputs") or {}
    assert not inputs, (
        "on.workflow_dispatch must not declare inputs; the Actions "
        f"run-workflow control selects the ref, got {inputs!r}"
    )


def test_with_block_carries_the_caller_configuration() -> None:
    """The caller passes the flat-layout paths and module prefix."""
    with_block = _mutation_job(_load()).get("with")
    assert with_block == EXPECTED_WITH, (
        f"jobs.mutation.with must be exactly {EXPECTED_WITH!r}, got {with_block!r}"
    )
