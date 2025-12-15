"""Pytest fixtures for simulacat GitHub API simulation.

This module provides pytest fixtures for configuring and running a local GitHub
API simulator. The primary fixture `github_sim_config` returns a JSON-serializable
mapping that can be overridden at function, module, or package scopes.

Example
-------
Override configuration at module scope::

    # conftest.py in a test module
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

import typing as typ

import pytest

from .config import default_github_sim_config

if typ.TYPE_CHECKING:
    from .types import GitHubSimConfig


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
    "github_sim_config",
]
