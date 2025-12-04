"""Shared fixtures for integration and behavioral tests."""

from __future__ import annotations

import pytest

pytest_plugins = ["pytest_bdd"]


@pytest.fixture(scope="session")
def bun_available() -> bool:
    """Check if bun is available in the environment."""
    import shutil

    return shutil.which("bun") is not None
