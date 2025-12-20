Feature: GitHub simulator client fixture
  The github_simulator fixture starts a local GitHub API simulator process and
  yields a github3.py client configured to talk to it.

  Scenario: A github3 client can reach the simulator
    Given a github_sim_config fixture with 1 users
    When the github_simulator fixture is requested
    Then the github3 client is bound to the simulator
    And the simulator responds to an HTTP request

  Scenario: Repository lookup works with configured repos
    Given a github_sim_config fixture with a user and repositories
    When the github_simulator fixture is requested
    Then the github3 client can look up repository "alice/repo1"

  Scenario: Repository listing works for users
    Given a github_sim_config fixture with a user and repositories
    When the github_simulator fixture is requested
    Then the github3 client can list repositories for user "alice"
    And the repository listing includes "alice/repo1"

  Scenario: Repository listing works for organizations
    Given a github_sim_config fixture with a user and repositories
    When the github_simulator fixture is requested
    Then the github3 client can list repositories for organization "acme"
    And the repository listing includes "acme/orgrepo"

  Scenario: Issue and pull request retrieval works
    Given a github_sim_config fixture with a user and repositories
    When the github_simulator fixture is requested
    Then the github3 client can retrieve issue 1 for "alice/repo1"
    And the github3 client can retrieve pull request 1 for "alice/repo1"
