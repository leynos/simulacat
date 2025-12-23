Feature: Scenario configuration helpers
  Scenario: Single repository with default branch metadata
    Given a scenario with a single repository and default branch
    When the scenario is serialized for the simulator
    Then the configuration includes repository "alice/rocket" with default branch "main"
    And the configuration includes branch "main" for "alice/rocket"

  Scenario: Multiple repositories with mixed visibility
    Given a scenario with public and private repositories
    When the scenario is serialized for the simulator
    Then the configuration marks repository "alice/public-repo" as public
    And the configuration marks repository "alice/private-repo" as private

  Scenario: Issues and pull requests are serialized when requested
    Given a scenario with issues and pull requests
    When the scenario is serialized for the simulator with issues and pull requests
    Then the configuration includes 1 issue
    And the configuration includes 1 pull request
