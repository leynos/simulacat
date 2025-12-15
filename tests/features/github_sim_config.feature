Feature: GitHub simulator configuration fixture
  The github_sim_config fixture declares GitHub simulator state in Python tests.

  Scenario: Default configuration is empty
    When the github_sim_config fixture is requested
    Then the configuration is an empty mapping
    And the configuration can be serialized to JSON

  Scenario: Configuration can include users
    Given a github_sim_config fixture with 2 users
    When the github_sim_config fixture is requested
    Then the configuration contains 2 users
    And the configuration can be serialized to JSON

