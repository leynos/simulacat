"""Validation helpers for GitHub App, installation, and token configuration.

Extracted from :mod:`simulacat.scenario_config` to keep the main module
focused on core scenario validation.  These functions validate
:class:`~simulacat.scenario_models.GitHubApp`,
:class:`~simulacat.scenario_models.AppInstallation`, and
:class:`~simulacat.scenario_models.AccessToken` instances against the
wider scenario context.
"""

from __future__ import annotations

import typing as typ

from ._validation_helpers import (
    _ALLOWED_REPOSITORY_VISIBILITIES,
    ConfigValidationError,
    RepositoryKey,
    _ensure_unique,
    _parse_repo_reference,
    _require_positive_int,
    _require_text,
    _select_auth_token_value,
)

if typ.TYPE_CHECKING:
    from .scenario_models import AccessToken, AppInstallation, GitHubApp, Repository


def validate_tokens(
    tokens: tuple[AccessToken, ...],
    user_logins: set[str],
    org_logins: set[str],
    repo_index: dict[RepositoryKey, Repository],
) -> list[str]:
    """Validate standalone access tokens and return their values.

    Parameters
    ----------
    tokens
        The access-token definitions to validate.
    user_logins
        Logins of all defined users.
    org_logins
        Logins of all defined organizations.
    repo_index
        Index of validated repositories keyed by ``(owner, name)``.

    Returns
    -------
    list[str]
        The validated list of token values.

    Raises
    ------
    ConfigValidationError
        If any token definition is invalid, references unknown entities,
        or duplicates another token value.

    """
    token_values: list[str] = []
    for token in tokens:
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
                    "Token repository must reference a configured "
                    f"repository (missing {repo!r} for token {value!r})"
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
    return token_values


def validate_apps(
    apps: tuple[GitHubApp, ...],
    user_logins: set[str],
    org_logins: set[str],
) -> set[str]:
    """Validate GitHub App definitions and return the set of known slugs.

    Parameters
    ----------
    apps
        The GitHub App definitions to validate.
    user_logins
        Logins of all defined users.
    org_logins
        Logins of all defined organizations.

    Returns
    -------
    set[str]
        The validated, unique set of app slugs.

    Raises
    ------
    ConfigValidationError
        If any app definition is invalid or duplicated.

    """
    slugs: list[str] = []
    for app in apps:
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


def validate_app_installations(  # noqa: PLR0913, PLR0917 — FIXME: consider a config object to reduce arity
    app_installations: tuple[AppInstallation, ...],
    app_slugs: set[str],
    user_logins: set[str],
    org_logins: set[str],
    repo_index: dict[RepositoryKey, Repository],
    token_values: list[str],
) -> list[str]:
    """Validate app installations and return the extended token-value pool.

    A *copy* of *token_values* is made internally; the caller's list is
    never mutated.  Installation access tokens are appended to the copy
    and the resulting list is returned.

    Parameters
    ----------
    app_installations
        The installation definitions to validate.
    app_slugs
        Slugs of all validated GitHub Apps.
    user_logins
        Logins of all defined users.
    org_logins
        Logins of all defined organizations.
    repo_index
        Index of validated repositories keyed by ``(owner, name)``.
    token_values
        Existing token values from standalone ``AccessToken`` instances.
        Used for duplicate detection; **not** modified in-place.

    Returns
    -------
    list[str]
        A new list containing all token values (standalone + installation).

    Raises
    ------
    ConfigValidationError
        If any installation is invalid, references unknown entities, or
        introduces duplicate tokens.

    """
    all_token_values: list[str] = list(token_values)
    installation_ids: list[str] = []
    for installation in app_installations:
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
            f"installation permission for installation {installation.installation_id}",
        )

        if installation.access_token is not None:
            value = _require_text(
                installation.access_token, "Installation access token"
            )
            if value in all_token_values:
                msg = (
                    f"Duplicate token value: installation "
                    f"{installation.installation_id} access_token "
                    f"duplicates a standalone token"
                )
                raise ConfigValidationError(msg)
            all_token_values.append(value)

    _ensure_unique(installation_ids, "installation ID")
    return all_token_values


def collect_all_token_values(
    tokens: tuple[AccessToken, ...],
    app_installations: tuple[AppInstallation, ...],
) -> list[str]:
    """Return all token values from standalone and installation sources.

    Parameters
    ----------
    tokens
        Standalone access-token definitions.
    app_installations
        App installation definitions (may carry ``access_token``).

    Returns
    -------
    list[str]
        Combined token values from both sources.

    """
    token_values = [token.value for token in tokens]
    token_values.extend(
        inst.access_token for inst in app_installations if inst.access_token is not None
    )
    return token_values


def validate_default_token(
    tokens: tuple[AccessToken, ...],
    app_installations: tuple[AppInstallation, ...],
    default_token: str | None,
) -> None:
    """Validate default_token against all token sources.

    This must be called after both token and app-installation validation
    so the full token pool is available.

    Parameters
    ----------
    tokens
        Standalone access-token definitions.
    app_installations
        App installation definitions (may carry ``access_token``).
    default_token
        The configured default token value, or ``None``.

    Raises
    ------
    ConfigValidationError
        If ``default_token`` does not match any configured token.

    """
    all_values = collect_all_token_values(tokens, app_installations)
    _select_auth_token_value(all_values, default_token)
    return  # noqa: PLR1711 — R503: explicit end-of-function return


__all__ = [
    "collect_all_token_values",
    "validate_app_installations",
    "validate_apps",
    "validate_default_token",
    "validate_tokens",
]
