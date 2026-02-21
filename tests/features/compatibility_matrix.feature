Feature: Compatibility matrix policy and CI coverage
  Step 4.1 defines supported dependency ranges and verifies them through
  reference-suite matrix execution.

  Scenario: Compatibility workflow covers multiple Python versions and reference suites
    Given the compatibility matrix workflow file
    Then the workflow includes Python versions "3.12" and "3.13"
    And the workflow executes both reference project suites

  Scenario: Compatibility workflow covers two github3.py major tracks
    Given the compatibility matrix workflow file
    Then the workflow includes github3.py constraint ">=3.2.0,<4.0.0"
    And the workflow includes github3.py constraint ">=4.0.0,<5.0.0"

  Scenario: Users guide documents compatibility policy and workarounds
    Given the users guide document
    Then the users guide includes a "Compatibility matrix" section
    And the users guide includes a "Known incompatibilities and workarounds" section
    And the users guide documents Python, github3.py, Node.js, and simulator ranges
