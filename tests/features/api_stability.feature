Feature: API stability and deprecation policy
  Step 4.2 establishes a predictable public API surface for downstream
  users and documents the deprecation lifecycle for API changes.

  Scenario: Public API symbols are registered with stability tiers
    Given the simulacat public API registry
    Then every symbol in the package __all__ has a stability tier
    And every registered fixture has a stability tier

  Scenario: Deprecation warnings include migration guidance
    Given a deprecated API entry with a replacement and guidance
    When a deprecation warning is emitted for the entry
    Then the warning is a SimulacatDeprecationWarning
    And the warning message includes the replacement name
    And the warning message includes migration guidance

  Scenario: Changelog links roadmap items to capabilities
    Given the changelog document
    Then the changelog references Phase 1 through Phase 4
    And the changelog describes behavioural changes at the step level

  Scenario: Users guide documents API stability and deprecation policy
    Given the users guide document
    Then the users guide includes an "API stability" section
    And the users guide includes a "Deprecation policy" section
