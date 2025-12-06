"""Step definitions for simulator orchestration behavioural tests.

This module provides pytest-bdd step bindings for testing the simulator
orchestration functionality. The steps exercise starting, stopping, and
configuring the GitHub API simulator process.

Feature files
-------------
The step definitions bind to scenarios in:
- tests/features/simulator_orchestration.feature

Fixtures
--------
- simulator_context: Provides shared state for simulator scenarios with
  automatic cleanup.

Running tests
-------------
Execute the behavioural tests with::

    pytest tests/steps/test_simulator_orchestration.py -v

Or run all tests including these::

    make test

"""

from __future__ import annotations

import typing as typ

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from simulacat.orchestration import start_sim_process, stop_sim_process
from tests import conftest as test_conftest

pytestmark = test_conftest.bun_required

if typ.TYPE_CHECKING:
    import subprocess  # noqa: S404  # simulacat#123: typing-only reference; no runtime process creation
    from pathlib import Path

scenarios("../features/simulator_orchestration.feature")


class SimulatorContext(typ.TypedDict):
    """Context object for simulator state during test scenarios."""

    config: dict[str, typ.Any]
    proc: subprocess.Popen[str] | None
    port: int | None
    tmpdir: Path


@pytest.fixture
def simulator_context(tmp_path: Path) -> typ.Generator[SimulatorContext, None, None]:
    """Provide a context for simulator scenarios with cleanup."""
    ctx: SimulatorContext = {
        "config": {},
        "proc": None,
        "port": None,
        "tmpdir": tmp_path,
    }
    yield ctx
    if ctx["proc"] is not None:
        stop_sim_process(ctx["proc"])


@given("an empty simulator configuration")
def given_empty_config(simulator_context: SimulatorContext) -> None:
    """Set up an empty configuration for the simulator."""
    simulator_context["config"] = {}


@given("a running simulator")
def given_running_simulator(simulator_context: SimulatorContext) -> None:
    """Start a simulator with empty configuration."""
    simulator_context["config"] = {}
    proc, port = start_sim_process(
        simulator_context["config"],
        simulator_context["tmpdir"],
    )
    simulator_context["proc"] = proc
    simulator_context["port"] = port


@given(parsers.parse("a simulator configuration with {count:d} users"))
def given_config_with_users(
    simulator_context: SimulatorContext,
    count: int,
) -> None:
    """Set up a configuration with the specified number of users."""
    simulator_context["config"] = {
        "users": [{"login": f"user{i}", "organizations": []} for i in range(count)],
        "organizations": [],
        "repositories": [],
        "branches": [],
        "blobs": [],
    }


@when("the simulator is started")
def when_simulator_started(simulator_context: SimulatorContext) -> None:
    """Start the simulator with the current configuration."""
    proc, port = start_sim_process(
        simulator_context["config"],
        simulator_context["tmpdir"],
    )
    simulator_context["proc"] = proc
    simulator_context["port"] = port


@when("the simulator is stopped")
def when_simulator_stopped(simulator_context: SimulatorContext) -> None:
    """Stop the currently running simulator."""
    proc = simulator_context["proc"]
    assert proc is not None, "No simulator process to stop"
    stop_sim_process(proc)


@then("a listening event is received")
def then_listening_event_received(simulator_context: SimulatorContext) -> None:
    """Verify that the simulator reported a listening event."""
    assert simulator_context["port"] is not None


@then("the reported port is greater than zero")
def then_port_greater_than_zero(simulator_context: SimulatorContext) -> None:
    """Verify that the reported port is a valid port number."""
    port = simulator_context["port"]
    assert port is not None
    assert port > 0


@then("the simulator process has exited")
def then_process_exited(simulator_context: SimulatorContext) -> None:
    """Verify that the simulator process has terminated."""
    proc = simulator_context["proc"]
    assert proc is not None
    assert proc.poll() is not None
