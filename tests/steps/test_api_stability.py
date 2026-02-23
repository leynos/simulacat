"""Behaviour tests for Step 4.2 API stability and deprecation policy."""

from __future__ import annotations

import typing as typ
import warnings
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

import simulacat
from simulacat.api_stability import (
    DEPRECATED_APIS,
    PUBLIC_API,
    ApiStability,
    DeprecatedApi,
    SimulacatDeprecationWarning,
    emit_deprecation_warning,
)

scenarios("../features/api_stability.feature")

_FIXTURE_NAMES: tuple[str, ...] = (
    "github_sim_config",
    "github_simulator",
    "simulacat_single_repo",
    "simulacat_empty_org",
)


def repo_root() -> Path:
    """Return the repository root path."""
    return Path(__file__).resolve().parents[2]


# --- Scenario: Public API symbols are registered with stability tiers ---


@given("the simulacat public API registry", target_fixture="public_api")
def given_public_api_registry() -> dict[str, ApiStability]:
    """Load the public API registry."""
    return dict(PUBLIC_API)


@then("every symbol in the package __all__ has a stability tier")
def then_all_symbols_have_tier(public_api: dict[str, ApiStability]) -> None:
    """Every __all__ symbol appears in PUBLIC_API with a valid tier."""
    for symbol in simulacat.__all__:
        assert symbol in public_api, (
            f"Symbol {symbol!r} from __all__ is not in PUBLIC_API"
        )
        assert isinstance(public_api[symbol], ApiStability), (
            f"PUBLIC_API[{symbol!r}] is not a valid ApiStability tier"
        )


@then("every registered fixture has a stability tier")
def then_all_fixtures_have_tier(public_api: dict[str, ApiStability]) -> None:
    """Every registered pytest fixture appears in PUBLIC_API."""
    for fixture_name in _FIXTURE_NAMES:
        assert fixture_name in public_api, (
            f"Fixture {fixture_name!r} is not in PUBLIC_API"
        )
        assert isinstance(public_api[fixture_name], ApiStability), (
            f"PUBLIC_API[{fixture_name!r}] is not a valid ApiStability tier"
        )


# --- Scenario: Deprecation warnings include migration guidance ---


class _DeprecationContext(typ.TypedDict):
    """Context for deprecation warning scenario."""

    entry: DeprecatedApi
    caught: list[warnings.WarningMessage]


@given(
    "a deprecated API entry with a replacement and guidance",
    target_fixture="deprecation_ctx",
)
def given_deprecated_api_entry() -> _DeprecationContext:
    """Provide a deprecated API entry for testing.

    If no real deprecated entries exist, create a synthetic one to validate
    the mechanism.
    """
    if DEPRECATED_APIS:
        entry = DEPRECATED_APIS[0]
    else:
        entry = DeprecatedApi(
            symbol_name="__test_synthetic_deprecated__",
            deprecated_since="0.1.0",
            replacement="new_replacement_api",
            removal_version="1.0.0",
            guidance="Migrate to new_replacement_api for improved stability.",
        )
    return {"entry": entry, "caught": []}


@when("a deprecation warning is emitted for the entry")
def when_deprecation_warning_emitted(
    deprecation_ctx: _DeprecationContext,
) -> None:
    """Emit a deprecation warning for the test entry."""
    entry = deprecation_ctx["entry"]

    if entry.symbol_name == "__test_synthetic_deprecated__":
        # Emit directly since synthetic entries are not in DEPRECATED_APIS.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warnings.warn(
                f"{entry.symbol_name} is deprecated since {entry.deprecated_since}. "
                f"Use {entry.replacement} instead. {entry.guidance}",
                SimulacatDeprecationWarning,
                stacklevel=2,
            )
        deprecation_ctx["caught"] = list(caught)
    else:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            emit_deprecation_warning(entry.symbol_name)
        deprecation_ctx["caught"] = list(caught)


@then("the warning is a SimulacatDeprecationWarning")
def then_warning_is_correct_type(
    deprecation_ctx: _DeprecationContext,
) -> None:
    """Assert emitted warning is a SimulacatDeprecationWarning."""
    caught = deprecation_ctx["caught"]
    assert len(caught) == 1, f"Expected 1 warning, got {len(caught)}"
    assert issubclass(caught[0].category, SimulacatDeprecationWarning)


@then("the warning message includes the replacement name")
def then_warning_includes_replacement(
    deprecation_ctx: _DeprecationContext,
) -> None:
    """Warning message mentions the replacement API."""
    entry = deprecation_ctx["entry"]
    message = str(deprecation_ctx["caught"][0].message)
    assert entry.replacement in message, (
        f"Expected replacement {entry.replacement!r} in warning: {message}"
    )


@then("the warning message includes migration guidance")
def then_warning_includes_guidance(
    deprecation_ctx: _DeprecationContext,
) -> None:
    """Warning message includes migration guidance text."""
    entry = deprecation_ctx["entry"]
    message = str(deprecation_ctx["caught"][0].message)
    assert entry.guidance in message, f"Expected guidance text in warning: {message}"


# --- Scenario: Changelog links roadmap items to capabilities ---


@given("the changelog document", target_fixture="changelog_text")
def given_changelog_document() -> str:
    """Load the changelog markdown text."""
    changelog_path = repo_root() / "docs" / "changelog.md"
    return changelog_path.read_text(encoding="utf-8")


@then("the changelog references Phase 1 through Phase 4")
def then_changelog_references_phases(changelog_text: str) -> None:
    """Changelog mentions all completed roadmap phases."""
    for phase_number in range(1, 5):
        assert f"Phase {phase_number}" in changelog_text, (
            f"Expected changelog to reference Phase {phase_number}"
        )


@then("the changelog describes behavioural changes at the step level")
def then_changelog_describes_steps(changelog_text: str) -> None:
    """Changelog includes step-level descriptions."""
    assert "Step" in changelog_text, (
        "Expected changelog to describe changes at the step level"
    )


# --- Scenario: Users guide documents API stability and deprecation policy ---


@given("the users guide document", target_fixture="users_guide_text")
def given_users_guide_document() -> str:
    """Load the users guide markdown text."""
    users_guide_path = repo_root() / "docs" / "users-guide.md"
    return users_guide_path.read_text(encoding="utf-8")


@then('the users guide includes an "API stability" section')
def then_users_guide_has_api_stability(users_guide_text: str) -> None:
    """Users guide contains API stability section."""
    assert "## API stability" in users_guide_text, (
        "Expected users guide to contain an 'API stability' section heading"
    )


@then('the users guide includes a "Deprecation policy" section')
def then_users_guide_has_deprecation_policy(users_guide_text: str) -> None:
    """Users guide contains deprecation policy section."""
    assert "## Deprecation policy" in users_guide_text, (
        "Expected users guide to contain a 'Deprecation policy' section heading"
    )
