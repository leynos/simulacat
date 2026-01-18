"""Scenario factory helpers for common GitHub layouts.

These helpers provide reusable, named scenario fragments that compose into a
``ScenarioConfig``. They are intended to reduce test boilerplate while keeping
configuration explicit and validated.
"""

from __future__ import annotations

import dataclasses as dc
import typing as typ

from .scenario_config import ConfigValidationError, ScenarioConfig
from .scenario_models import Branch, DefaultBranch, Organization, Repository, User

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

    return ScenarioConfig(
        users=users,
        organizations=organizations,
        repositories=repositories,
        branches=branches,
        issues=issues,
        pull_requests=pull_requests,
    )


__all__ = [
    "empty_org_scenario",
    "merge_scenarios",
    "monorepo_with_apps_scenario",
    "single_repo_scenario",
]
