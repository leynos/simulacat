"""Configuration utilities for simulacat.

This module provides helper functions for working with GitHub API simulator
configurations. These utilities do not require pytest and can be used in any
Python context.
"""

from __future__ import annotations

import json
import typing as typ

if typ.TYPE_CHECKING:
    import collections.abc as cabc

    from .types import GitHubSimConfig


def default_github_sim_config() -> GitHubSimConfig:
    """Return the default simulator configuration.

    The default configuration is an empty mapping. The orchestration layer
    will expand this to a minimal valid state when starting the simulator.

    Returns
    -------
    GitHubSimConfig
        An empty dictionary that can be customized by overriding the
        github_sim_config fixture.

    """
    return {}


def is_json_serializable(value: object) -> bool:
    """Check if a value can be serialized to JSON.

    Parameters
    ----------
    value
        The value to check for JSON serializability.

    Returns
    -------
    bool
        True if the value can be serialized to JSON, False otherwise.

    """
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    else:
        return True


def merge_configs(*configs: cabc.Mapping[str, typ.Any]) -> GitHubSimConfig:
    """Merge multiple configuration mappings into one.

    Later configurations override earlier ones. This enables layering of
    package, module, and function-level configuration overrides. Note that
    merging is shallow: nested dictionaries are replaced entirely, not
    recursively merged.

    Parameters
    ----------
    *configs
        Variable number of configuration mappings to merge.

    Returns
    -------
    GitHubSimConfig
        A new dictionary containing the merged configuration.

    Example
    -------
    Merge base and override configurations::

        base = {"users": [{"login": "base"}], "organizations": []}
        override = {"users": [{"login": "override"}]}
        merged = merge_configs(base, override)
        # Result: {"users": [{"login": "override"}], "organizations": []}

    """
    result: GitHubSimConfig = {}
    for config in configs:
        result.update(config)
    return result


__all__ = [
    "default_github_sim_config",
    "is_json_serializable",
    "merge_configs",
]
