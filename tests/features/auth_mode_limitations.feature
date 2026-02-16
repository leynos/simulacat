Feature: Authentication mode limitations
  The simulator does not validate tokens, enforce permissions, or
  implement rate limiting. These scenarios document observable
  limitations compared with real GitHub behaviour. See the
  "Authentication mode limitations" section in the users' guide for
  the full reference.

  Scenario: arbitrary token values pass scenario validation
    Given a scenario with a non-standard token value
    When the limitation scenario is validated
    Then the scenario passes validation without error

  Scenario: token permissions are not included in the serialized simulator configuration
    Given a scenario with a token that has permissions and repository scoping
    When the limitation scenario is validated and serialized
    Then the serialized output does not contain token metadata

  Scenario: token repository visibility is not included in the serialized simulator configuration
    Given a scenario with a token that has repository visibility metadata
    When the limitation scenario is validated and serialized
    Then the serialized output does not contain visibility metadata

  Scenario: GitHub App and installation fields are excluded from simulator output
    Given a scenario with a GitHub App and an installation with permissions
    When the limitation scenario is validated and serialized
    Then the serialized output does not contain app or installation fields

  Scenario: an installation access token resolves as a literal string value
    Given a scenario with an installation that declares a static access token
    When the limitation scenario auth token is resolved
    Then the resolved token is the literal access token string
