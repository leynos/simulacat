Feature: GitHub App installation metadata
  GitHub App and installation configuration helpers describe app metadata
  and per-installation access for test scenarios. The simulator does not
  enforce these; they are client-side metadata only.

  Scenario: a GitHub App scenario validates and serializes
    Given a scenario with a GitHub App and installation
    When the scenario is validated and serialized
    Then the serialized configuration does not include app metadata

  Scenario: an app installation with an access token resolves for auth
    Given a scenario with a GitHub App installation that has an access token
    When the auth token is resolved
    Then the resolved token matches the installation access token

  Scenario: app scenarios can be merged with repository scenarios
    Given a GitHub App scenario and a repository scenario
    When the scenarios are merged
    Then the merged scenario contains the app and the repository

  Scenario: an invalid installation reference raises a validation error
    Given a scenario with an installation referencing an undefined app
    When the scenario is validated
    Then a validation error about the app reference is raised
