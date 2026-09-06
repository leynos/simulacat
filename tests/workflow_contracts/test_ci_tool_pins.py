"""Contract tests for the tool versions the CI workflow depends on.

`main` was red at "Run ruff" from 2026-07-29 because `uv tool install ruff`
named no version. Upstream shipped a `noqa-comments` rule and 59 suppressions
the tree already carried became errors, on a workflow nobody had touched. The
Makefile made it worse by running whichever `ruff` was on `PATH`, so no local
gate could disagree with CI.

These tests assert the install commands and the recipe lines themselves, not a
comment or a step name near them. A version written as `${VAR}` is resolved
back to the value the step's `env` gives it, because a variable holding
`latest` is not a pin and a misspelt variable name is not one either. Each
assertion carries a mutation check, so a pattern that quietly matched nothing
cannot pass vacuously.

The tests are module-level functions rather than grouped in classes: this
repository's ruff configuration enables `PLR6301`, which rejects a test method
that does not use `self`.
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

if not WORKFLOW_PATH.exists():
    # An import-time skip, not a `pytestmark`: the parametrised cases below are
    # built while this module is imported, which is before pytest applies a
    # marker, so a marker would not stop the workflow being read.
    pytest.skip(
        "workflow file not present in this working copy",
        allow_module_level=True,
    )

# Package-manager installs, where the version travels with the package name.
INSTALL_PATTERNS = (
    re.compile(r"\buv tool install\s+(?P<arguments>.+)$", re.MULTILINE),
    re.compile(r"\buv pip install\s+(?P<arguments>.+)$", re.MULTILINE),
    re.compile(r"\bnpm install -g\s+(?P<arguments>.+)$", re.MULTILINE),
    re.compile(r"\bbun install -g\s+(?P<arguments>.+)$", re.MULTILINE),
)

# `cargo install`, where the version is a separate `--version` argument and the
# crate name is a bare word. Matched separately for that reason.
CARGO_INSTALL = re.compile(
    r"\bcargo(?:\s+\+\S+)?\s+install\s+(?P<arguments>.+)$", re.MULTILINE
)

# An exact version: digits and dots, optionally a pre-release suffix. A moving
# tag or a range is not a version, so `latest`, `^0.23`, `~=1.2`, `1.*` and any
# comparator are rejected; each would reintroduce the drift a pin prevents.
EXACT_VERSION = r"\d+(?:\.\d+)+(?:[-.][0-9A-Za-z][0-9A-Za-z.]*)?"
PINNED = re.compile(rf"^@?[A-Za-z0-9._/-]+(?:==|@){EXACT_VERSION}$")
# `cargo install --version` accepts a bare version or one with a leading `=`.
CARGO_VERSION = re.compile(rf"^=?{EXACT_VERSION}$")
SHELL_VARIABLE = re.compile(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}")

# `uv` may be spelt literally or through the Makefile's `$(UV)` variable.
UV_COMMAND = r"(?:uv|\$\(UV\))"

RUFF_VERSION_RE = re.compile(r"^RUFF_VERSION \?= (?P<version>\S+)$", re.MULTILINE)
TY_VERSION_RE = re.compile(r"^TY_VERSION \?= (?P<version>\S+)$", re.MULTILINE)
RUFF_DEFINITION_RE = re.compile(
    rf"^RUFF = .*{UV_COMMAND} tool run ruff@\$\(RUFF_VERSION\)", re.MULTILINE
)
TY_DEFINITION_RE = re.compile(
    rf"^TY = .*{UV_COMMAND} tool run ty@\$\(TY_VERSION\)", re.MULTILINE
)
RUFF_REQUIREMENT_RE = re.compile(r'"ruff==(?P<version>[^"]+)"')
# A recipe reaching for ruff or ty other than through `$(RUFF)` or `$(TY)`:
# either from `PATH`, or through an unversioned `uv tool run`. The `\b` after
# the tool name matters, or `ty` also matches inside `typos@$(TYPOS_VERSION)`.
UNPINNED_INVOCATION_RE = re.compile(
    rf"^\t@?(?:ruff|ty)\b|^\t@?.*{UV_COMMAND} tool run (?:ruff|ty)\b(?!@)",
    re.MULTILINE,
)


class Install(typ.NamedTuple):
    """One package argument of one install command in the workflow."""

    command: str
    package: str
    resolved: str


def _string_mapping(value: object) -> dict[str, str]:
    """Read an `env:` mapping, keeping only the entries with string values."""
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items() if isinstance(item, str)}


def _steps() -> cabc.Iterator[tuple[str, dict[str, str]]]:
    """Yield each `run:` script with the environment visible to it.

    A version written as `${VAR}` means nothing without the value behind it, so
    the workflow, job and step `env` mappings are merged in that order of
    increasing precedence and carried alongside the script.
    """
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert isinstance(workflow, dict), "the workflow must be a mapping"
    workflow_env = _string_mapping(workflow.get("env"))
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "the workflow must declare a jobs mapping"

    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        job_env = workflow_env | _string_mapping(job.get("env"))
        for step in job.get("steps", []):
            if isinstance(step, dict) and isinstance(step.get("run"), str):
                yield step["run"], job_env | _string_mapping(step.get("env"))


def _resolve(text: str, environment: dict[str, str]) -> str:
    """Substitute every `${VAR}` in ``text`` with the value the step gives it.

    An unresolved variable becomes a marker rather than a plausible version, so
    a misspelt or undefined name fails a pin assertion instead of passing it.
    """

    def substitute(match: re.Match[str]) -> str:
        return environment.get(match.group("name"), "<undefined>")

    return SHELL_VARIABLE.sub(substitute, text)


def _installs() -> list[Install]:
    """Collect every package argument of every package-manager install."""
    found: list[Install] = []
    for script, environment in _steps():
        for pattern in INSTALL_PATTERNS:
            for match in pattern.finditer(script):
                command = match.group(0).strip()
                for argument in match.group("arguments").split():
                    # A `-flag` is not a package, and a lone backslash is the
                    # shell's line continuation rather than something installed.
                    if argument.startswith("-") or argument == "\\":
                        continue
                    package = argument.strip("\"'")
                    found.append(
                        Install(command, package, _resolve(package, environment))
                    )
    return found


def _cargo_installs() -> list[tuple[str, str]]:
    """Collect every `cargo install` command, with its resolved text."""
    return [
        (match.group(0).strip(), _resolve(match.group(0).strip(), environment))
        for script, environment in _steps()
        for match in CARGO_INSTALL.finditer(script)
    ]


def _cargo_version(command: str) -> str | None:
    """Read the value of a `cargo install` command's `--version` argument."""
    arguments = command.split()
    for index, argument in enumerate(arguments):
        if argument == "--version" and index + 1 < len(arguments):
            return arguments[index + 1].strip("\"'")
        if argument.startswith("--version="):
            return argument.partition("=")[2].strip("\"'")
    return None


INSTALLS = _installs()
CARGO_INSTALLS = _cargo_installs()


def test_the_workflow_installs_tools_at_all() -> None:
    """Guard the patterns: one that matches nothing would prove nothing."""
    assert INSTALLS


@pytest.mark.parametrize(
    "install", INSTALLS, ids=lambda install: install.package.strip("\"'")
)
def test_every_installed_tool_names_an_exact_version(install: Install) -> None:
    """Check the value behind the variable is a version, not a moving tag.

    Parameters
    ----------
    install : Install
        One install command, its package argument, and the argument with every
        `${VAR}` replaced by the value the step's environment gives it.

    """
    assert PINNED.match(install.resolved), (
        f"{install.command!r} installs {install.package!r}, "
        f"which resolves to {install.resolved!r}"
    )


@pytest.mark.parametrize(
    "selector",
    [
        "markdownlint-cli2@latest",
        "markdownlint-cli2@^0.23",
        "markdownlint-cli2@~0.23.0",
        "mbake==1.*",
        "mbake>=1.4.6",
        "mbake==<undefined>",
        "mbake",
    ],
    ids=["latest", "caret", "tilde", "wildcard", "lower-bound", "undefined", "bare"],
)
def test_the_pin_assertion_rejects_anything_but_one_version(selector: str) -> None:
    """Check every way of not pinning fails.

    Parameters
    ----------
    selector : str
        A resolved selector naming something other than one version.

    """
    assert not PINNED.match(selector)


@pytest.mark.parametrize(
    "selector",
    ["mbake==1.4.6", "markdownlint-cli2@0.23.2", "nixie-cli==1.1.0", "ty==0.0.78"],
    ids=["pypi", "npm", "pypi-two-component", "three-component"],
)
def test_the_pin_assertion_accepts_an_exact_version(selector: str) -> None:
    """Check the shapes the workflow actually uses still pass.

    Parameters
    ----------
    selector : str
        A resolved selector naming exactly one version.

    """
    assert PINNED.match(selector)


def test_an_undefined_variable_does_not_resolve_to_a_version() -> None:
    """Check a misspelt variable name fails rather than looking pinned."""
    assert _resolve("mbake==${TYPO}", {"MBAKE_VERSION": "1.4.6"}) == (
        "mbake==<undefined>"
    )
    assert _resolve("mbake==${MBAKE_VERSION}", {"MBAKE_VERSION": "1.4.6"}) == (
        "mbake==1.4.6"
    )


def test_the_workflow_installs_a_crate() -> None:
    """Guard the cargo pattern: merman-cli is installed by `cargo install`."""
    assert CARGO_INSTALLS


@pytest.mark.parametrize(
    ("command", "resolved"), CARGO_INSTALLS, ids=lambda value: value.split()[-1]
)
def test_every_cargo_install_names_an_exact_version(
    command: str, resolved: str
) -> None:
    """Check a crate installed in CI is pinned like every other tool.

    Parameters
    ----------
    command : str
        The command as written in the workflow, for the message.
    resolved : str
        The same command with every `${VAR}` replaced.

    """
    version = _cargo_version(resolved)

    assert version is not None, f"{command!r} names no --version"
    assert CARGO_VERSION.match(version), (
        f"{command!r} installs at version {version!r}, which is not exact"
    )


@pytest.mark.parametrize(
    ("command", "version"),
    [
        ("cargo +1.95.0 install merman-cli --locked", None),
        ("cargo install merman-cli --version '=0.7.0' --locked", "=0.7.0"),
        ("cargo install merman-cli --version 0.7.0", "0.7.0"),
        ("cargo install merman-cli --version=0.7.0", "0.7.0"),
    ],
    ids=["no-version", "equals-prefixed", "bare", "joined"],
)
def test_the_cargo_version_is_read_from_every_argument_form(
    command: str, version: str | None
) -> None:
    """Check dropping `--version` is visible to the reader.

    Parameters
    ----------
    command : str
        A candidate `cargo install` command.
    version : str | None
        The version the reader should find, or None when there is none.

    """
    assert _cargo_version(command) == version


@pytest.mark.parametrize(
    "version",
    ["^0.7", "*", ">=0.7.0", "<undefined>"],
    ids=["caret", "wildcard", "lower-bound", "undefined"],
)
def test_the_cargo_assertion_rejects_a_range(version: str) -> None:
    """Check `--version '^0.7'` counts as a range, not a pin.

    Parameters
    ----------
    version : str
        A `--version` argument naming more than one release.

    """
    assert not CARGO_VERSION.match(version)


@pytest.mark.parametrize(
    ("name", "pattern"),
    [("RUFF_VERSION", RUFF_VERSION_RE), ("TY_VERSION", TY_VERSION_RE)],
    ids=["ruff", "ty"],
)
def test_the_makefile_pins_the_linter_to_an_exact_version(
    name: str, pattern: re.Pattern[str]
) -> None:
    """Check each version variable names one release.

    Parameters
    ----------
    name : str
        The Makefile variable, for the message.
    pattern : re.Pattern[str]
        The pattern that reads it.

    """
    match = pattern.search(MAKEFILE_PATH.read_text(encoding="utf-8"))

    assert match is not None, f"{name} is not pinned in the Makefile"
    assert re.fullmatch(r"\d+\.\d+\.\d+", match.group("version")), (
        f"{name} must be an exact version, got {match.group('version')!r}"
    )


@pytest.mark.parametrize(
    ("name", "pattern"),
    [("RUFF", RUFF_DEFINITION_RE), ("TY", TY_DEFINITION_RE)],
    ids=["ruff", "ty"],
)
def test_the_variable_invokes_the_pinned_release(
    name: str, pattern: re.Pattern[str]
) -> None:
    """Check `$(RUFF)` and `$(TY)` expand to the pin.

    Without this, redefining `RUFF = ruff` restores the PATH-dependent
    behaviour while every recipe, the version variable and the project
    requirement stay untouched, so every other assertion here still passes.

    Parameters
    ----------
    name : str
        The Makefile variable, for the message.
    pattern : re.Pattern[str]
        The pattern that reads its definition.

    """
    assert pattern.search(MAKEFILE_PATH.read_text(encoding="utf-8")), (
        f"{name} must be defined as `uv tool run <tool>@$({name}_VERSION)`"
    )


def test_no_recipe_reaches_for_an_unpinned_linter() -> None:
    """Check no recipe uses `PATH` or an unversioned `uv tool run`."""
    assert not UNPINNED_INVOCATION_RE.search(MAKEFILE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("recipe", "unpinned"),
    [
        ("check-fmt:\n\truff format --check\n", True),
        ("typecheck:\n\tty check\n", True),
        ("check-fmt:\n\t$(UV) tool run ruff format\n", True),
        ("typecheck:\n\t@$(UV) tool run ty check\n", True),
        ("check-fmt:\n\t$(UV) tool run ruff@0.15.20 format\n", False),
        ("spelling:\n\t$(UV) tool run typos@$(TYPOS_VERSION) --config x\n", False),
        ("check-fmt:\n\t$(RUFF) format --check\n", False),
        ("typecheck:\n\t$(TY) check\n", False),
    ],
    ids=[
        "bare-ruff",
        "bare-ty",
        "unversioned-uv-run-ruff",
        "unversioned-uv-run-ty",
        "versioned-uv-run",
        "typos-is-not-ty",
        "ruff-variable",
        "ty-variable",
    ],
)
def test_the_invocation_assertion_rejects_every_unpinned_form(
    recipe: str, *, unpinned: bool
) -> None:
    """Check each unpinned recipe shape is caught and each pinned one is not.

    Parameters
    ----------
    recipe : str
        A candidate Makefile recipe.
    unpinned : bool
        Whether the assertion should reject it.

    """
    assert bool(UNPINNED_INVOCATION_RE.search(recipe)) is unpinned


def test_the_project_requirement_matches_the_makefile_pin() -> None:
    """Check the virtual environment's ruff is the version the gates run.

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
