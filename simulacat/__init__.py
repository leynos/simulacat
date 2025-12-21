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
)
from .types import GitHubSimConfig

PACKAGE_NAME = "simulacat"

try:  # pragma: no cover - Rust optional
    rust = __import__(f"_{PACKAGE_NAME}_rs")
    hello = rust.hello  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python fallback
    from .pure import hello

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
    "hello",
    "is_json_serializable",
    "merge_configs",
]
