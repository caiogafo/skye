---
component: router
codename: jet
---

# Requirements Document

## Introduction

The model router: configuration, fallbacks and health, over the models. The design and the tasks are in `design.md` and `tasks.md`; the owner's notes of 2026-11-07 on the `.skye` work are absorbed in `design.md`.

The requirements themselves live in `.kiro/steering/10-requirements.md`; each requirement below is one user story of this component, and each acceptance criterion is a pointer to the steering criterion it realizes (never a copy).

## Requirements

### Requirement 1: Router and model configuration

**User Story:** As a platform engineer, I want to configure model routing with fallbacks in code or in a `.skye` file, so that my applications stay available when a provider has issues and I do not hardcode secrets.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 17.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 17.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 17.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 17.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 17.5 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL realize Requirement 17.6 of #[[file:.kiro/steering/10-requirements.md]].
7. THE spec SHALL realize Requirement 17.7 of #[[file:.kiro/steering/10-requirements.md]].
8. THE spec SHALL honor decision D68 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 2: Tests

**User Story:** As a developer, I want an organized and sufficient test suite, so that I can trust the library and find the tests I need.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 23.3 of #[[file:.kiro/steering/10-requirements.md]].
