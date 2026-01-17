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
    if not isinstance(value, str) or not value.strip():
        msg = f"{label} must be a non-empty string"
        raise ConfigValidationError(msg)
    return value


def _require_unique(values: cabc.Iterable[str], label: str) -> tuple[str, ...]:
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
    label: str
    key: cabc.Callable[[T], Key]
    format_key: cabc.Callable[[Key], str]
    getter: cabc.Callable[[ScenarioConfig], cabc.Iterable[T]]


def _merge_entries[T, Key](
    scenarios: cabc.Iterable[ScenarioConfig],
    spec: _MergeSpec[T, Key],
) -> tuple[T, ...]:
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
    """Return a scenario for a single repository owned by a user or organisation."""
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
    """Return a scenario with a single empty organisation."""
    login = _require_text(login, "Organization login")
    return ScenarioConfig(organizations=(Organization(login=login),))


def monorepo_with_apps_scenario(
    owner: str,
    repo: str = "monorepo",
    apps: tuple[str, ...] = ("app",),
    *,
    owner_is_org: bool = False,
) -> ScenarioConfig:
    """Return a monorepo scenario with app branches under ``apps/<name>``."""
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
