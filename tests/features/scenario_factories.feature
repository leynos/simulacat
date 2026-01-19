Feature: Scenario factory helpers
  Scenario factories describe reusable GitHub layouts for simulator tests.
  Scenario: Single repository factory scenario
    Given a single repository scenario factory
    When the scenario is serialized for the simulator
    Then the configuration includes repository "alice/rocket"

  Scenario: Monorepo factory provides app branches
    Given a monorepo scenario with apps
    When the scenario is serialized for the simulator
    Then the configuration includes app branches

  Scenario: Scenario fragments can be merged
    Given two scenario fragments with shared owner
    When the scenario fragments are merged
    Then the merged scenario contains 2 repositories

  Scenario: Conflicting fragments raise an error
    Given two conflicting scenario fragments
    When the conflicting fragments are merged
    Then a scenario conflict error is reported
