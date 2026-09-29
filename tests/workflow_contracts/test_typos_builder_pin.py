"""Contract tests for the `typos-config-builder` pin in the Makefile.

`make spelling` runs the shared gate through `uv tool run --from <git url>`. A
moving ref there (`main`, `latest`) or a recipe that bypasses the definition
would let CI execute different code with no change in this repository, and no
other assertion would notice: the version variable, the recipe and the gate
would all still read plausibly.

The assertions read the `Makefile` text through small predicates so that each
one can be run against a mutated definition as well as the real file.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

MAKEFILE_PATH = Path(__file__).resolve().parents[2] / "Makefile"

# A release tag in the estate's `vMAJOR.MINOR.PATCH` form. `main`, `latest` and
# a branch name are moving refs, so none of them matches.
VERSION_RE = re.compile(
    r"^TYPOS_CONFIG_BUILDER_VERSION \?= v\d+\.\d+\.\d+$", re.MULTILINE
)
# The definition must interpolate the version variable into the git URL's ref;
# a hard-coded ref would leave the variable pinned and the invocation not.
DEFINITION_RE = re.compile(
    r"^TYPOS_CONFIG_BUILDER = .*--from \\\n"
    r'\t"git\+https://github\.com/leynos/typos-config-builder\.git'
    r'@\$\(TYPOS_CONFIG_BUILDER_VERSION\)" \\\n'
    r"\ttypos-config-builder$",
    re.MULTILINE,
)
# The recipe must go through the variable, not a bare `uv tool run`, and must
# end there: a further tab-prefixed line would run after the gate unchecked.
RECIPE_RE = re.compile(
    r"^spelling:.*\n\t\$\(TYPOS_CONFIG_BUILDER\) gate --repository \."
    r"(?:\n(?!\t)|\Z)",
    re.MULTILINE,
)

PINNED_DEFINITION = (
    "TYPOS_CONFIG_BUILDER = $(UV) tool run --python 3.14 --from \\\n"
    '\t"git+https://github.com/leynos/typos-config-builder.git'
    '@$(TYPOS_CONFIG_BUILDER_VERSION)" \\\n'
    "\ttypos-config-builder\n"
)


def _makefile() -> str:
    """Return the Makefile text."""
    return MAKEFILE_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("line", "is_pinned"),
    [
        ("TYPOS_CONFIG_BUILDER_VERSION ?= v0.1.3\n", True),
        ("TYPOS_CONFIG_BUILDER_VERSION ?= v10.20.30\n", True),
        ("TYPOS_CONFIG_BUILDER_VERSION ?= main\n", False),
        ("TYPOS_CONFIG_BUILDER_VERSION ?= latest\n", False),
        ("TYPOS_CONFIG_BUILDER_VERSION ?= v0.1\n", False),
        ("TYPOS_CONFIG_BUILDER_VERSION ?=\n", False),
    ],
    ids=["release", "multi-digit", "branch", "latest", "partial", "empty"],
)
def test_the_version_predicate_accepts_only_a_release_tag(
    line: str, *, is_pinned: bool
) -> None:
    """Check the version pattern rejects every moving or partial ref."""
    assert bool(VERSION_RE.search(line)) is is_pinned


@pytest.mark.parametrize(
    ("text", "is_pinned"),
    [
        (PINNED_DEFINITION, True),
        (PINNED_DEFINITION.replace("$(TYPOS_CONFIG_BUILDER_VERSION)", "main"), False),
        (PINNED_DEFINITION.replace("$(TYPOS_CONFIG_BUILDER_VERSION)", "v0.1.3"), False),
        (PINNED_DEFINITION.replace("@$(TYPOS_CONFIG_BUILDER_VERSION)", ""), False),
    ],
    ids=["interpolated", "branch-ref", "hard-coded-tag", "no-ref"],
)
def test_the_definition_predicate_requires_the_version_variable(
    text: str, *, is_pinned: bool
) -> None:
    """Check the definition pattern rejects a ref that bypasses the variable."""
    assert bool(DEFINITION_RE.search(text)) is is_pinned


@pytest.mark.parametrize(
    ("text", "goes_through_variable"),
    [
        ("spelling: ## x\n\t$(TYPOS_CONFIG_BUILDER) gate --repository .\n", True),
        (
            "spelling: ## x\n\tuv tool run typos-config-builder gate --repository .\n",
            False,
        ),
        (
            "spelling: ## x\n\t$(TYPOS_CONFIG_BUILDER) gate --repository . --check\n",
            False,
        ),
        (
            (
                "spelling: ## x\n\t$(TYPOS_CONFIG_BUILDER) gate --repository .\n"
                "\tprintf 'extra command'\n"
            ),
            False,
        ),
        ("spelling: ## x\n\t$(TYPOS_CONFIG_BUILDER) gate --repository .", True),
        (
            "spelling: ## x\n\t$(TYPOS_CONFIG_BUILDER) gate --repository .\n\nnext:\n",
            True,
        ),
    ],
    ids=[
        "variable",
        "bare-uv-run",
        "extra-flag",
        "extra-recipe-line",
        "end-of-file",
        "next-rule",
    ],
)
def test_the_recipe_predicate_requires_the_pinned_variable(
    text: str, *, goes_through_variable: bool
) -> None:
    """Check the recipe pattern rejects a bypass of the pinned definition."""
    assert bool(RECIPE_RE.search(text)) is goes_through_variable


def test_the_makefile_pins_the_builder_to_a_release_tag() -> None:
    """Check `TYPOS_CONFIG_BUILDER_VERSION` names a release tag."""
    assert VERSION_RE.search(_makefile()), (
        "TYPOS_CONFIG_BUILDER_VERSION must be a vMAJOR.MINOR.PATCH release tag"
    )


def test_the_makefile_interpolates_the_pin_into_the_git_reference() -> None:
    """Check `TYPOS_CONFIG_BUILDER` installs the ref the variable names."""
    assert DEFINITION_RE.search(_makefile()), (
        "TYPOS_CONFIG_BUILDER must install "
        "`git+...typos-config-builder.git@$(TYPOS_CONFIG_BUILDER_VERSION)`"
    )


def test_the_spelling_recipe_runs_the_pinned_gate() -> None:
    """Check `make spelling` invokes the gate through the pinned variable."""
    assert RECIPE_RE.search(_makefile()), (
        "the spelling recipe must run `$(TYPOS_CONFIG_BUILDER) gate --repository .`"
    )
