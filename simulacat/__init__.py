"""simulacat package."""

from __future__ import annotations

from .api_stability import (
    PUBLIC_API,
    ApiStability,
    SimulacatDeprecationWarning,
)
from .config import (
    default_github_sim_config,
    is_json_serializable,
    merge_configs,
)
from .scenario import (
    AccessToken,
    AppInstallation,
    Branch,
    ConfigValidationError,
    DefaultBranch,
    GitHubApp,
    Issue,
    Organization,
    PullRequest,
    Repository,
    ScenarioConfig,
    User,
    empty_org_scenario,
    github_app_scenario,
    merge_scenarios,
    monorepo_with_apps_scenario,
    single_repo_scenario,
)
from .types import GitHubSimConfig

__all__ = [
    "PUBLIC_API",
    "AccessToken",
    "ApiStability",
    "AppInstallation",
    "Branch",
    "ConfigValidationError",
    "DefaultBranch",
    "GitHubApp",
    "GitHubSimConfig",
    "Issue",
    "Organization",
    "PullRequest",
    "Repository",
    "ScenarioConfig",
    "SimulacatDeprecationWarning",
    "User",
    "default_github_sim_config",
    "empty_org_scenario",
    "github_app_scenario",
    "is_json_serializable",
    "merge_configs",
    "merge_scenarios",
    "monorepo_with_apps_scenario",
    "single_repo_scenario",
]
