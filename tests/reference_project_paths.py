"""Path helpers for Step 3.2 reference project test assets.

This module provides a single place for deriving absolute paths to the
reference projects used by unit and behavioural tests.

Examples
--------
Resolve the authenticated reference project path::

    from tests.reference_project_paths import reference_project_path

    project_dir = reference_project_path("authenticated-pytest")
"""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the repository root directory.

    Returns
    -------
    Path
        Absolute path to the repository root.

    """
    return Path(__file__).resolve().parents[1]


def reference_project_path(name: str) -> Path:
    """Return the absolute path to a named reference project.

    Parameters
    ----------
    name
        Reference project directory name (for example, ``"basic-pytest"``).

    Returns
    -------
    Path
        Absolute path to ``examples/reference-projects/<name>``.

    """
    return repo_root() / "examples" / "reference-projects" / name
