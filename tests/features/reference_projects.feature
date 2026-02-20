Feature: Reference projects for CI usage
  Step 3.2 provides minimal reference projects that demonstrate running
  simulacat-based pytest suites in CI with Python and Node.js tooling.

  Scenario: The basic reference project pytest suite runs
    Given the reference project "basic-pytest"
    When the project's pytest suite is executed
    Then the suite command succeeds

  Scenario: The authenticated reference project pytest suite runs
    Given the reference project "authenticated-pytest"
    When the project's pytest suite is executed
    Then the suite command succeeds

  Scenario: Reference project workflows use Python and Node.js setup actions
    Given the reference project "basic-pytest"
    Then the workflow includes setup-python and setup-node actions
    When the reference project is switched to "authenticated-pytest"
    Then the workflow includes setup-python and setup-node actions
