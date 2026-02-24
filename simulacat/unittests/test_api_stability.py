"""Unit tests for Step 4.2 API stability and deprecation policy contracts."""

from __future__ import annotations

import warnings
from pathlib import Path
from types import MappingProxyType

import pytest

import simulacat
from simulacat.api_stability import (
    DEPRECATED_APIS,
    FIXTURE_NAMES,
    PUBLIC_API,
    ApiStability,
    DeprecatedApi,
    SimulacatDeprecationWarning,
    emit_deprecation_warning,
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
        missing = set(FIXTURE_NAMES) - set(PUBLIC_API)
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
    @pytest.mark.parametrize(
        ("member", "expected_value"),
        [
            (ApiStability.STABLE, "stable"),
            (ApiStability.PROVISIONAL, "provisional"),
            (ApiStability.DEPRECATED, "deprecated"),
        ],
    )
    def test_tier_has_expected_value(
        member: ApiStability,
        expected_value: str,
    ) -> None:
        """ApiStability members have the expected string values."""
        assert member == expected_value, (
            f"{member.name} should be {expected_value!r}, got {member.value!r}"
        )


class TestDeprecationWarning:
    """Validate the deprecation warning mechanism."""

    @staticmethod
    def test_warning_is_deprecation_subclass() -> None:
        """SimulacatDeprecationWarning is a DeprecationWarning subclass."""
        assert issubclass(SimulacatDeprecationWarning, DeprecationWarning), (
            "SimulacatDeprecationWarning must be a DeprecationWarning subclass"
        )

    @staticmethod
    def test_emit_raises_for_unknown_symbol() -> None:
        """emit_deprecation_warning raises ValueError for unknown symbols."""
        with pytest.raises(ValueError, match="not in DEPRECATED_APIS"):
            emit_deprecation_warning("nonexistent_symbol_xyz")

    @staticmethod
    def test_emit_warning_for_deprecated_symbol(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """emit_deprecation_warning emits a warning with migration guidance."""
        entry = DeprecatedApi(
            symbol_name="__test_old_api__",
            deprecated_since="0.1.0",
            replacement="new_api",
            removal_version="1.0.0",
            guidance="Migrate to new_api for improved stability.",
        )
        patched = MappingProxyType({entry.symbol_name: entry})
        monkeypatch.setattr("simulacat.api_stability.DEPRECATED_APIS", patched)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            emit_deprecation_warning(entry.symbol_name)

        assert len(caught) == 1, f"Expected 1 warning, got {len(caught)}"
        assert issubclass(caught[0].category, SimulacatDeprecationWarning), (
            f"Expected SimulacatDeprecationWarning, got {caught[0].category}"
        )
        message = str(caught[0].message)
        assert entry.replacement in message, (
            f"Warning should mention replacement {entry.replacement!r}"
        )
        assert entry.guidance in message, (
            f"Warning should include guidance {entry.guidance!r}"
        )
        assert entry.removal_version in message, (
            f"Warning should include removal version {entry.removal_version!r}"
        )


class TestDeprecatedApisRegistry:
    """Validate the DEPRECATED_APIS mapping structure."""

    @staticmethod
    def test_deprecated_apis_is_mapping() -> None:
        """DEPRECATED_APIS is a mapping."""
        assert isinstance(DEPRECATED_APIS, MappingProxyType), (
            "DEPRECATED_APIS must be a MappingProxyType"
        )

    @staticmethod
    def test_deprecated_entries_have_required_fields() -> None:
        """Every DeprecatedApi entry has non-empty required fields."""
        for entry in DEPRECATED_APIS.values():
            assert isinstance(entry, DeprecatedApi), (
                f"Expected DeprecatedApi, got {type(entry)}"
            )
            assert entry.symbol_name.strip(), "symbol_name must not be empty"
            assert entry.deprecated_since.strip(), (
                f"{entry.symbol_name}: deprecated_since must not be empty"
            )
            assert entry.replacement.strip(), (
                f"{entry.symbol_name}: replacement must not be empty"
            )
            assert entry.guidance.strip(), (
                f"{entry.symbol_name}: guidance must not be empty"
            )


class TestChangelog:
    """Validate the changelog file exists and links roadmap items."""

    @staticmethod
    def _changelog_path() -> Path:
        return Path(__file__).resolve().parents[2] / "docs" / "changelog.md"

    @staticmethod
    def test_changelog_exists() -> None:
        """Changelog file exists at docs/changelog.md."""
        assert TestChangelog._changelog_path().is_file(), (
            "Expected docs/changelog.md to exist"
        )

    @staticmethod
    def test_changelog_references_phases() -> None:
        """Changelog references completed roadmap phases."""
        text = TestChangelog._changelog_path().read_text(encoding="utf-8")
        for phase_number in range(1, 5):
            assert f"Phase {phase_number}" in text, (
                f"Expected changelog to reference Phase {phase_number}"
            )
