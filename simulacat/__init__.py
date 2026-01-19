"""simulacat package."""

from __future__ import annotations

from .config import (
    default_github_sim_config,
    is_json_serializable,
    merge_configs,
)
from .scenario import (
    Branch,
    ConfigValidationError,
    DefaultBranch,
    Issue,
    Organization,
    PullRequest,
    Repository,
    ScenarioConfig,
    User,
    empty_org_scenario,
    merge_scenarios,
    monorepo_with_apps_scenario,
    single_repo_scenario,
)
from .types import GitHubSimConfig

__all__ = [
    "Branch",
    "ConfigValidationError",
    "DefaultBranch",
    "GitHubSimConfig",
    "Issue",
    "Organization",
    "PullRequest",
    "Repository",
    "ScenarioConfig",
    "User",
    "default_github_sim_config",
    "empty_org_scenario",
    "is_json_serializable",
    "merge_configs",
    "merge_scenarios",
    "monorepo_with_apps_scenario",
    "single_repo_scenario",
]
