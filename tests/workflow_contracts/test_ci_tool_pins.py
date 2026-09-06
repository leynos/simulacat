"""Contract tests for the tool versions the CI workflow depends on.

`main` was red at "Run ruff" from 2026-07-29 because `uv tool install ruff`
named no version. Upstream shipped a `noqa-comments` rule and 59 suppressions
the tree already carried became errors, on a workflow nobody had touched. The
Makefile made it worse by running whichever `ruff` was on `PATH`, so no local
gate could disagree with CI.

These tests assert the install commands and the recipe lines themselves, not a
comment or a step name near them, and each carries a mutation check so a
pattern that quietly matched nothing cannot pass vacuously.
"""

from __future__ import annotations

import re
import typing as typ
from pathlib import Path

import pytest
import yaml

if typ.TYPE_CHECKING:
    import collections.abc as cabc

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"
MAKEFILE_PATH = REPOSITORY_ROOT / "Makefile"
PYPROJECT_PATH = REPOSITORY_ROOT / "pyproject.toml"

pytestmark = pytest.mark.skipif(
    not WORKFLOW_PATH.exists(),
    reason="workflow file not present in this working copy",
)

INSTALL_PATTERNS = (
    re.compile(r"\buv tool install\s+(?P<arguments>.+)$", re.MULTILINE),
    re.compile(r"\buv pip install\s+(?P<arguments>.+)$", re.MULTILINE),
    re.compile(r"\bnpm install -g\s+(?P<arguments>.+)$", re.MULTILINE),
    re.compile(r"\bbun install -g\s+(?P<arguments>.+)$", re.MULTILINE),
)

# `name==version` or `name@version`, where the version may be a shell expansion
# of a variable holding one. A bare name is not pinned.
PINNED = re.compile(r"^@?[A-Za-z0-9._/-]+(==|@)\S+$")
CONTINUES = re.compile(r"\\\s*$")

RUFF_VERSION_RE = re.compile(r"^RUFF_VERSION \?= (?P<version>\S+)$", re.MULTILINE)
TY_VERSION_RE = re.compile(r"^TY_VERSION \?= (?P<version>\S+)$", re.MULTILINE)
RUFF_REQUIREMENT_RE = re.compile(r'"ruff==(?P<version>[^"]+)"')
# A recipe line invoking ruff or ty from PATH rather than through $(RUFF)/$(TY).
PATH_INVOCATION_RE = re.compile(r"^\t@?(ruff|ty)\b", re.MULTILINE)


def _install_arguments(text: str) -> cabc.Iterator[tuple[str, str]]:
    """Yield every (install command, package argument) pair in ``text``."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        for pattern in INSTALL_PATTERNS:
            match = pattern.search(line)
            if match is None:
                continue
            command = match.group(0).strip()
            arguments = match.group("arguments")
            offset = index
            while True:
                continues = bool(CONTINUES.search(arguments))
                for token in arguments.rstrip("\\").split():
                    if not token.startswith("-"):
                        yield command, token.strip("\"'")
                if not continues or offset + 1 >= len(lines):
                    break
                offset += 1
                arguments = lines[offset]


def _run_scripts() -> str:
    """Concatenate every `run:` script in the workflow."""
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert isinstance(workflow, dict), "the workflow must be a mapping"
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "the workflow must declare a jobs mapping"
    scripts = [
        step["run"]
        for job in jobs.values()
        if isinstance(job, dict)
        for step in job.get("steps", [])
        if isinstance(step, dict) and isinstance(step.get("run"), str)
    ]
    assert scripts, "the workflow declares no run: steps"
    return "\n".join(scripts)


def test_the_workflow_installs_tools_at_all() -> None:
    """Guard the patterns: one that matches nothing would prove nothing."""
    assert list(_install_arguments(_run_scripts()))


@pytest.mark.parametrize(
    ("command", "package"),
    list(_install_arguments(_run_scripts())),
    ids=lambda value: value.replace(" ", "-"),
)
def test_every_installed_tool_names_a_version(command: str, package: str) -> None:
    """Every package the workflow installs is pinned to an exact version."""
    resolved = re.sub(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}", "0.0.0", package)
    assert PINNED.match(resolved), f"{command!r} installs {package!r} unpinned"


def test_the_pin_assertion_rejects_an_unpinned_install() -> None:
    """Mutation check for the assertion above."""
    packages = [package for _, package in _install_arguments("  uv tool install ruff")]

    assert packages == ["ruff"]
    assert not PINNED.match(packages[0])


def test_the_makefile_pins_ruff_and_ty_and_uses_them_everywhere() -> None:
    """Both linters are pinned, and no recipe reaches for PATH instead."""
    makefile = MAKEFILE_PATH.read_text(encoding="utf-8")

    pins = (("RUFF_VERSION", RUFF_VERSION_RE), ("TY_VERSION", TY_VERSION_RE))
    for name, pattern in pins:
        match = pattern.search(makefile)
        assert match is not None, f"{name} is not pinned in the Makefile"
        assert re.fullmatch(r"\d+\.\d+\.\d+", match.group("version")), (
            f"{name} must be an exact version, got {match.group('version')!r}"
        )

    assert not PATH_INVOCATION_RE.search(makefile), (
        "a Makefile recipe calls ruff or ty from PATH instead of $(RUFF)/$(TY); "
        "the version it gets is then whatever the machine happens to have"
    )


def test_the_path_invocation_assertion_rejects_a_bare_call() -> None:
    """Mutation check: a recipe line calling ruff from PATH must be caught."""
    assert PATH_INVOCATION_RE.search("check-fmt:\n\truff format --check\n")
    assert PATH_INVOCATION_RE.search("typecheck:\n\tty check\n")
    assert not PATH_INVOCATION_RE.search("check-fmt:\n\t$(RUFF) format --check\n")


def test_the_project_requirement_matches_the_makefile_pin() -> None:
    """The virtual environment's ruff is the version the gates run.

    Two pins for one tool drift silently, and the drift shows up only as a
    formatting or lint diff nobody asked for.
    """
    makefile_match = RUFF_VERSION_RE.search(MAKEFILE_PATH.read_text(encoding="utf-8"))
    project_match = RUFF_REQUIREMENT_RE.search(
        PYPROJECT_PATH.read_text(encoding="utf-8")
    )

    assert makefile_match is not None, "RUFF_VERSION is not pinned in the Makefile"
    assert project_match is not None, "pyproject.toml does not pin ruff exactly"
    assert makefile_match.group("version") == project_match.group("version")
