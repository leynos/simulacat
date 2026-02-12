"""Scenario factory helpers for common GitHub layouts.

These helpers provide reusable, named scenario fragments that compose into a
``ScenarioConfig``. They are intended to reduce test boilerplate while keeping
configuration explicit and validated.
"""

from __future__ import annotations

import dataclasses as dc
import typing as typ

from .scenario_config import ConfigValidationError, ScenarioConfig
from .scenario_models import (
    AppInstallation,
    Branch,
    DefaultBranch,
    GitHubApp,
    Organization,
    Repository,
    User,
)

if typ.TYPE_CHECKING:
    import collections.abc as cabc


def _require_text(value: object, label: str) -> str:
    """Validate a non-empty string input."""
    if not isinstance(value, str) or not value.strip():
        msg = f"{label} must be a non-empty string"
        raise ConfigValidationError(msg)
    return value


def _require_unique(values: cabc.Iterable[str], label: str) -> tuple[str, ...]:
    """Ensure all values are unique."""
    items = tuple(values)
    seen: set[str] = set()
    for value in items:
        if value in seen:
            msg = f"Duplicate {label}: {value!r}"
            raise ConfigValidationError(msg)
        seen.add(value)
    return items


@dc.dataclass(frozen=True, slots=True)
class _MergeSpec[T, Key]:
    """Describe how to merge a scenario collection."""

    label: str
    key: cabc.Callable[[T], Key]
    format_key: cabc.Callable[[Key], str]
    getter: cabc.Callable[[ScenarioConfig], cabc.Iterable[T]]


def _merge_entries[T, Key](
    scenarios: cabc.Iterable[ScenarioConfig],
    spec: _MergeSpec[T, Key],
) -> tuple[T, ...]:
    """Merge scenario entries with conflict detection."""
    merged: dict[Key, T] = {}
    for scenario in scenarios:
        for item in spec.getter(scenario):
            item_key = spec.key(item)
            existing = merged.get(item_key)
            if existing is None:
                merged[item_key] = item
            elif existing != item:
                msg = (
                    f"Conflicting {spec.label} definition for "
                    f"{spec.format_key(item_key)}"
                )
                raise ConfigValidationError(msg)
    return tuple(merged.values())


def single_repo_scenario(
    owner: str,
    name: str = "repo",
    *,
    owner_is_org: bool = False,
    default_branch: str = "main",
) -> ScenarioConfig:
    """Return a scenario for a single repository owned by a user or organization.

    Parameters
    ----------
    owner : str
        Login for the user or organization that owns the repository.
    name : str, optional
        Repository name.
    owner_is_org : bool, optional
        Whether the owner should be treated as an organization.
    default_branch : str, optional
        Default branch name for the repository.

    Returns
    -------
    ScenarioConfig
        Scenario configuration with a single repository and owner.

    Raises
    ------
    ConfigValidationError
        If any provided text values are blank.
    """
    owner = _require_text(owner, "Owner")
    name = _require_text(name, "Repository name")
    default_branch = _require_text(default_branch, "Default branch")

    users = ()
    organizations = ()
    if owner_is_org:
        organizations = (Organization(login=owner),)
    else:
        users = (User(login=owner),)

    repo = Repository(
        owner=owner,
        name=name,
        default_branch=DefaultBranch(name=default_branch),
    )
    return ScenarioConfig(
        users=users,
        organizations=organizations,
        repositories=(repo,),
    )


def empty_org_scenario(login: str) -> ScenarioConfig:
    """Return a scenario with a single empty organization.

    Parameters
    ----------
    login : str
        Organization login name.

    Returns
    -------
    ScenarioConfig
        Scenario configuration with the organization and no repositories.

    Raises
    ------
    ConfigValidationError
        If the login is blank.
    """
    login = _require_text(login, "Organization login")
    return ScenarioConfig(organizations=(Organization(login=login),))


def monorepo_with_apps_scenario(
    owner: str,
    repo: str = "monorepo",
    apps: tuple[str, ...] = ("app",),
    *,
    owner_is_org: bool = False,
) -> ScenarioConfig:
    """Return a monorepo scenario with app branches under ``apps/<name>``.

    Parameters
    ----------
    owner : str
        Login for the user or organization that owns the repository.
    repo : str, optional
        Monorepo name.
    apps : tuple[str, ...], optional
        App names to map to ``apps/<name>`` branches.
    owner_is_org : bool, optional
        Whether the owner should be treated as an organization.

    Returns
    -------
    ScenarioConfig
        Scenario configuration with a monorepo and app branches.

    Raises
    ------
    ConfigValidationError
        If any text inputs are blank, the apps list is empty, or app names are
        duplicated.
    """
    owner = _require_text(owner, "Owner")
    repo = _require_text(repo, "Repository name")
    if not apps:
        msg = "Apps must include at least one entry"
        raise ConfigValidationError(msg)
    app_names = _require_unique(
        [_require_text(app, "App name") for app in apps],
        "app name",
    )

    users = ()
    organizations = ()
    if owner_is_org:
        organizations = (Organization(login=owner),)
    else:
        users = (User(login=owner),)

    repository = Repository(
        owner=owner,
        name=repo,
        default_branch=DefaultBranch(name="main"),
    )
    branches = tuple(
        Branch(
            owner=owner,
            repository=repo,
            name=f"apps/{app}",
        )
        for app in app_names
    )
    return ScenarioConfig(
        users=users,
        organizations=organizations,
        repositories=(repository,),
        branches=branches,
    )


def github_app_scenario(  # noqa: PLR0913
    app_slug: str,
    name: str,
    *,
    account: str,
    account_is_org: bool = False,
    repositories: tuple[str, ...] = (),
    permissions: tuple[str, ...] = (),
    access_token: str | None = None,
    app_id: int | None = None,
) -> ScenarioConfig:
    """Return a scenario with a GitHub App and one installation.

    Parameters
    ----------
    app_slug : str
        URL-friendly identifier for the app.
    name : str
        Human-readable display name for the app.
    account : str
        User or organization login where the app is installed.
    account_is_org : bool, optional
        Whether the account should be treated as an organization.
    repositories : tuple[str, ...], optional
        Repository references in ``owner/name`` form accessible to the
        installation.
    permissions : tuple[str, ...], optional
        Permission labels granted to this installation.
    access_token : str | None, optional
        Optional token value used for ``Authorization`` headers.
    app_id : int | None, optional
        Numeric app ID assigned by GitHub.

    Returns
    -------
    ScenarioConfig
        Scenario configuration with the app, installation, and account.

    Raises
    ------
    ConfigValidationError
        If any provided text values are blank.

    """
    app_slug = _require_text(app_slug, "App slug")
    name = _require_text(name, "App name")
    account = _require_text(account, "Account")

    users: tuple[User, ...] = ()
    organizations: tuple[Organization, ...] = ()
    if account_is_org:
        organizations = (Organization(login=account),)
    else:
        users = (User(login=account),)

    app = GitHubApp(app_slug=app_slug, name=name, app_id=app_id)
    installation = AppInstallation(
        installation_id=1,
        app_slug=app_slug,
        account=account,
        repositories=repositories,
        permissions=permissions,
        access_token=access_token,
    )

    repo_objects: list[Repository] = []
    for repo_ref in repositories:
        if "/" not in repo_ref:
            msg = (
                f"Repository reference must be in 'owner/repo' form (got {repo_ref!r})"
            )
            raise ConfigValidationError(msg)
        owner, repo_name = repo_ref.split("/", 1)
        repo_objects.append(Repository(owner=owner, name=repo_name))

    return ScenarioConfig(
        users=users,
        organizations=organizations,
        repositories=tuple(repo_objects),
        apps=(app,),
        app_installations=(installation,),
    )


def merge_scenarios(*scenarios: ScenarioConfig) -> ScenarioConfig:
    """Merge multiple scenarios into a single configuration.

    Scenarios are merged left to right. Entities with the same identity key are
    deduplicated if identical, and raise ``ConfigValidationError`` when their
    definitions differ.

    Parameters
    ----------
    *scenarios : ScenarioConfig
        Scenario fragments to merge.

    Returns
    -------
    ScenarioConfig
        Combined scenario configuration.

    Raises
    ------
    ConfigValidationError
        If any entity definitions conflict across the scenarios.
    """
    scenario_list = tuple(scenarios)
    if not scenario_list:
        return ScenarioConfig()

    users = _merge_entries(
        scenario_list,
        _MergeSpec(
            label="user",
            key=lambda user: user.login,
            format_key=lambda key: key,
            getter=lambda scenario: scenario.users,
        ),
    )
    organizations = _merge_entries(
        scenario_list,
        _MergeSpec(
            label="organization",
            key=lambda org: org.login,
            format_key=lambda key: key,
            getter=lambda scenario: scenario.organizations,
        ),
    )
    repositories = _merge_entries(
        scenario_list,
        _MergeSpec(
            label="repository",
            key=lambda repo: (repo.owner, repo.name),
            format_key=lambda key: f"{key[0]}/{key[1]}",
            getter=lambda scenario: scenario.repositories,
        ),
    )
    branches = _merge_entries(
        scenario_list,
        _MergeSpec(
            label="branch",
            key=lambda branch: (branch.owner, branch.repository, branch.name),
            format_key=lambda key: f"{key[0]}/{key[1]}:{key[2]}",
            getter=lambda scenario: scenario.branches,
        ),
    )
    issues = _merge_entries(
        scenario_list,
        _MergeSpec(
            label="issue",
            key=lambda issue: (issue.owner, issue.repository, issue.number),
            format_key=lambda key: f"{key[0]}/{key[1]}#{key[2]}",
            getter=lambda scenario: scenario.issues,
        ),
    )
    pull_requests = _merge_entries(
        scenario_list,
        _MergeSpec(
            label="pull request",
            key=lambda pr: (pr.owner, pr.repository, pr.number),
            format_key=lambda key: f"{key[0]}/{key[1]}#{key[2]}",
            getter=lambda scenario: scenario.pull_requests,
        ),
    )
    apps = _merge_entries(
        scenario_list,
        _MergeSpec(
            label="app",
            key=lambda app: app.app_slug,
            format_key=lambda key: key,
            getter=lambda scenario: scenario.apps,
        ),
    )
    app_installations = _merge_entries(
        scenario_list,
        _MergeSpec(
            label="app installation",
            key=lambda inst: inst.installation_id,
            format_key=str,
            getter=lambda scenario: scenario.app_installations,
        ),
    )

    return ScenarioConfig(
        users=users,
        organizations=organizations,
        repositories=repositories,
        branches=branches,
        issues=issues,
        pull_requests=pull_requests,
        apps=apps,
        app_installations=app_installations,
    )


__all__ = [
    "empty_org_scenario",
    "github_app_scenario",
    "merge_scenarios",
    "monorepo_with_apps_scenario",
    "single_repo_scenario",
]
