Feature: GitHub simulator client fixture
  The github_simulator fixture starts a local GitHub API simulator process and
  yields a github3.py client configured to talk to it.

  Scenario: A github3 client can reach the simulator
    Given a github_sim_config fixture with 1 users
    When the github_simulator fixture is requested
    Then the github3 client is bound to the simulator
    And the simulator responds to an HTTP request

