"""Pytest plugin for simulacat.

The plugin exposes fixtures that let tests configure and interact with a local
GitHub API simulator.
"""

from __future__ import annotations

import collections.abc as cabc
import json
import os
import shutil
import typing as typ

import pytest

if typ.TYPE_CHECKING:
    import subprocess  # noqa: S404  # simulacat#123: typing-only; fixture doesn't spawn processes directly
    from pathlib import Path

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


def _is_bun_available() -> bool:
    """Return True if the configured Bun executable is available.

    The orchestration layer defaults to using the `BUN` environment variable
    and falls back to `bun` on PATH. The fixture mirrors that behaviour so
    missing Bun yields a clean skip rather than a subprocess failure.
    """
    bun_executable = os.environ.get("BUN", "bun")
    return shutil.which(bun_executable) is not None


@pytest.fixture
def github_simulator(
    github_sim_config: GitHubSimConfig,
    tmp_path: Path,
) -> typ.Generator[typ.Any, None, None]:
    """Provide a github3.py client connected to a running simulator."""
    if not _is_bun_available():
        pytest.skip("Bun is required for github_simulator fixture")

    try:
        import github3
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency is required
        msg = "github3.py is required for github_simulator fixture"
        raise RuntimeError(msg) from exc

    from simulacat.orchestration import start_sim_process, stop_sim_process

    proc: subprocess.Popen[str] | None = None
    try:
        proc, port = start_sim_process(github_sim_config, tmp_path)
        base_url = f"http://127.0.0.1:{port}"
        from github3.session import GitHubSession

        session = GitHubSession()
        session.base_url = base_url
        client = github3.GitHub(session=session)
        yield client
    finally:
        if proc is not None:
            stop_sim_process(proc)
