"""Shared validation primitives used across scenario validation modules.

This module holds low-level helpers and the canonical
:class:`ConfigValidationError` exception so that higher-level validation
modules (``scenario_config``, ``app_validation``, ``issue_validation``)
can import them without circular dependencies.
"""

from __future__ import annotations


class ConfigValidationError(ValueError):
    """Raised when a ScenarioConfig fails validation."""


type RepositoryKey = tuple[str, str]

_ALLOWED_REPOSITORY_VISIBILITIES = frozenset({"all", "private", "public"})


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
    """Select the auth token value from the given pool.

    Parameters
    ----------
    token_values
        All available token values.
    default_token
        Explicit default selection, or ``None``.

    Returns
    -------
    str | None
        The selected token value, or ``None`` when no tokens exist.

    Raises
    ------
    ConfigValidationError
        If the default doesn't match, or multiple tokens exist without
        a default.

    """
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


__all__ = [
    "ConfigValidationError",
    "RepositoryKey",
]
