"""Unit tests for the github_sim_config pytest fixture.

These tests verify that simulacat exposes a JSON-serializable configuration
fixture with sensible defaults and override semantics.

Running tests
-------------
Execute these tests with::

    pytest simulacat/unittests/test_github_sim_config.py -v

Or run via make::

    make test

"""

from __future__ import annotations

import json
import typing as typ

import pytest

from simulacat.types import GitHubSimConfig


def test_github_sim_config_typed_dict_has_expected_keys() -> None:
    """GitHubSimConfig exposes the simulator top-level schema keys."""
    hints = typ.get_type_hints(GitHubSimConfig)
    assert set(hints) == {
        "users",
        "organizations",
        "repositories",
        "branches",
        "blobs",
    }


def test_default_fixture_returns_empty_mapping(
    github_sim_config: GitHubSimConfig,
) -> None:
    """The default github_sim_config fixture is an empty JSON mapping."""
    assert github_sim_config == {}
    json.dumps(github_sim_config)


@pytest.mark.parametrize(
    "github_sim_config",
    [
        {
            "users": [
                {
                    "login": "alice",
                    "organizations": [],
                }
            ]
        }
    ],
    indirect=True,
)
def test_indirect_parametrization_overrides_fixture(
    github_sim_config: GitHubSimConfig,
) -> None:
    """Indirect parametrization replaces the fixture value per test."""
    assert github_sim_config["users"][0]["login"] == "alice"
    json.dumps(github_sim_config)


class TestModuleOverride:
    """Override semantics at module scope."""

    @staticmethod
    @pytest.fixture
    def github_sim_config() -> GitHubSimConfig:
        """Provide a module-level override for github_sim_config."""
        return {"users": [{"login": "module-user", "organizations": []}]}

    @staticmethod
    def test_module_fixture_override_wins(github_sim_config: GitHubSimConfig) -> None:
        """A fixture in the test module overrides the plugin fixture."""
        assert github_sim_config["users"][0]["login"] == "module-user"


def test_package_scope_override(pytester: pytest.Pytester) -> None:
    """A package-scoped fixture in conftest.py overrides the plugin fixture."""
    pytester.makeconftest(
        """
        import pytest

        pytest_plugins = ["simulacat.pytest_plugin"]


        @pytest.fixture(scope="package")
        def github_sim_config():
            return {"users": [{"login": "pkg-user", "organizations": []}]}
        """
    )
    pytester.makepyfile(
        """
        def test_package_override(github_sim_config):
            assert github_sim_config["users"][0]["login"] == "pkg-user"
        """
    )

    result = pytester.runpytest("-q")
    result.assert_outcomes(passed=1)
