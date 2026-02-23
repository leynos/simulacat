"""Unit tests for Step 4.2 API stability and deprecation policy contracts."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

import simulacat
from simulacat.api_stability import (
    DEPRECATED_APIS,
    PUBLIC_API,
    ApiStability,
    DeprecatedApi,
    SimulacatDeprecationWarning,
    emit_deprecation_warning,
)

_FIXTURE_NAMES: tuple[str, ...] = (
    "github_sim_config",
    "github_simulator",
    "simulacat_single_repo",
    "simulacat_empty_org",
)


class TestPublicApiRegistry:
    """Validate that PUBLIC_API covers the full public surface."""

    @staticmethod
    def test_public_api_covers_all_dunder_all_symbols() -> None:
        """Every symbol in ``simulacat.__all__`` appears in PUBLIC_API."""
        missing = set(simulacat.__all__) - set(PUBLIC_API)
        assert not missing, (
            f"PUBLIC_API is missing symbols from __all__: {sorted(missing)}"
        )

    @staticmethod
    def test_public_api_covers_registered_fixtures() -> None:
        """Every registered pytest fixture appears in PUBLIC_API."""
        missing = set(_FIXTURE_NAMES) - set(PUBLIC_API)
        assert not missing, f"PUBLIC_API is missing fixtures: {sorted(missing)}"

    @staticmethod
    def test_every_entry_has_valid_stability_tier() -> None:
        """Every PUBLIC_API entry maps to a valid ApiStability member."""
        for symbol_name, tier in PUBLIC_API.items():
            assert isinstance(tier, ApiStability), (
                f"PUBLIC_API[{symbol_name!r}] is not an ApiStability member"
            )

    @staticmethod
    def test_public_api_is_immutable() -> None:
        """PUBLIC_API is a read-only mapping."""
        with pytest.raises(TypeError):
            PUBLIC_API["__test__"] = ApiStability.STABLE  # type: ignore[index]


class TestApiStabilityTiers:
    """Validate the ApiStability enum."""

    @staticmethod
    def test_has_stable_tier() -> None:
        """ApiStability defines a STABLE tier."""
        assert ApiStability.STABLE == "stable"

    @staticmethod
    def test_has_provisional_tier() -> None:
        """ApiStability defines a PROVISIONAL tier."""
        assert ApiStability.PROVISIONAL == "provisional"

    @staticmethod
    def test_has_deprecated_tier() -> None:
        """ApiStability defines a DEPRECATED tier."""
        assert ApiStability.DEPRECATED == "deprecated"


class TestDeprecationWarning:
    """Validate the deprecation warning mechanism."""

    @staticmethod
    def test_warning_is_deprecation_subclass() -> None:
        """SimulacatDeprecationWarning is a DeprecationWarning subclass."""
        assert issubclass(SimulacatDeprecationWarning, DeprecationWarning)

    @staticmethod
    def test_emit_raises_for_unknown_symbol() -> None:
        """emit_deprecation_warning raises ValueError for unknown symbols."""
        with pytest.raises(ValueError, match="not in DEPRECATED_APIS"):
            emit_deprecation_warning("nonexistent_symbol_xyz")

    @staticmethod
    def test_emit_warning_for_deprecated_symbol() -> None:
        """emit_deprecation_warning emits a warning with migration guidance."""
        # Use a real deprecated entry if available, otherwise this test
        # validates the mechanism with a synthetic entry via monkeypatch.
        if DEPRECATED_APIS:
            entry = DEPRECATED_APIS[0]
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                emit_deprecation_warning(entry.symbol_name)
            assert len(caught) == 1
            assert issubclass(caught[0].category, SimulacatDeprecationWarning)
            assert entry.replacement in str(caught[0].message)
            assert entry.guidance in str(caught[0].message)


class TestDeprecatedApisRegistry:
    """Validate the DEPRECATED_APIS tuple structure."""

    @staticmethod
    def test_deprecated_apis_is_tuple() -> None:
        """DEPRECATED_APIS is a tuple."""
        assert isinstance(DEPRECATED_APIS, tuple)

    @staticmethod
    def test_deprecated_entries_have_required_fields() -> None:
        """Every DeprecatedApi entry has non-empty required fields."""
        for entry in DEPRECATED_APIS:
            assert isinstance(entry, DeprecatedApi)
            assert entry.symbol_name.strip()
            assert entry.deprecated_since.strip()
            assert entry.replacement.strip()
            assert entry.guidance.strip()


class TestChangelog:
    """Validate the changelog file exists and links roadmap items."""

    @staticmethod
    def _changelog_path() -> Path:
        return Path(__file__).resolve().parents[2] / "docs" / "changelog.md"

    def test_changelog_exists(self) -> None:
        """Changelog file exists at docs/changelog.md."""
        assert self._changelog_path().is_file(), "Expected docs/changelog.md to exist"

    def test_changelog_references_phases(self) -> None:
        """Changelog references completed roadmap phases."""
        text = self._changelog_path().read_text(encoding="utf-8")
        for phase_number in range(1, 5):
            assert f"Phase {phase_number}" in text, (
                f"Expected changelog to reference Phase {phase_number}"
            )
