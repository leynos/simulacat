"""Scenario models for GitHub simulator configuration.

These dataclasses provide a stable, Pythonic configuration surface that can be
validated and serialized into the simulator's JSON configuration format.
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
        GitHubRepositoryConfig,
        GitHubSimConfig,
        GitHubUserConfig,
    )


class ConfigValidationError(ValueError):
    """Raised when a ScenarioConfig fails validation."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{label} must be a non-empty string"
        raise ConfigValidationError(msg)
    return value


def _require_positive_int(value: object, label: str) -> int:
    if not isinstance(value, int) or value <= 0:
        msg = f"{label} must be a positive integer"
        raise ConfigValidationError(msg)
    return value


def _ensure_unique(values: list[str], label: str) -> set[str]:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            msg = f"Duplicate {label}: {value!r}"
            raise ConfigValidationError(msg)
        seen.add(value)
    return seen


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
        """Normalise organisations into a tuple for immutability."""
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
    """Represent a GitHub organisation for scenario configuration."""

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
            data["user"] = {"login": self.author}
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
            data["user"] = {"login": self.author}
        if self.base_branch is not None:
            data["base"] = {"ref": self.base_branch}
        if self.head_branch is not None:
            data["head"] = {"ref": self.head_branch}
        if self.is_draft:
            data["draft"] = True
        return data


RepositoryKey = tuple[str, str]


@dc.dataclass(frozen=True, slots=True)
class ScenarioConfig:
    """Container for scenario configuration.

    Use this class to build and validate simulator configuration without
    depending on the simulator's internal JSON schema.
    """

    users: tuple[User, ...] = dc.field(default_factory=tuple)
    organizations: tuple[Organization, ...] = dc.field(default_factory=tuple)
    repositories: tuple[Repository, ...] = dc.field(default_factory=tuple)
    branches: tuple[Branch, ...] = dc.field(default_factory=tuple)
    issues: tuple[Issue, ...] = dc.field(default_factory=tuple)
    pull_requests: tuple[PullRequest, ...] = dc.field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Normalise scenario collections into tuples for immutability."""
        object.__setattr__(self, "users", tuple(self.users))
        object.__setattr__(self, "organizations", tuple(self.organizations))
        object.__setattr__(self, "repositories", tuple(self.repositories))
        object.__setattr__(self, "branches", tuple(self.branches))
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(self, "pull_requests", tuple(self.pull_requests))

    def validate(self) -> None:
        """Validate the scenario configuration.

        Raises
        ------
        ConfigValidationError
            If the configuration is inconsistent or incomplete.

        """
        self._build_indexes()

    def to_simulator_config(
        self,
        *,
        include_unsupported: bool = False,
    ) -> GitHubSimConfig:
        """Serialize the scenario into the simulator configuration format.

        Parameters
        ----------
        include_unsupported
            Include issues and pull requests in the serialized configuration.
            These are retained in the scenario even if the simulator ignores
            them, so they are opt-in by default.

        Returns
        -------
        GitHubSimConfig
            A JSON-serializable simulator configuration.

        """
        _orgs, _users, _repos, branch_index = self._build_indexes()
        branches: list[Branch] = []
        for repo_branches in branch_index.values():
            branches.extend(repo_branches.values())
        config: GitHubSimConfig = {
            "users": [user.to_dict() for user in self.users],
            "organizations": [org.to_dict() for org in self.organizations],
            "repositories": [repo.to_dict() for repo in self.repositories],
            "branches": [branch.to_dict() for branch in branches],
            "blobs": [],
        }

        if include_unsupported:
            config["issues"] = [issue.to_dict() for issue in self.issues]
            config["pull_requests"] = [pr.to_dict() for pr in self.pull_requests]

        return config

    def _build_indexes(
        self,
    ) -> tuple[
        set[str],
        set[str],
        dict[RepositoryKey, Repository],
        dict[RepositoryKey, dict[str, Branch]],
    ]:
        org_logins = self._validate_organizations()
        user_logins = self._validate_users(org_logins)
        repo_index = self._validate_repositories(user_logins, org_logins)
        branch_index = self._validate_branches(repo_index)
        self._validate_issues(repo_index)
        self._validate_pull_requests(repo_index, branch_index)
        return org_logins, user_logins, repo_index, branch_index

    def _validate_organizations(self) -> set[str]:
        logins = [
            _require_text(org.login, "Organisation login") for org in self.organizations
        ]
        return _ensure_unique(logins, "organisation login")

    def _validate_users(self, org_logins: set[str]) -> set[str]:
        logins: list[str] = []
        for user in self.users:
            logins.append(_require_text(user.login, "User login"))
            for org in user.organizations:
                _require_text(org, "User organisation")
                if org not in org_logins:
                    msg = (
                        "User organisation must refer to a defined organisation "
                        f"(missing {org!r} for user {user.login!r})"
                    )
                    raise ConfigValidationError(msg)
        return _ensure_unique(logins, "user login")

    def _validate_repositories(
        self,
        user_logins: set[str],
        org_logins: set[str],
    ) -> dict[RepositoryKey, Repository]:
        repo_index: dict[RepositoryKey, Repository] = {}
        for repo in self.repositories:
            owner = _require_text(repo.owner, "Repository owner")
            name = _require_text(repo.name, "Repository name")
            if owner not in user_logins and owner not in org_logins:
                msg = (
                    "Repository owner must be a defined user or organisation "
                    f"(got {owner!r} for {owner}/{name})"
                )
                raise ConfigValidationError(msg)
            key = (owner, name)
            if key in repo_index:
                msg = f"Duplicate repository definition: {owner}/{name}"
                raise ConfigValidationError(msg)
            if repo.default_branch is not None:
                _require_text(repo.default_branch.name, "Default branch name")
                if repo.default_branch.sha is not None:
                    _require_text(repo.default_branch.sha, "Default branch sha")
            repo_index[key] = repo
        return repo_index

    def _validate_branches(
        self, repo_index: dict[RepositoryKey, Repository]
    ) -> dict[RepositoryKey, dict[str, Branch]]:
        branch_index: dict[RepositoryKey, dict[str, Branch]] = {}
        for branch in self.branches:
            owner = _require_text(branch.owner, "Branch owner")
            repo = _require_text(branch.repository, "Branch repository")
            name = _require_text(branch.name, "Branch name")
            if branch.sha is not None:
                _require_text(branch.sha, "Branch sha")
            key = (owner, repo)
            if key not in repo_index:
                msg = f"Branch refers to unknown repository {owner}/{repo}"
                raise ConfigValidationError(msg)
            repo_branches = branch_index.setdefault(key, {})
            existing = repo_branches.get(name)
            if existing is not None:
                self._validate_branch_overlap(existing, branch, key)
            repo_branches[name] = branch

        for key, repo in repo_index.items():
            if repo.default_branch is None:
                continue
            default_branch = repo.default_branch.to_branch(*key)
            repo_branches = branch_index.setdefault(key, {})
            existing = repo_branches.get(default_branch.name)
            if existing is not None:
                self._validate_branch_overlap(
                    existing,
                    default_branch,
                    key,
                    is_default=True,
                )
                repo_branches[default_branch.name] = Branch(
                    owner=existing.owner,
                    repository=existing.repository,
                    name=existing.name,
                    sha=existing.sha or default_branch.sha,
                    is_protected=(
                        existing.is_protected
                        if existing.is_protected is not None
                        else default_branch.is_protected
                    ),
                )
                continue
            repo_branches[default_branch.name] = default_branch

        return branch_index

    @staticmethod
    def _validate_branch_overlap(
        existing: Branch,
        incoming: Branch,
        key: RepositoryKey,
        *,
        is_default: bool = False,
    ) -> None:
        mismatch = []
        if existing.sha and incoming.sha and existing.sha != incoming.sha:
            mismatch.append("sha")
        if (
            existing.is_protected is not None
            and incoming.is_protected is not None
            and existing.is_protected != incoming.is_protected
        ):
            mismatch.append("protected")
        if mismatch:
            kind = "default branch" if is_default else "branch"
            owner, repo = key
            msg = (
                f"Conflicting {kind} metadata for {owner}/{repo}:{existing.name} "
                f"({', '.join(mismatch)} differs)"
            )
            raise ConfigValidationError(msg)

    def _validate_issues(self, repo_index: dict[RepositoryKey, Repository]) -> None:
        issue_numbers: dict[RepositoryKey, set[int]] = {}
        for issue in self.issues:
            owner = _require_text(issue.owner, "Issue owner")
            repo = _require_text(issue.repository, "Issue repository")
            number = _require_positive_int(issue.number, "Issue number")
            _require_text(issue.title, "Issue title")
            self._require_state(issue.state, "Issue state")
            if issue.author is not None:
                _require_text(issue.author, "Issue author")
            key = (owner, repo)
            if key not in repo_index:
                msg = f"Issue refers to unknown repository {owner}/{repo}"
                raise ConfigValidationError(msg)
            numbers = issue_numbers.setdefault(key, set())
            if number in numbers:
                msg = f"Duplicate issue number {number} for {owner}/{repo}"
                raise ConfigValidationError(msg)
            numbers.add(number)

    def _validate_pull_requests(
        self,
        repo_index: dict[RepositoryKey, Repository],
        branch_index: dict[RepositoryKey, dict[str, Branch]],
    ) -> None:
        pr_numbers: dict[RepositoryKey, set[int]] = {}
        for pr in self.pull_requests:
            owner = _require_text(pr.owner, "Pull request owner")
            repo = _require_text(pr.repository, "Pull request repository")
            number = _require_positive_int(pr.number, "Pull request number")
            _require_text(pr.title, "Pull request title")
            self._require_state(pr.state, "Pull request state")
            if pr.author is not None:
                _require_text(pr.author, "Pull request author")
            key = (owner, repo)
            if key not in repo_index:
                msg = f"Pull request refers to unknown repository {owner}/{repo}"
                raise ConfigValidationError(msg)
            numbers = pr_numbers.setdefault(key, set())
            if number in numbers:
                msg = f"Duplicate pull request number {number} for {owner}/{repo}"
                raise ConfigValidationError(msg)
            numbers.add(number)
            self._validate_pull_request_branches(pr, key, branch_index)

    @staticmethod
    def _validate_pull_request_branches(
        pr: PullRequest,
        key: RepositoryKey,
        branch_index: dict[RepositoryKey, dict[str, Branch]],
    ) -> None:
        repo_branches = branch_index.get(key, {})
        for label, name in ("base", pr.base_branch), ("head", pr.head_branch):
            if name is None:
                continue
            _require_text(name, f"Pull request {label} branch")
            if name not in repo_branches:
                owner, repo = key
                msg = (
                    "Pull request branch must reference a configured branch "
                    f"(missing {name!r} for {owner}/{repo})"
                )
                raise ConfigValidationError(msg)

    @staticmethod
    def _require_state(state: str, label: str) -> None:
        allowed = {"open", "closed"}
        if state not in allowed:
            msg = f"{label} must be one of {sorted(allowed)}"
            raise ConfigValidationError(msg)


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
