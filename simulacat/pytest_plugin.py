"""Pytest plugin for simulacat.

The plugin exposes fixtures that let tests configure and interact with a local
GitHub API simulator.
"""

from __future__ import annotations

import json
import typing as typ

import pytest

from simulacat.types import GitHubSimConfig

if typ.TYPE_CHECKING:
    from pytest import FixtureRequest


@pytest.fixture
def github_sim_config(request: FixtureRequest) -> GitHubSimConfig:
    """Return configuration for the GitHub API simulator.

    The fixture defaults to an empty mapping. Tests can override it by defining
    a fixture with the same name in a test module or a `conftest.py`, or by
    parametrizing it indirectly:

    `@pytest.mark.parametrize("github_sim_config", [...], indirect=True)`

    Parameters
    ----------
    request
        The fixture request object, used for indirect parametrization.

    Returns
    -------
    GitHubSimConfig
        A JSON-serializable configuration mapping.

    Raises
    ------
    TypeError
        If the provided configuration is not a mapping or cannot be serialized
        to JSON.
    """
    raw_config: object = getattr(request, "param", {})
    if raw_config is None:
        raw_config = {}

    if not isinstance(raw_config, dict):
        msg = "github_sim_config must be a mapping"
        raise TypeError(msg)

    try:
        json.dumps(raw_config)
    except (TypeError, ValueError) as exc:
        msg = "github_sim_config must be JSON serializable"
        raise TypeError(msg) from exc

    return typ.cast(GitHubSimConfig, raw_config)

