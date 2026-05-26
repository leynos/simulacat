"""Shared protocols for github3.py test clients."""

from __future__ import annotations

import typing as typ

if typ.TYPE_CHECKING:
    import collections.abc as cabc


class GitHubClient(typ.Protocol):
    """Protocol for the subset of github3.GitHub used in tests."""

    def issue(self, owner: str, repository: str, number: int) -> object:
        """Return a single issue by number."""
        ...

    def organization(self, login: str) -> object:
        """Return an organization object by login."""
        ...

    def pull_request(self, owner: str, repository: str, number: int) -> object:
        """Return a single pull request by number."""
        ...

    def rate_limit(self) -> dict[str, object]:
        """Return the rate limit payload."""
        ...

    def repositories_by(self, username: str) -> cabc.Iterable[object]:
        """Iterate over repositories owned by a user/org."""
        ...

    def repository(self, owner: str, repository: str) -> object:
        """Return a repository by owner/name."""
        ...
