Feature: github_simulator authentication headers

  Scenario: an auth token sets the Authorization header
    Given a github_sim_config fixture with an auth token
    When the github_simulator fixture is requested
    Then the github3 client Authorization header is "token test-token"

  Scenario: no token leaves the Authorization header unset
    Given a github_sim_config fixture without an auth token
    When the github_simulator fixture is requested
    Then the github3 client Authorization header is absent
