"""simulacat package."""

from __future__ import annotations

from .fixtures import (
    GitHubSimConfig,
    default_github_sim_config,
    github_sim_config,
    is_json_serializable,
    merge_configs,
)

PACKAGE_NAME = "simulacat"

try:  # pragma: no cover - Rust optional
    rust = __import__(f"_{PACKAGE_NAME}_rs")
    hello = rust.hello  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python fallback
    from .pure import hello

__all__ = [
    "GitHubSimConfig",
    "default_github_sim_config",
    "github_sim_config",
    "hello",
    "is_json_serializable",
    "merge_configs",
]
