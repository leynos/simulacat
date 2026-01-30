"""Scenario data models for GitHub simulator configuration.

These dataclasses capture the domain concepts used by the simulator (users,
repositories, branches, issues, and pull requests) while remaining independent
of the simulator's JSON schema. They are intended to be composed into a
``ScenarioConfig`` and serialized by the configuration layer.

Examples
--------
>>> from simulacat.scenario_models import Repository, User
>>> user = User(login="alice")
>>> repo = Repository(owner="alice", name="demo")
"""

from __future__ import annotations

import dataclasses as dc
import typing as typ

if typ.TYPE_CHECKING:
    from .types import (
        GitHubBranchConfig,
        GitHubIssueConfig,
        GitHubOrganizationConfig,
        GitHubPullRequestConfig,
        GitHubPullRequestRefConfig,
        GitHubRepositoryConfig,
        GitHubUserConfig,
        GitHubUserRefConfig,
    )


@dc.dataclass(frozen=True, slots=True)
class User:
    """Represent a GitHub user for scenario configuration."""

    login: str
    organizations: tuple[str, ...] = dc.field(default_factory=tuple)
    name: str | None = None
    bio: str | None = None
    email: str | None = None
    user_id: int | None = None

    def __post_init__(self) -> None:
        """Normalise organizations into a tuple for immutability."""
        object.__setattr__(self, "organizations", tuple(self.organizations))

    def to_dict(self) -> GitHubUserConfig:
        """Return the simulator-ready dictionary representation."""
        data: GitHubUserConfig = {
            "login": self.login,
            "organizations": list(self.organizations),
        }
        if self.name is not None:
            data["name"] = self.name
        if self.bio is not None:
            data["bio"] = self.bio
        if self.email is not None:
            data["email"] = self.email
        if self.user_id is not None:
            data["id"] = self.user_id
        return data


@dc.dataclass(frozen=True, slots=True)
class Organization:
    """Represent a GitHub organization for scenario configuration."""

    login: str
    name: str | None = None
    description: str | None = None
    email: str | None = None
    org_id: int | None = None

    def to_dict(self) -> GitHubOrganizationConfig:
        """Return the simulator-ready dictionary representation."""
        data: GitHubOrganizationConfig = {"login": self.login}
        if self.name is not None:
            data["name"] = self.name
        if self.description is not None:
            data["description"] = self.description
        if self.email is not None:
            data["email"] = self.email
        if self.org_id is not None:
            data["id"] = self.org_id
        return data


@dc.dataclass(frozen=True, slots=True)
class AccessToken:
    """Represent an access token for scenario configuration.

    Parameters
    ----------
    value : str
        Token string used for Authorization headers.
    owner : str
        User or organization login that owns the token.
    permissions : tuple[str, ...]
        Permission labels associated with the token.
    repositories : tuple[str, ...]
        Repository references in ``owner/name`` form scoped to the token.
    repository_visibility : str | None
        Visibility scope for repository access (``public``, ``private``,
        or ``all``).

    """

    value: str
    owner: str
    permissions: tuple[str, ...] = dc.field(default_factory=tuple)
    repositories: tuple[str, ...] = dc.field(default_factory=tuple)
    repository_visibility: str | None = None

    def __post_init__(self) -> None:
        """Normalize collections into tuples for immutability."""
        if isinstance(self.permissions, str):
            msg = "Token permissions must be an iterable of strings"
            raise TypeError(msg)
        if isinstance(self.repositories, str):
            msg = "Token repositories must be an iterable of strings"
            raise TypeError(msg)
        object.__setattr__(self, "permissions", tuple(self.permissions))
        object.__setattr__(self, "repositories", tuple(self.repositories))


@dc.dataclass(frozen=True, slots=True)
class DefaultBranch:
    """Describe default branch metadata for a repository."""

    name: str
    sha: str | None = None
    is_protected: bool | None = None

    def to_branch(self, owner: str, repository: str) -> Branch:
        """Return a Branch instance representing this default branch."""
        return Branch(
            owner=owner,
            repository=repository,
            name=self.name,
            sha=self.sha,
            is_protected=self.is_protected,
        )


@dc.dataclass(frozen=True, slots=True)
class Repository:
    """Represent a GitHub repository for scenario configuration."""

    owner: str
    name: str
    description: str | None = None
    is_private: bool = False
    default_branch: DefaultBranch | None = None
    repo_id: int | None = None

    def to_dict(self) -> GitHubRepositoryConfig:
        """Return the simulator-ready dictionary representation."""
        data: GitHubRepositoryConfig = {
            "owner": self.owner,
            "name": self.name,
            "private": self.is_private,
        }
        if self.description is not None:
            data["description"] = self.description
        if self.repo_id is not None:
            data["id"] = self.repo_id
        if self.default_branch is not None:
            data["default_branch"] = self.default_branch.name
        return data


@dc.dataclass(frozen=True, slots=True)
class Branch:
    """Represent a Git branch for scenario configuration."""

    owner: str
    repository: str
    name: str
    sha: str | None = None
    is_protected: bool | None = None

    def to_dict(self) -> GitHubBranchConfig:
        """Return the simulator-ready dictionary representation."""
        data: GitHubBranchConfig = {
            "owner": self.owner,
            "repository": self.repository,
            "name": self.name,
        }
        if self.is_protected is not None:
            data["protected"] = self.is_protected
        if self.sha is not None:
            data["sha"] = self.sha
        return data


@dc.dataclass(frozen=True, slots=True)
class Issue:
    """Represent a GitHub issue for scenario configuration."""

    owner: str
    repository: str
    number: int
    title: str
    body: str | None = None
    state: str = "open"
    author: str | None = None

    def to_dict(self) -> GitHubIssueConfig:
        """Return the simulator-ready dictionary representation."""
        data: GitHubIssueConfig = {
            "owner": self.owner,
            "repository": self.repository,
            "number": self.number,
            "title": self.title,
            "state": self.state,
        }
        if self.body is not None:
            data["body"] = self.body
        if self.author is not None:
            user: GitHubUserRefConfig = {"login": self.author}
            data["user"] = user
        return data


@dc.dataclass(frozen=True, slots=True)
class PullRequest:
    """Represent a GitHub pull request for scenario configuration."""

    owner: str
    repository: str
    number: int
    title: str
    body: str | None = None
    state: str = "open"
    author: str | None = None
    base_branch: str | None = None
    head_branch: str | None = None
    is_draft: bool = False

    def to_dict(self) -> GitHubPullRequestConfig:
        """Return the simulator-ready dictionary representation."""
        data: GitHubPullRequestConfig = {
            "owner": self.owner,
            "repository": self.repository,
            "number": self.number,
            "title": self.title,
            "state": self.state,
        }
        if self.body is not None:
            data["body"] = self.body
        if self.author is not None:
            user: GitHubUserRefConfig = {"login": self.author}
            data["user"] = user
        if self.base_branch is not None:
            base: GitHubPullRequestRefConfig = {"ref": self.base_branch}
            data["base"] = base
        if self.head_branch is not None:
            head: GitHubPullRequestRefConfig = {"ref": self.head_branch}
            data["head"] = head
        if self.is_draft:
            data["draft"] = True
        return data


__all__ = [
    "AccessToken",
    "Branch",
    "DefaultBranch",
    "Issue",
    "Organization",
    "PullRequest",
    "Repository",
    "User",
]
