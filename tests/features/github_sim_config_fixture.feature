Feature: github_sim_config fixture
  The github_sim_config fixture provides simulator configuration that can be
  overridden at function, module, and package scopes.

  Background:
    Given the pytest framework is available

  Scenario: Default configuration is an empty mapping
    When the github_sim_config fixture is requested without overrides
    Then it returns an empty mapping

  Scenario: Configuration is JSON-serializable
    Given a github_sim_config with test data
    When the configuration is serialized to JSON
    Then serialization succeeds without error

  Scenario: Function-scope override takes precedence
    Given a module-level github_sim_config override
    And a function-level github_sim_config override
    When the github_sim_config fixture is resolved
    Then the function-level configuration is used

  Scenario: Module-scope override applies to all tests in module
    Given a module-level github_sim_config override with users
    When multiple tests request github_sim_config
    Then all tests receive the module-level configuration
