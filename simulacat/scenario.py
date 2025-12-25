"""Public scenario configuration API.

This module exposes the stable, test-facing scenario surface. Import the data
classes and ``ScenarioConfig`` from here to build simulator configurations
without depending on the internal JSON schema.

Examples
--------
>>> from simulacat.scenario import Repository, ScenarioConfig, User
>>> scenario = ScenarioConfig(
...     users=(User(login="alice"),),
...     repositories=(Repository(owner="alice", name="demo"),),
... )
>>> config = scenario.to_simulator_config()
"""

from __future__ import annotations

from .scenario_config import ConfigValidationError, ScenarioConfig
from .scenario_models import (
    Branch,
    DefaultBranch,
    Issue,
    Organization,
    PullRequest,
    Repository,
    User,
)

__all__ = [
    "Branch",
    "ConfigValidationError",
    "DefaultBranch",
    "Issue",
    "Organization",
    "PullRequest",
    "Repository",
    "ScenarioConfig",
    "User",
]
