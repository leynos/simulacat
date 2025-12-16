"""Pytest fixtures for simulacat GitHub API simulation.

This module provides pytest fixtures for configuring and running a local GitHub
API simulator. The primary fixture `github_sim_config` returns a JSON-serializable
mapping that can be overridden at function, module, or package scopes.

Note
----
The fixture is automatically registered as a pytest plugin via the
``pytest11`` entry point. You do not need to import this module directly;
pytest will discover and load the fixture automatically.

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


def __getattr__(name: str) -> typ.Any:  # noqa: ANN401
    """Lazily import pytest-dependent fixtures to avoid hard runtime dependency.

    This allows ``import simulacat.fixtures`` to succeed even when pytest is not
    installed, while still providing access to the fixture when pytest is available.
    """
    if name == "github_sim_config":
        from .pytest_plugin import github_sim_config

        return github_sim_config

    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


def __dir__() -> list[str]:
    """List available attributes including lazily-imported fixtures."""
    return ["github_sim_config"]


__all__ = [
    "github_sim_config",  # noqa: F822 - dynamically available via __getattr__
]
