"""Compatibility policy for supported dependency versions.

This module defines the canonical dependency compatibility policy used by
documentation and tests.
"""

from __future__ import annotations

import dataclasses as dc
from types import MappingProxyType


@dc.dataclass(frozen=True, slots=True)
class DependencyCompatibility:
    """Version policy for a dependency."""

    minimum_version: str
    recommended_version: str
    supported_range: str
    rationale: str


@dc.dataclass(frozen=True, slots=True)
class KnownIncompatibility:
    """Known incompatible dependency combination and workaround."""

    dependency_name: str
    affected_versions: str
    failure_signature: str
    workaround: str


COMPATIBILITY_POLICY = MappingProxyType({
    "python": DependencyCompatibility(
        minimum_version="3.12",
        recommended_version="3.13",
        supported_range=">=3.12,<3.14",
        rationale=(
            "Packaging metadata and CI target Python 3.12 and 3.13 as the "
            "supported range."
        ),
    ),
    "github3.py": DependencyCompatibility(
        minimum_version="3.2.0",
        recommended_version="4.0.1",
        supported_range=">=3.2.0,<5.0.0",
        rationale=(
            "Compatibility tests pass on both github3.py 3.x and 4.x major tracks."
        ),
    ),
    "node.js": DependencyCompatibility(
        minimum_version="20.x",
        recommended_version="22.x",
        supported_range="20.x-22.x",
        rationale=(
            "Node.js majors 20 and 22 are documented and aligned with CI "
            "runtime support."
        ),
    ),
    "@simulacrum/github-api-simulator": DependencyCompatibility(
        minimum_version="0.6.2",
        recommended_version="0.6.3",
        supported_range=">=0.6.2,<0.7.0",
        rationale=(
            "Patch releases 0.6.2 and newer in the 0.6 line retain the "
            "required simulator API surface."
        ),
    ),
})


KNOWN_INCOMPATIBILITIES = (
    KnownIncompatibility(
        dependency_name="github3.py",
        affected_versions=">=5.0.0,<6.0.0",
        failure_signature=(
            "ERROR: Could not find a version that satisfies the requirement "
            "github3.py>=5.0.0,<6.0.0"
        ),
        workaround=(
            "Use github3.py >=3.2.0,<5.0.0. The compatibility matrix validates "
            "3.x and 4.x majors."
        ),
    ),
    KnownIncompatibility(
        dependency_name="python",
        affected_versions="<3.12",
        failure_signature=("ERROR: Package 'simulacat' requires a different Python"),
        workaround=(
            "Use Python 3.12 or 3.13. These are the supported versions in the "
            "compatibility matrix."
        ),
    ),
)
