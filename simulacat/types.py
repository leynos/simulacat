"""Type definitions for simulacat.

These types describe the JSON configuration surface passed to the GitHub API
simulator. The schema mirrors the simulator's expected initial state, while
remaining permissive for partial configurations.
"""

from __future__ import annotations

import typing as typ


class GitHubUserConfig(typ.TypedDict, total=False):
    """Configuration schema for a GitHub user entry."""

    login: str
    organizations: list[str]
    id: int
    name: str
    bio: str
    email: str


class GitHubOrganizationConfig(typ.TypedDict, total=False):
    """Configuration schema for a GitHub organization entry."""

    login: str
    id: int
    name: str
    description: str
    email: str


class GitHubRepositoryConfig(typ.TypedDict, total=False):
    """Configuration schema for a GitHub repository entry."""

    owner: str
    name: str
    id: int
    description: str
    private: bool
    default_branch: str


class GitHubBranchConfig(typ.TypedDict, total=False):
    """Configuration schema for a GitHub branch entry."""

    owner: str
    repository: str
    name: str
    sha: str
    protected: bool


class GitHubUserRefConfig(typ.TypedDict, total=False):
    """Lightweight user reference used in nested objects."""

    login: str


class GitHubPullRequestRefConfig(typ.TypedDict, total=False):
    """Reference object for pull request base/head branches."""

    ref: str


class GitHubIssueConfig(typ.TypedDict, total=False):
    """Configuration schema for a GitHub issue entry."""

    owner: str
    repository: str
    number: int
    title: str
    body: str
    state: str
    user: GitHubUserRefConfig


class GitHubPullRequestConfig(typ.TypedDict, total=False):
    """Configuration schema for a GitHub pull request entry."""

    owner: str
    repository: str
    number: int
    title: str
    body: str
    state: str
    user: GitHubUserRefConfig
    base: GitHubPullRequestRefConfig
    head: GitHubPullRequestRefConfig
    draft: bool


class GitHubSimConfig(typ.TypedDict, total=False):
    """Configuration mapping for the GitHub API simulator.

    All keys are optional so that callers can supply partial configurations.
    The orchestration layer fills missing required arrays when needed.

    Most fields use strongly-typed structures for improved type safety. The
    `blobs` field remains untyped to allow arbitrary JSON-serializable
    structures. The pytest fixture validates JSON serializability at runtime.
    """

    users: list[GitHubUserConfig]
    organizations: list[GitHubOrganizationConfig]
    repositories: list[GitHubRepositoryConfig]
    branches: list[GitHubBranchConfig]
    issues: list[GitHubIssueConfig]
    pull_requests: list[GitHubPullRequestConfig]
    blobs: list[dict[str, typ.Any]]
