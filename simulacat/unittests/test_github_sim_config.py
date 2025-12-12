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
import textwrap
import types
import typing as typ

import pytest

from simulacat.types import GitHubSimConfig

pytest_plugins = ["pytester"]

if typ.TYPE_CHECKING:
    from _pytest.pytester import Pytester


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
    assert github_sim_config["organizations"] == []
    assert github_sim_config["repositories"] == []
    assert github_sim_config["branches"] == []
    assert github_sim_config["blobs"] == []
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


@pytest.mark.parametrize(
    "github_sim_config",
    [
        typ.cast(
            "object",
            types.MappingProxyType({
                "users": [{"login": "proxy-user", "organizations": []}]
            }),
        ),
    ],
    indirect=True,
)
def test_fixture_accepts_mapping_and_normalizes_to_dict(
    github_sim_config: GitHubSimConfig,
) -> None:
    """The fixture accepts Mapping values and normalizes them into a dict."""
    assert isinstance(github_sim_config, dict)
    assert github_sim_config["users"][0]["login"] == "proxy-user"
    json.dumps(github_sim_config)


@pytest.mark.parametrize("github_sim_config", [None], indirect=True)
def test_indirect_parametrization_normalizes_none_to_empty_mapping(
    github_sim_config: GitHubSimConfig,
) -> None:
    """Passing None via indirect parametrization is treated as an empty config."""
    assert github_sim_config == {}


def test_indirect_parametrization_rejects_non_mapping(pytester: Pytester) -> None:
    """Indirect parametrization rejects values that are not mappings."""
    pytester.makepyfile(
        """
        import pytest


        @pytest.mark.parametrize("github_sim_config", ["nope"], indirect=True)
        def test_non_mapping(github_sim_config):
            assert False, "fixture should fail before reaching test body"
        """
    )
    result = pytester.runpytest("-q")
    result.assert_outcomes(errors=1)
    assert (
        "github_sim_config must be a mapping"
        in result.stdout.str() + result.stderr.str()
    )


def test_indirect_parametrization_rejects_non_string_keys(pytester: Pytester) -> None:
    """Indirect parametrization rejects mappings with non-string keys."""
    pytester.makepyfile(
        """
        import pytest


        @pytest.mark.parametrize("github_sim_config", [{1: "x"}], indirect=True)
        def test_non_string_keys(github_sim_config):
            assert False, "fixture should fail before reaching test body"
        """
    )
    result = pytester.runpytest("-q")
    result.assert_outcomes(errors=1)
    assert (
        "github_sim_config keys must be strings"
        in result.stdout.str() + result.stderr.str()
    )


def test_indirect_parametrization_rejects_non_json_serializable(
    pytester: Pytester,
) -> None:
    """Indirect parametrization rejects non-JSON-serializable configurations."""
    pytester.makepyfile(
        """
        import pytest


        @pytest.mark.parametrize(
            "github_sim_config",
            [{"users": [object()]}],
            indirect=True,
        )
        def test_non_json_serializable(github_sim_config):
            assert False, "fixture should fail before reaching test body"
        """
    )
    result = pytester.runpytest("-q")
    result.assert_outcomes(errors=1)
    assert (
        "github_sim_config must be JSON serializable"
        in result.stdout.str() + result.stderr.str()
    )


def test_package_scoped_override_via_conftest(pytester: Pytester) -> None:
    """A package-scoped conftest fixture overrides the plugin fixture."""
    pkg = pytester.path / "pkg_override"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "conftest.py").write_text(
        textwrap.dedent(
            """\
            import pytest


            @pytest.fixture(scope="package")
            def github_sim_config():
                return {"users": [{"login": "pkg-user", "organizations": []}]}
            """
        ),
        encoding="utf-8",
    )
    (pkg / "test_pkg_override.py").write_text(
        textwrap.dedent(
            """\
            def test_package_override_wins(pytestconfig, github_sim_config):
                assert pytestconfig.pluginmanager.hasplugin("simulacat")
                assert github_sim_config["users"][0]["login"] == "pkg-user"
            """
        ),
        encoding="utf-8",
    )

    result = pytester.runpytest(str(pkg), "-q")
    result.assert_outcomes(passed=1)
