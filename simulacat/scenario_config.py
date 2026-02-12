"""Scenario configuration and validation helpers.

This module provides validation and serialization for scenario configuration
data classes, keeping test code insulated from the simulator's JSON schema.
Use :class:`ScenarioConfig` to validate inputs and emit a simulator-ready
configuration mapping.

Examples
--------
Build a scenario and serialize it for the simulator:

>>> from simulacat.scenario import Repository, ScenarioConfig, User
>>> scenario = ScenarioConfig(
...     users=(User(login="alice"),),
...     repositories=(Repository(owner="alice", name="demo"),),
... )
>>> config = scenario.to_simulator_config()
"""

from __future__ import annotations

import dataclasses as dc
import typing as typ

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

if typ.TYPE_CHECKING:
    from .types import GitHubSimConfig


class ConfigValidationError(ValueError):
    """Raised when a ScenarioConfig fails validation."""


type RepositoryKey = tuple[str, str]

_ALLOWED_REPOSITORY_VISIBILITIES = frozenset({"all", "private", "public"})


@dc.dataclass(frozen=True, slots=True)
class _ScenarioIndexes:
    """Internal validated indexes for scenario configuration."""

    org_logins: set[str]
    user_logins: set[str]
    repo_index: dict[RepositoryKey, Repository]
    branch_index: dict[RepositoryKey, dict[str, Branch]]
    app_slugs: set[str] = dc.field(default_factory=set)


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{label} must be a non-empty string"
        raise ConfigValidationError(msg)
    return value


def _require_positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
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


def _parse_repo_reference(value: str) -> RepositoryKey:
    if "/" not in value:
        msg = "Token repository must be in the form 'owner/repo'"
        raise ConfigValidationError(msg)
    owner, repo = value.split("/", 1)
    owner = _require_text(owner, "Token repository owner")
    repo = _require_text(repo, "Token repository name")
    return owner, repo


def _select_auth_token_value(
    token_values: list[str],
    default_token: str | None,
) -> str | None:
    if not token_values:
        if default_token is not None:
            msg = "Default token must match one of the configured tokens"
            raise ConfigValidationError(msg)
        return None

    if default_token is not None:
        selected = _require_text(default_token, "Default token")
        if selected not in token_values:
            msg = "Default token must match one of the configured tokens"
            raise ConfigValidationError(msg)
        return selected

    if len(token_values) == 1:
        return token_values[0]

    msg = "Multiple tokens configured but no default_token set"
    raise ConfigValidationError(msg)


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
    tokens: tuple[AccessToken, ...] = dc.field(default_factory=tuple)
    apps: tuple[GitHubApp, ...] = dc.field(default_factory=tuple)
    app_installations: tuple[AppInstallation, ...] = dc.field(default_factory=tuple)
    default_token: str | None = None
    _indexes: _ScenarioIndexes | None = dc.field(
        init=False,
        default=None,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """Normalise scenario collections into tuples for immutability."""
        object.__setattr__(self, "users", tuple(self.users))
        object.__setattr__(self, "organizations", tuple(self.organizations))
        object.__setattr__(self, "repositories", tuple(self.repositories))
        object.__setattr__(self, "branches", tuple(self.branches))
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(self, "pull_requests", tuple(self.pull_requests))
        object.__setattr__(self, "tokens", tuple(self.tokens))
        object.__setattr__(self, "apps", tuple(self.apps))
        object.__setattr__(self, "app_installations", tuple(self.app_installations))

    def validate(self, *, include_unsupported: bool = True) -> None:
        """Validate the scenario configuration.

        Parameters
        ----------
        include_unsupported
            When True, also validate issues and pull requests. This is enabled
            by default to keep `validate()` strict.

        Raises
        ------
        ConfigValidationError
            If the configuration is inconsistent or incomplete.

        """
        indexes = self._ensure_indexes()
        if include_unsupported:
            self._validate_issues(indexes.repo_index)
            self._validate_pull_requests(indexes.repo_index, indexes.branch_index)

    def to_simulator_config(
        self, *, include_unsupported: bool = False
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
        indexes = self._ensure_indexes()
        if include_unsupported:
            self._validate_issues(indexes.repo_index)
            self._validate_pull_requests(indexes.repo_index, indexes.branch_index)

        branches: list[Branch] = []
        for repo_branches in indexes.branch_index.values():
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

    def resolve_auth_token(self) -> str | None:
        """Return the configured default auth token value, if any.

        Installation access tokens are included in the candidate pool
        alongside standalone ``AccessToken`` values. The existing selection
        rules apply: a single token auto-selects; multiple tokens require
        ``default_token``.

        Returns
        -------
        str | None
            The token value to use for Authorization headers, or None when no
            tokens are configured.

        Raises
        ------
        ConfigValidationError
            If multiple tokens exist without a default selection.

        """
        self._ensure_indexes()
        token_values = [token.value for token in self.tokens]
        token_values.extend(
            inst.access_token
            for inst in self.app_installations
            if inst.access_token is not None
        )
        return _select_auth_token_value(token_values, self.default_token)

    def _ensure_indexes(self) -> _ScenarioIndexes:
        indexes = self._indexes
        if indexes is None:
            indexes = self._build_indexes()
            object.__setattr__(self, "_indexes", indexes)
        return indexes

    def _build_indexes(self) -> _ScenarioIndexes:
        org_logins = self._validate_organizations()
        user_logins = self._validate_users(org_logins)
        repo_index = self._validate_repositories(user_logins, org_logins)
        self._validate_tokens(user_logins, org_logins, repo_index)
        app_slugs = self._validate_apps(user_logins, org_logins)
        self._validate_app_installations(app_slugs, user_logins, org_logins, repo_index)
        self._validate_default_token()
        branch_index = self._validate_branches(repo_index)
        return _ScenarioIndexes(
            org_logins, user_logins, repo_index, branch_index, app_slugs
        )

    def _validate_organizations(self) -> set[str]:
        logins = [
            _require_text(org.login, "Organization login") for org in self.organizations
        ]
        return _ensure_unique(logins, "organization login")

    def _validate_users(self, org_logins: set[str]) -> set[str]:
        logins: list[str] = []
        for user in self.users:
            logins.append(_require_text(user.login, "User login"))
            for org in user.organizations:
                _require_text(org, "User organization")
                if org not in org_logins:
                    msg = (
                        "User organization must refer to a defined organization "
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
                    "Repository owner must be a defined user or organization "
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

    def _validate_tokens(
        self,
        user_logins: set[str],
        org_logins: set[str],
        repo_index: dict[RepositoryKey, Repository],
    ) -> None:
        token_values: list[str] = []
        for token in self.tokens:
            value = _require_text(token.value, "Token value")
            owner = _require_text(token.owner, "Token owner")
            if owner not in user_logins and owner not in org_logins:
                msg = (
                    "Token owner must be a defined user or organization "
                    f"(got {owner!r} for token {value!r})"
                )
                raise ConfigValidationError(msg)
            token_values.append(value)

            permissions = [
                _require_text(permission, "Token permission")
                for permission in token.permissions
            ]
            _ensure_unique(permissions, f"token permission for {value!r}")

            repositories = [
                _require_text(repo, "Token repository") for repo in token.repositories
            ]
            _ensure_unique(repositories, f"token repository reference for {value!r}")
            for repo in repositories:
                key = _parse_repo_reference(repo)
                if key not in repo_index:
                    msg = (
                        "Token repository must reference a configured repository "
                        f"(missing {repo!r} for token {value!r})"
                    )
                    raise ConfigValidationError(msg)

            if token.repository_visibility is None:
                continue

            if token.repository_visibility not in _ALLOWED_REPOSITORY_VISIBILITIES:
                msg = (
                    "Token repository visibility must be one of "
                    f"{sorted(_ALLOWED_REPOSITORY_VISIBILITIES)}"
                )
                raise ConfigValidationError(msg)

        _ensure_unique(token_values, "token value")

    def _validate_apps(
        self,
        user_logins: set[str],
        org_logins: set[str],
    ) -> set[str]:
        slugs: list[str] = []
        for app in self.apps:
            _require_text(app.app_slug, "App slug")
            _require_text(app.name, "App name")
            if app.app_id is not None:
                _require_positive_int(app.app_id, "App ID")
            if app.owner is not None:
                owner = _require_text(app.owner, "App owner")
                if owner not in user_logins and owner not in org_logins:
                    msg = (
                        "App owner must be a defined user or organization "
                        f"(got {owner!r} for app {app.app_slug!r})"
                    )
                    raise ConfigValidationError(msg)
            slugs.append(app.app_slug)
        return _ensure_unique(slugs, "app slug")

    def _validate_app_installations(
        self,
        app_slugs: set[str],
        user_logins: set[str],
        org_logins: set[str],
        repo_index: dict[RepositoryKey, Repository],
    ) -> None:
        installation_ids: list[str] = []
        token_values = [token.value for token in self.tokens]
        for installation in self.app_installations:
            _require_positive_int(installation.installation_id, "Installation ID")
            installation_ids.append(str(installation.installation_id))

            slug = _require_text(installation.app_slug, "Installation app slug")
            if slug not in app_slugs:
                msg = (
                    "Installation app must reference a defined GitHub App "
                    f"(got {slug!r} for installation "
                    f"{installation.installation_id})"
                )
                raise ConfigValidationError(msg)

            account = _require_text(installation.account, "Installation account")
            if account not in user_logins and account not in org_logins:
                msg = (
                    "Installation account must be a defined user or "
                    f"organization (got {account!r} for installation "
                    f"{installation.installation_id})"
                )
                raise ConfigValidationError(msg)

            for repo_ref in installation.repositories:
                _require_text(repo_ref, "Installation repository")
                key = _parse_repo_reference(repo_ref)
                if key not in repo_index:
                    msg = (
                        "Installation repository must reference a configured "
                        f"repository (missing {repo_ref!r} for installation "
                        f"{installation.installation_id})"
                    )
                    raise ConfigValidationError(msg)

            permissions = [
                _require_text(perm, "Installation permission")
                for perm in installation.permissions
            ]
            _ensure_unique(
                permissions,
                f"installation permission for installation "
                f"{installation.installation_id}",
            )

            if installation.access_token is not None:
                value = _require_text(
                    installation.access_token, "Installation access token"
                )
                if value in token_values:
                    msg = (
                        f"Duplicate token value: installation "
                        f"{installation.installation_id} access_token "
                        f"duplicates a standalone token"
                    )
                    raise ConfigValidationError(msg)
                token_values.append(value)

        _ensure_unique(installation_ids, "installation ID")

    def _validate_default_token(self) -> None:
        """Validate default_token against all token sources.

        This must be called after both ``_validate_tokens`` and
        ``_validate_app_installations`` so the full token pool is available.
        """
        token_values = [token.value for token in self.tokens]
        token_values.extend(
            inst.access_token
            for inst in self.app_installations
            if inst.access_token is not None
        )
        _select_auth_token_value(token_values, self.default_token)

    def _validate_branches(
        self, repo_index: dict[RepositoryKey, Repository]
    ) -> dict[RepositoryKey, dict[str, Branch]]:
        branch_index = self._validate_explicit_branches(repo_index)
        self._attach_default_branches(repo_index, branch_index)
        return branch_index

    def _validate_explicit_branches(
        self, repo_index: dict[RepositoryKey, Repository]
    ) -> dict[RepositoryKey, dict[str, Branch]]:
        branch_index: dict[RepositoryKey, dict[str, Branch]] = {}
        for branch in self.branches:
            key = self._validate_branch_core(branch, repo_index)
            repo_branches = branch_index.setdefault(key, {})
            existing = repo_branches.get(branch.name)
            if existing is not None:
                self._validate_branch_overlap(existing, branch, key)
            repo_branches[branch.name] = branch
        return branch_index

    @staticmethod
    def _validate_branch_core(
        branch: Branch,
        repo_index: dict[RepositoryKey, Repository],
    ) -> RepositoryKey:
        owner = _require_text(branch.owner, "Branch owner")
        repo = _require_text(branch.repository, "Branch repository")
        _require_text(branch.name, "Branch name")
        if branch.sha is not None:
            _require_text(branch.sha, "Branch sha")
        key = (owner, repo)
        if key not in repo_index:
            msg = f"Branch refers to unknown repository {owner}/{repo}"
            raise ConfigValidationError(msg)
        return key

    def _attach_default_branches(
        self,
        repo_index: dict[RepositoryKey, Repository],
        branch_index: dict[RepositoryKey, dict[str, Branch]],
    ) -> None:
        for key, repo in repo_index.items():
            if repo.default_branch is None:
                continue
            self._merge_default_branch(key, repo.default_branch, branch_index)

    def _merge_default_branch(
        self,
        key: RepositoryKey,
        default_branch: DefaultBranch,
        branch_index: dict[RepositoryKey, dict[str, Branch]],
    ) -> None:
        repo_branches = branch_index.setdefault(key, {})
        default_as_branch = default_branch.to_branch(*key)
        existing = repo_branches.get(default_as_branch.name)
        if existing is None:
            repo_branches[default_as_branch.name] = default_as_branch
            return
        self._validate_branch_overlap(
            existing,
            default_as_branch,
            key,
            is_default=True,
        )
        repo_branches[default_as_branch.name] = Branch(
            owner=existing.owner,
            repository=existing.repository,
            name=existing.name,
            sha=existing.sha or default_as_branch.sha,
            is_protected=(
                existing.is_protected
                if existing.is_protected is not None
                else default_as_branch.is_protected
            ),
        )

    @staticmethod
    def _validate_branch_overlap(
        existing: Branch,
        incoming: Branch,
        key: RepositoryKey,
        *,
        is_default: bool = False,
    ) -> None:
        mismatch: list[str] = []
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
    "ConfigValidationError",
    "ScenarioConfig",
]
