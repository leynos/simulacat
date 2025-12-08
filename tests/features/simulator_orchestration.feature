Feature: GitHub simulator orchestration
  The simulator orchestration manages the lifecycle of the
  GitHub API simulator process for test isolation.

  Scenario: Start simulator with empty configuration
    Given an empty simulator configuration
    When the simulator is started
    Then a listening event is received
    And the reported port is greater than zero

  Scenario: Stop simulator cleanly
    Given a running simulator
    When the simulator is stopped
    Then the simulator process has exited
