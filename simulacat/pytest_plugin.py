"""Pytest plugin for simulacat.

The plugin exposes fixtures that let tests configure and interact with a local
GitHub API simulator.
"""

from __future__ import annotations

import collections.abc as cabc
import json
import typing as typ

import pytest

if typ.TYPE_CHECKING:
    from simulacat.types import GitHubSimConfig


_REQUIRED_SIMULATOR_KEYS: tuple[str, ...] = (
    "users",
    "organizations",
    "repositories",
    "branches",
    "blobs",
)


@pytest.fixture
def github_sim_config(request: pytest.FixtureRequest) -> GitHubSimConfig:
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

    if not isinstance(raw_config, cabc.Mapping):
        msg = "github_sim_config must be a mapping"
        raise TypeError(msg)

    if not all(isinstance(key, str) for key in raw_config):
        msg = "github_sim_config keys must be strings"
        raise TypeError(msg)

    config: dict[str, object] = dict(raw_config)

    if config:
        for key in _REQUIRED_SIMULATOR_KEYS:
            if key not in config:
                config[key] = []
                continue

            value = config[key]
            if isinstance(value, list):
                continue

            msg = f"github_sim_config[{key!r}] must be a list"
            raise TypeError(msg)

    try:
        json.dumps(config)
    except (TypeError, ValueError) as exc:
        msg = "github_sim_config must be JSON serializable"
        raise TypeError(msg) from exc

    return typ.cast("GitHubSimConfig", config)
