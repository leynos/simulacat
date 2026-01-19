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

from simulacat.scenario_config import ScenarioConfig

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
_SIMULACAT_METADATA_KEY = "__simulacat__"
_SIMULACAT_AUTH_TOKEN_KEY = "auth_token"  # noqa: S105


def _split_simulacat_config(
    config: cabc.Mapping[str, typ.Any],
) -> tuple[GitHubSimConfig, str | None]:
    """Return simulator config and optional auth token from metadata."""
    mutable_config: dict[str, typ.Any] = dict(config)
    auth_token: str | None = None
    raw_metadata = mutable_config.pop(_SIMULACAT_METADATA_KEY, None)
    if raw_metadata is None:
        return typ.cast("GitHubSimConfig", mutable_config), None

    if not isinstance(raw_metadata, cabc.Mapping):
        msg = f"{_SIMULACAT_METADATA_KEY} must be a mapping"
        raise TypeError(msg)

    raw_token = raw_metadata.get(_SIMULACAT_AUTH_TOKEN_KEY)
    if raw_token is None:
        return typ.cast("GitHubSimConfig", mutable_config), None

    if not isinstance(raw_token, str) or not raw_token.strip():
        msg = f"{_SIMULACAT_AUTH_TOKEN_KEY} must be a non-empty string"
        raise TypeError(msg)

    auth_token = raw_token
    return typ.cast("GitHubSimConfig", mutable_config), auth_token


def _coerce_github_sim_config(
    raw_config: object,
) -> cabc.Mapping[str, typ.Any]:
    if raw_config is None:
        return {}

    if isinstance(raw_config, ScenarioConfig):
        auth_token = raw_config.resolve_auth_token()
        sim_config = raw_config.to_simulator_config()
        config: dict[str, typ.Any] = dict(
            typ.cast("cabc.Mapping[str, typ.Any]", sim_config)
        )
        if auth_token is not None:
            config[_SIMULACAT_METADATA_KEY] = {_SIMULACAT_AUTH_TOKEN_KEY: auth_token}
        return config

    if not isinstance(raw_config, cabc.Mapping):
        msg = "github_sim_config must be a mapping"
        raise TypeError(msg)

    if not all(isinstance(key, str) for key in raw_config):
        msg = "github_sim_config keys must be strings"
        raise TypeError(msg)

    return typ.cast("cabc.Mapping[str, typ.Any]", raw_config)


def _validate_sim_config(config: cabc.Mapping[str, typ.Any]) -> GitHubSimConfig:
    materialized: dict[str, typ.Any] = dict(config)

    if materialized:
        for key in _REQUIRED_SIMULATOR_KEYS:
            if key not in materialized:
                materialized[key] = []
                continue

            value = materialized[key]
            if isinstance(value, list):
                continue

            msg = f"github_sim_config[{key!r}] must be a list"
            raise TypeError(msg)

    try:
        json.dumps(materialized)
    except (TypeError, ValueError) as exc:
        msg = "github_sim_config must be JSON serializable"
        raise TypeError(msg) from exc

    return typ.cast("GitHubSimConfig", materialized)


@pytest.fixture
def github_sim_config(request: pytest.FixtureRequest) -> GitHubSimConfig:
    """Return configuration for the GitHub API simulator.

    The fixture defaults to an empty mapping. Tests can override it by defining
    a fixture with the same name in a test module or a `conftest.py`, or by
    parametrizing it indirectly:

    `@pytest.mark.parametrize("github_sim_config", [...], indirect=True)`

    ScenarioConfig instances are also accepted when provided via indirect
    parametrization. Tokens are converted into Authorization metadata for the
    `github_simulator` fixture.

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
    coerced = _coerce_github_sim_config(raw_config)
    return _validate_sim_config(coerced)


@pytest.fixture
def simulacat_single_repo() -> GitHubSimConfig:
    """Return a single-repository scenario configuration."""
    from simulacat.scenario_factories import single_repo_scenario

    scenario = single_repo_scenario("octocat", name="demo-repo")
    return scenario.to_simulator_config()


@pytest.fixture
def simulacat_empty_org() -> GitHubSimConfig:
    """Return an empty-organisation scenario configuration."""
    from simulacat.scenario_factories import empty_org_scenario

    scenario = empty_org_scenario("octo-org")
    return scenario.to_simulator_config()


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
    github_sim_config: GitHubSimConfig | ScenarioConfig,
    tmp_path: Path,
) -> cabc.Generator[typ.Any, None, None]:
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
        if isinstance(github_sim_config, ScenarioConfig):
            auth_token = github_sim_config.resolve_auth_token()
            sim_config: GitHubSimConfig = github_sim_config.to_simulator_config()
        else:
            sim_config, auth_token = _split_simulacat_config(github_sim_config)

        proc, port = start_sim_process(sim_config, tmp_path)
        base_url = f"http://127.0.0.1:{port}"
        from github3.session import GitHubSession

        session = GitHubSession()
        session.base_url = base_url
        if auth_token is not None:
            session.headers["Authorization"] = f"token {auth_token}"
        client = github3.GitHub(session=session)
        yield client
    finally:
        if proc is not None:
            stop_sim_process(proc)
