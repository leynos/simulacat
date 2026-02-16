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
from .scenario_factories import (
    empty_org_scenario,
    github_app_scenario,
    merge_scenarios,
    monorepo_with_apps_scenario,
    single_repo_scenario,
)
from .scenario_models import (
    AccessToken,
    AppInstallation,
    Branch,
    DefaultBranch,
    GitHubApp,
    Issue,
    Organization,
    PullRequest,
    Repository,
    User,
)

__all__ = [
    "AccessToken",
    "AppInstallation",
    "Branch",
    "ConfigValidationError",
    "DefaultBranch",
    "GitHubApp",
    "Issue",
    "Organization",
    "PullRequest",
    "Repository",
    "ScenarioConfig",
    "User",
    "empty_org_scenario",
    "github_app_scenario",
    "merge_scenarios",
    "monorepo_with_apps_scenario",
    "single_repo_scenario",
]
