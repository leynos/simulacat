"""Validation helpers for issue and pull-request configuration.

Extracted from :mod:`simulacat.scenario_config` to keep the main module
focused on core scenario validation.  These functions validate
:class:`~simulacat.scenario_models.Issue` and
:class:`~simulacat.scenario_models.PullRequest` instances against the
wider scenario context.
"""

from __future__ import annotations

import typing as typ

from ._validation_helpers import (
    ConfigValidationError,
    RepositoryKey,
    _require_positive_int,
    _require_text,
)

if typ.TYPE_CHECKING:
    from .scenario_models import Branch, Issue, PullRequest, Repository

_ALLOWED_STATES = frozenset({"open", "closed"})


def _require_state(state: str, label: str) -> None:
    if state not in _ALLOWED_STATES:
        msg = f"{label} must be one of {sorted(_ALLOWED_STATES)}"
        raise ConfigValidationError(msg)


def validate_issues(
    issues: tuple[Issue, ...],
    repo_index: dict[RepositoryKey, Repository],
) -> None:
    """Validate issue definitions against the repository index.

    Parameters
    ----------
    issues
        The issue definitions to validate.
    repo_index
        Index of validated repositories keyed by ``(owner, name)``.

    Raises
    ------
    ConfigValidationError
        If any issue is invalid, references an unknown repository, or
        has a duplicate number within a repository.

    """
    issue_numbers: dict[RepositoryKey, set[int]] = {}
    for issue in issues:
        owner = _require_text(issue.owner, "Issue owner")
        repo = _require_text(issue.repository, "Issue repository")
        number = _require_positive_int(issue.number, "Issue number")
        _require_text(issue.title, "Issue title")
        _require_state(issue.state, "Issue state")
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


def validate_pull_requests(
    pull_requests: tuple[PullRequest, ...],
    repo_index: dict[RepositoryKey, Repository],
    branch_index: dict[RepositoryKey, dict[str, Branch]],
) -> None:
    """Validate pull-request definitions against repository and branch indexes.

    Parameters
    ----------
    pull_requests
        The pull-request definitions to validate.
    repo_index
        Index of validated repositories keyed by ``(owner, name)``.
    branch_index
        Index of validated branches keyed by repository then branch name.

    Raises
    ------
    ConfigValidationError
        If any pull request is invalid, references an unknown repository
        or branch, or has a duplicate number within a repository.

    """
    pr_numbers: dict[RepositoryKey, set[int]] = {}
    for pr in pull_requests:
        owner = _require_text(pr.owner, "Pull request owner")
        repo = _require_text(pr.repository, "Pull request repository")
        number = _require_positive_int(pr.number, "Pull request number")
        _require_text(pr.title, "Pull request title")
        _require_state(pr.state, "Pull request state")
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
        _validate_pull_request_branches(pr, key, branch_index)


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


__all__ = [
    "validate_issues",
    "validate_pull_requests",
]
