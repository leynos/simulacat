"""Shared fixtures for integration and behavioural tests."""

from __future__ import annotations

import shutil

import pytest

pytest_plugins = ["pytest_bdd", "simulacat.pytest_plugin"]


def _is_bun_available() -> bool:
    """Return True if bun is available in the environment."""
    return shutil.which("bun") is not None


bun_required = pytest.mark.skipif(
    not _is_bun_available(),
    reason="Bun is required for simulator tests",
)


@pytest.fixture(scope="session")
def bun_available() -> bool:
    """Check if bun is available in the environment."""
    return _is_bun_available()


@pytest.fixture
def require_bun(*, bun_available: bool) -> None:
    """Skip the current test if bun is not available."""
    if not bun_available:
        pytest.skip("Bun is required for simulator tests")
