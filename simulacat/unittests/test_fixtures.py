"""Unit tests for simulacat pytest fixtures.

This module verifies the fixture functionality for configuring the GitHub API
simulator. Tests cover:

- Default configuration generation (default_github_sim_config)
- Configuration validation (is_json_serializable)
- Fixture scope and override behaviour

Fixtures
--------
- tmp_path: pytest built-in for temporary directories

Running tests
-------------
Execute these tests with::

    pytest simulacat/unittests/test_fixtures.py -v

Or run via make::

    make test

"""

from __future__ import annotations

import json
import typing as typ
from pathlib import Path

import pytest

if typ.TYPE_CHECKING:
    from simulacat.types import GitHubSimConfig


class TestDefaultGithubSimConfig:
    """Tests for the default_github_sim_config function."""

    @staticmethod
    def test_returns_empty_mapping() -> None:
        """The default configuration is an empty mapping."""
        from simulacat.config import default_github_sim_config

        config = default_github_sim_config()

        assert config == {}, f"Expected empty mapping, got {config}"

    @staticmethod
    def test_returns_dict_type() -> None:
        """The default configuration returns a dict instance."""
        from simulacat.config import default_github_sim_config

        config = default_github_sim_config()

        assert isinstance(config, dict), f"Expected dict, got {type(config)}"

    @staticmethod
    def test_is_json_serializable() -> None:
        """The default configuration can be serialized to JSON."""
        from simulacat.config import default_github_sim_config

        config = default_github_sim_config()

        try:
            serialized = json.dumps(config)
            assert serialized == "{}", f"Expected '{{}}', got {serialized}"
        except (TypeError, ValueError) as exc:
            pytest.fail(f"Failed to serialize config: {exc}")


class TestIsJsonSerializable:
    """Tests for the is_json_serializable validation function."""

    @staticmethod
    def test_accepts_empty_dict() -> None:
        """Empty dictionaries are serializable."""
        from simulacat.config import is_json_serializable

        assert is_json_serializable({}) is True

    @staticmethod
    def test_accepts_nested_dicts() -> None:
        """Nested dictionaries with JSON types are serializable."""
        from simulacat.config import is_json_serializable

        config = {
            "users": [{"login": "test", "organizations": []}],
            "count": 42,
            "enabled": True,
            "ratio": 1.5,
            "nothing": None,
        }

        assert is_json_serializable(config) is True

    @staticmethod
    def test_rejects_path_objects() -> None:
        """Path objects are not JSON serializable."""
        from simulacat.config import is_json_serializable

        config = {"path": Path("/example/test")}

        assert is_json_serializable(config) is False

    @staticmethod
    def test_rejects_functions() -> None:
        """Function objects are not JSON serializable."""
        from simulacat.config import is_json_serializable

        config = {"callback": lambda x: x}

        assert is_json_serializable(config) is False

    @staticmethod
    def test_rejects_custom_objects() -> None:
        """Custom class instances are not JSON serializable."""
        from simulacat.config import is_json_serializable

        class Custom:
            pass

        config = {"obj": Custom()}

        assert is_json_serializable(config) is False


class TestGithubSimConfigType:
    """Tests for the GitHubSimConfig type alias."""

    @staticmethod
    def test_type_alias_is_mapping() -> None:
        """GitHubSimConfig is a mapping type."""
        # Verify the type is accessible and is a type alias
        # This is a static check; at runtime we verify it accepts dict
        config: GitHubSimConfig = {}
        assert isinstance(config, dict)

    @staticmethod
    def test_type_accepts_nested_structures() -> None:
        """GitHubSimConfig accepts nested JSON-like structures."""
        config: GitHubSimConfig = {
            "users": [{"login": "test", "organizations": ["org1"]}],
            "repositories": [{"owner": "test", "name": "repo"}],
        }
        assert "users" in config
        assert "repositories" in config


class TestMergeConfigs:
    """Tests for configuration merging utility."""

    @staticmethod
    def test_no_args_returns_empty() -> None:
        """Calling merge_configs() with no arguments returns empty dict."""
        from simulacat.config import merge_configs

        result = merge_configs()

        assert result == {}

    @staticmethod
    def test_empty_configs_return_empty() -> None:
        """Merging empty configs returns empty dict."""
        from simulacat.config import merge_configs

        result = merge_configs({}, {})

        assert result == {}

    @staticmethod
    def test_later_config_wins() -> None:
        """Later configurations override earlier ones."""
        from simulacat.config import merge_configs

        base = {"users": [{"login": "base"}]}
        override = {"users": [{"login": "override"}]}

        result = merge_configs(base, override)

        assert result["users"][0]["login"] == "override"

    @staticmethod
    def test_preserves_unoverridden_keys() -> None:
        """Keys not in override are preserved from base."""
        from simulacat.config import merge_configs

        base = {"users": [{"login": "base"}], "organizations": []}
        override = {"users": [{"login": "override"}]}

        result = merge_configs(base, override)

        assert "organizations" in result
        assert result["organizations"] == []

    @staticmethod
    def test_multiple_configs_merge_in_order() -> None:
        """Multiple configs merge left to right."""
        from simulacat.config import merge_configs

        first = {"a": 1}
        second = {"b": 2}
        third = {"a": 3, "c": 4}

        result = merge_configs(first, second, third)

        assert result == {"a": 3, "b": 2, "c": 4}


class TestFixtureRegistration:
    """Tests verifying the modules are properly structured."""

    @staticmethod
    def test_config_module_exists() -> None:
        """The config module exists and can be imported."""
        from simulacat import config

        assert hasattr(config, "default_github_sim_config")
        assert hasattr(config, "is_json_serializable")
        assert hasattr(config, "merge_configs")

    @staticmethod
    def test_fixtures_module_exists() -> None:
        """The fixtures module exists and can be imported."""
        from simulacat import fixtures

        assert hasattr(fixtures, "github_sim_config")
        assert hasattr(fixtures, "simulacat_single_repo")
        assert hasattr(fixtures, "simulacat_empty_org")

    @staticmethod
    def test_github_sim_config_is_callable() -> None:
        """The github_sim_config fixture function is callable."""
        from simulacat.fixtures import github_sim_config

        # The fixture function should be callable
        assert callable(github_sim_config)

    @staticmethod
    def test_simulacat_single_repo_fixture_is_callable() -> None:
        """The simulacat_single_repo fixture function is callable."""
        from simulacat.fixtures import simulacat_single_repo

        assert callable(simulacat_single_repo)

    @staticmethod
    def test_simulacat_empty_org_fixture_is_callable() -> None:
        """The simulacat_empty_org fixture function is callable."""
        from simulacat.fixtures import simulacat_empty_org

        assert callable(simulacat_empty_org)


def test_simulacat_single_repo_fixture_returns_expected_config(
    request: pytest.FixtureRequest,
) -> None:
    """simulacat_single_repo returns a config with a demo repository."""
    config = request.getfixturevalue("simulacat_single_repo")

    assert isinstance(config, dict)
    repos = typ.cast("list[dict[str, typ.Any]]", config.get("repositories", []))
    assert len(repos) == 1
    repo = repos[0]
    assert repo.get("owner") == "octocat"
    assert repo.get("name") == "demo-repo"
    assert repo.get("default_branch") == "main"

    users = typ.cast("list[dict[str, typ.Any]]", config.get("users", []))
    assert len(users) == 1
    assert users[0].get("login") == "octocat"

    orgs = typ.cast("list[dict[str, typ.Any]]", config.get("organizations", []))
    assert orgs == []

    branches = typ.cast("list[dict[str, typ.Any]]", config.get("branches", []))
    assert any(
        branch.get("owner") == "octocat"
        and branch.get("repository") == "demo-repo"
        and branch.get("name") == "main"
        for branch in branches
    )


def test_simulacat_empty_org_fixture_returns_expected_config(
    request: pytest.FixtureRequest,
) -> None:
    """simulacat_empty_org returns a config with an empty organisation."""
    config = request.getfixturevalue("simulacat_empty_org")

    assert isinstance(config, dict)
    orgs = typ.cast("list[dict[str, typ.Any]]", config.get("organizations", []))
    assert len(orgs) == 1
    assert orgs[0].get("login") == "octo-org"
    assert config.get("repositories", []) == []
    assert config.get("users", []) == []
