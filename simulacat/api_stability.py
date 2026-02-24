"""API stability tiers, public surface registry, and deprecation utilities.

This module is the canonical source of truth for which symbols and fixtures
are part of the supported simulacat API and at what stability tier. It also
provides a deprecation warning mechanism for communicating API changes to
downstream consumers.

Stability tiers
----------------
- **stable**: consumers may depend on the symbol. Changes follow the
  deprecation lifecycle.
- **provisional**: the symbol may change without the full deprecation
  lifecycle. Consumers are advised to pin versions.
- **deprecated**: the symbol will be removed in a future version. Warnings
  are emitted with migration guidance.

Deprecation lifecycle
---------------------
1. Introduce the replacement API alongside the old one.
2. Emit ``SimulacatDeprecationWarning`` with clear migration guidance.
3. Remove the deprecated API only after a documented transition period.
"""

from __future__ import annotations

import dataclasses as dc
import enum
import typing as typ
import warnings
from types import MappingProxyType

if typ.TYPE_CHECKING:
    import collections.abc as cabc


class ApiStability(enum.StrEnum):
    """Stability tier for a public API element.

    Attributes
    ----------
    STABLE
        Symbol is part of the supported API. Changes follow the deprecation
        lifecycle.
    PROVISIONAL
        Symbol may change without the full deprecation lifecycle. Consumers
        should pin versions.
    DEPRECATED
        Symbol will be removed in a future version. Warnings are emitted
        with migration guidance.

    """

    STABLE = "stable"
    PROVISIONAL = "provisional"
    DEPRECATED = "deprecated"


@dc.dataclass(frozen=True, slots=True)
class DeprecatedApi:
    """Record of a deprecated API element.

    Attributes
    ----------
    symbol_name
        The name of the deprecated symbol or fixture.
    deprecated_since
        Version string when the deprecation was introduced.
    replacement
        Name of the replacement symbol or fixture.
    removal_version
        Version string when the deprecated symbol will be removed.
    guidance
        Migration guidance for consumers.

    """

    symbol_name: str
    deprecated_since: str
    replacement: str
    removal_version: str
    guidance: str


class SimulacatDeprecationWarning(DeprecationWarning):
    """Warning emitted when a deprecated simulacat API element is used.

    Consumers can filter these warnings independently of other library
    deprecation warnings using the standard ``warnings`` module::

        import warnings
        from simulacat.api_stability import SimulacatDeprecationWarning

        warnings.filterwarnings("error", category=SimulacatDeprecationWarning)
    """


# -- Public API registry ------------------------------------------------------
#
# Every symbol in ``simulacat.__all__`` and every registered pytest fixture
# must appear here. Unit tests enforce coverage so drift is caught by CI.

PUBLIC_API: cabc.Mapping[str, ApiStability] = MappingProxyType({
    # Configuration helpers
    "default_github_sim_config": ApiStability.STABLE,
    "is_json_serializable": ApiStability.STABLE,
    "merge_configs": ApiStability.STABLE,
    # Scenario models
    "AccessToken": ApiStability.STABLE,
    "AppInstallation": ApiStability.STABLE,
    "Branch": ApiStability.STABLE,
    "ConfigValidationError": ApiStability.STABLE,
    "DefaultBranch": ApiStability.STABLE,
    "GitHubApp": ApiStability.STABLE,
    "Issue": ApiStability.STABLE,
    "Organization": ApiStability.STABLE,
    "PullRequest": ApiStability.STABLE,
    "Repository": ApiStability.STABLE,
    "ScenarioConfig": ApiStability.STABLE,
    "User": ApiStability.STABLE,
    # Scenario factories
    "empty_org_scenario": ApiStability.STABLE,
    "github_app_scenario": ApiStability.STABLE,
    "merge_scenarios": ApiStability.STABLE,
    "monorepo_with_apps_scenario": ApiStability.STABLE,
    "single_repo_scenario": ApiStability.STABLE,
    # Types
    "GitHubSimConfig": ApiStability.STABLE,
    # API stability (self-referential)
    "ApiStability": ApiStability.STABLE,
    "SimulacatDeprecationWarning": ApiStability.STABLE,
    "PUBLIC_API": ApiStability.STABLE,
    # pytest fixtures (registered via pytest11 entry point)
    "github_sim_config": ApiStability.STABLE,
    "github_simulator": ApiStability.STABLE,
    "simulacat_single_repo": ApiStability.STABLE,
    "simulacat_empty_org": ApiStability.STABLE,
})

FIXTURE_NAMES: tuple[str, ...] = (
    "github_sim_config",
    "github_simulator",
    "simulacat_single_repo",
    "simulacat_empty_org",
)


# -- Deprecated APIs ----------------------------------------------------------
#
# Currently empty. When a symbol is deprecated, add a DeprecatedApi entry
# here and change its PUBLIC_API tier to ApiStability.DEPRECATED.

DEPRECATED_APIS: cabc.Mapping[str, DeprecatedApi] = MappingProxyType({})


def emit_deprecation_warning(symbol_name: str) -> None:
    """Emit a deprecation warning for the named symbol.

    Parameters
    ----------
    symbol_name
        The name of the deprecated symbol. Must be present in
        ``DEPRECATED_APIS``.

    Raises
    ------
    ValueError
        If ``symbol_name`` is not in ``DEPRECATED_APIS``.

    """
    entry = DEPRECATED_APIS.get(symbol_name)
    if entry is None:
        msg = f"{symbol_name!r} is not in DEPRECATED_APIS"
        raise ValueError(msg)

    # stacklevel=2 points the warning at the direct caller's frame.
    # If this function is wrapped by another helper, the wrapper must
    # increase the stacklevel accordingly.
    warnings.warn(
        f"{entry.symbol_name} is deprecated since {entry.deprecated_since} "
        f"and will be removed in {entry.removal_version}. "
        f"Use {entry.replacement} instead. {entry.guidance.strip()}",
        SimulacatDeprecationWarning,
        stacklevel=2,
    )
