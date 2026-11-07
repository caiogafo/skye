---
component: base
codename: stratus
---

# Requirements Document

## Introduction

Foundation: the core models, errors, configuration and every Port, in the standard library only, with no I/O. This spec is at the requirements stage: the design and the tasks come after the requirements are approved.

The requirements themselves live in `.kiro/steering/10-requirements.md`; each requirement below is one user story of this component, and each acceptance criterion is a pointer to the steering criterion it realizes (never a copy).

## Requirements

### Requirement 1: `base`

**User Story:** As a maintainer, I want `base` to be a small standard-library foundation, so that everything depends on something that installs nothing and does no I/O.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 3.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 3.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 3.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 3.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 3.5 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 2: Interfaces and the standard response

**User Story:** As a component developer, I want well-defined interfaces and one response format whatever the provider, so that I can build compatible components and write provider-agnostic code.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 16.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 16.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 16.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 16.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 16.5 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 3: Errors and logging

**User Story:** As a developer, I want clear, actionable errors and structured logs, so that I can diagnose problems and plug the library into my observability stack.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 18.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 18.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 18.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 18.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 4: Token usage and cost

**User Story:** As a product manager, I want token usage and estimated cost for every call, so that I can monitor and control spending.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 19.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 19.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 19.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 5: Configuration

**User Story:** As a DevOps engineer, I want to configure the library from code or files with predictable precedence, so that I can manage environments without code changes.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 20.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 20.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 20.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 20.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 6: Type safety

**User Story:** As a Python developer, I want complete type hints and field-level validation errors, so that I catch mistakes early and get IDE support.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 21.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 21.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 21.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 7: The `.skye` parser

**User Story:** As a developer, and as an AI agent writing configuration for one, I want one parser in `base` that reads the `.skye` language from text and reports every error with its place and a fix, so that routers, flows and prompts are read the same way and a mistake is easy to repair.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 54.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 54.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 54.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 54.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 54.5 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL realize Requirement 54.8 of #[[file:.kiro/steering/10-requirements.md]].
7. THE spec SHALL realize Requirement 54.11 of #[[file:.kiro/steering/10-requirements.md]].
