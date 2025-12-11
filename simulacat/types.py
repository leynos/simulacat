"""Type definitions for simulacat.

These types describe the JSON configuration surface passed to the GitHub API
simulator. The schema mirrors the simulator's expected initial state, while
remaining permissive for partial configurations.
"""

from __future__ import annotations

import typing as typ


class GitHubSimConfig(typ.TypedDict, total=False):
    """Configuration mapping for the GitHub API simulator.

    All keys are optional so that callers can supply partial configurations.
    The orchestration layer fills missing required arrays when needed.
    """

    users: list[dict[str, typ.Any]]
    organizations: list[dict[str, typ.Any]]
    repositories: list[dict[str, typ.Any]]
    branches: list[dict[str, typ.Any]]
    blobs: list[dict[str, typ.Any]]

