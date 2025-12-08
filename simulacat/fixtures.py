"""Pytest fixtures for simulacat GitHub API simulation.

This module provides pytest fixtures for configuring and running a local GitHub
API simulator. The primary fixture `github_sim_config` returns a JSON-serializable
mapping that can be overridden at function, module, or package scopes.

Example:
-------
Override configuration at module scope::

    # conftest.py in your test module
    import pytest

    @pytest.fixture
    def github_sim_config():
        return {
            "users": [{"login": "testuser", "organizations": []}],
            "organizations": [],
            "repositories": [],
            "branches": [],
            "blobs": [],
        }

Override at function scope::

    @pytest.fixture
    def github_sim_config():
        return {"users": [{"login": "function-user", "organizations": []}]}

    def test_with_custom_config(github_sim_config):
        assert github_sim_config["users"][0]["login"] == "function-user"

"""

from __future__ import annotations

import json
import typing as typ

import pytest

if typ.TYPE_CHECKING:
    import collections.abc as cabc

# Type alias for simulator configuration
GitHubSimConfig: typ.TypeAlias = dict[str, typ.Any]


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
    package, module, and function-level configuration overrides.

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


@pytest.fixture
def github_sim_config() -> GitHubSimConfig:
    """Provide simulator configuration for tests.

    This fixture returns a JSON-serializable mapping that configures the
    GitHub API simulator. Override this fixture at function, module, or
    package scope to customize the simulator's initial state.

    Returns
    -------
    GitHubSimConfig
        A dictionary containing simulator configuration. The default is
        an empty mapping.

    Example
    -------
    Override at module level in conftest.py::

        @pytest.fixture
        def github_sim_config():
            return {
                "users": [{"login": "testuser", "organizations": []}],
                "organizations": [],
                "repositories": [{"owner": "testuser", "name": "my-repo"}],
                "branches": [],
                "blobs": [],
            }

    """
    return default_github_sim_config()


__all__ = [
    "GitHubSimConfig",
    "default_github_sim_config",
    "github_sim_config",
    "is_json_serializable",
    "merge_configs",
]
