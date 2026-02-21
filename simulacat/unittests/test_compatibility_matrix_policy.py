"""Unit tests for Step 4.1 compatibility policy contracts."""

from __future__ import annotations

import re

from packaging.version import Version

from simulacat.compatibility_policy import (
    COMPATIBILITY_POLICY,
    KNOWN_INCOMPATIBILITIES,
)


def test_policy_covers_required_dependencies() -> None:
    """Compatibility policy includes all Step 4.1 dependency dimensions."""
    assert set(COMPATIBILITY_POLICY) == {
        "python",
        "github3.py",
        "node.js",
        "@simulacrum/github-api-simulator",
    }


def test_minimum_is_not_newer_than_recommended_for_semver_values() -> None:
    """Minimum semantic versions do not exceed recommended versions."""
    semver_dependencies = ("python", "github3.py", "@simulacrum/github-api-simulator")
    for dependency_name in semver_dependencies:
        policy = COMPATIBILITY_POLICY[dependency_name]
        assert Version(policy.minimum_version) <= Version(policy.recommended_version), (
            f"Expected minimum <= recommended for {dependency_name}"
        )


def test_nodejs_policy_uses_major_x_format() -> None:
    """Node.js policy declares major tracks in the documented ``<major>.x`` form."""
    policy = COMPATIBILITY_POLICY["node.js"]
    major_x_pattern = re.compile(r"^\d+\.x$")
    assert major_x_pattern.match(policy.minimum_version), (
        "Expected Node.js minimum version to use <major>.x format"
    )
    assert major_x_pattern.match(policy.recommended_version), (
        "Expected Node.js recommended version to use <major>.x format"
    )


def test_known_incompatibilities_have_signature_and_workaround() -> None:
    """Known incompatibilities include reproducible signatures and workarounds."""
    assert KNOWN_INCOMPATIBILITIES, "Expected at least one known incompatibility"
    for incompatibility in KNOWN_INCOMPATIBILITIES:
        assert incompatibility.failure_signature.strip(), (
            "Expected known incompatibility to include failure signature"
        )
        assert incompatibility.workaround.strip(), (
            "Expected known incompatibility to include workaround"
        )
