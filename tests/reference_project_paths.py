"""Shared path helpers for Step 3.2 reference project tests."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the repository root from test package location."""
    return Path(__file__).resolve().parents[1]


def reference_project_path(name: str) -> Path:
    """Return the absolute path to a named reference project."""
    return repo_root() / "examples" / "reference-projects" / name
