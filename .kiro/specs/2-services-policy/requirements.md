---
component: policy
codename: isobar
previous_name: policy-engine
---

# Requirements Document

## Introduction

The Policy Engine decides whether a principal may perform an action on a resource. Its model is inspired by Cedar, the authorization language from AWS: rules are permit or forbid statements over a principal, an action, a resource and a context. Anything that is not permitted is denied, and a forbid always wins. Skye implements a small subset of that model in pure Python with no dependency, so it fits in a Lambda package and can run inside the Gateway, the agent loop and the model router.

Status: requirements draft, to be reviewed before design. Items marked OPEN are decisions for the owner.

The requirements themselves live in `.kiro/steering/10-requirements.md`; each requirement below is one user story of this component, and each acceptance criterion is a pointer to the steering criterion it realizes (never a copy). Questions that were open in the former text are in `.kiro/steering/12-decisions.md`.

## Glossary

- **Principal**: The caller on whose behalf something is done (a user, a service or an agent run)
- **Action**: What is being attempted (call a tool, list tools, use a model, read a memory)
- **Resource**: What the action is applied to (a tool, a model, a memory store, an MCP server)
- **Context**: Facts about the request (time, source, arguments, operation tags)
- **Entity**: A principal or a resource with an identifier, attributes and parents (groups or collections)
- **Policy**: One permit or forbid statement with a scope and optional conditions
- **Policy set**: A versioned collection of policies evaluated together
- **Decision**: Allow or deny, with the policies that determined it
- **Enforcement mode**: Enforce (the decision is applied) or log-only (the decision is recorded but not applied)

## Requirements

### Requirement 1: Policy model

**User Story:** As a security owner, I want rules expressed as permit and forbid, so that access is explicit and reviewable.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 35.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 35.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 35.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 2: Evaluation semantics

**User Story:** As a security owner, I want predictable decisions, so that the same request always gets the same answer.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 35.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 35.5 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 35.6 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 35.7 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 3: Conditions

**User Story:** As a security owner, I want conditions on attributes and context, so that rules can depend on more than names.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 35.8 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 35.9 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 35.10 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 4: Entities

**User Story:** As a platform engineer, I want to describe who and what exists, so that policies can use groups and attributes.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 36.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 36.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 36.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 5: Policy representation

**User Story:** As a security owner, I want to write policies in a format I can review and store, so that changes go through review.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 36.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 36.5 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 36.6 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 36.7 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 6: Schema and validation

**User Story:** As a platform engineer, I want mistakes found when policies load, not when a request is denied, so that a bad policy never reaches production.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 36.8 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 36.9 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 7: Integration points

**User Story:** As a developer, I want one engine for every place that needs a decision, so that access is enforced the same way everywhere.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 37.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 37.2 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 8: Enforcement modes

**User Story:** As a security owner, I want to try a policy before enforcing it, so that I see its effect without blocking anyone.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 37.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 9: Loading and versions

**User Story:** As a platform engineer, I want to change policies without redeploying, so that a fix does not wait for a release.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 37.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 37.5 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 37.6 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 10: Observability

**User Story:** As a security owner, I want every decision recorded, so that I can explain why a request was allowed or denied.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 37.7 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 37.8 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 11: Dependencies and budgets

**User Story:** As a maintainer, I want the engine to stay light, so that it fits a Lambda package.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 38.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 38.2 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 12: Cedar alignment

**User Story:** As a security owner, I want to move to Cedar later without rewriting policies, so that today's choice does not lock me in.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 38.3 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 38.4 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 38.5 of #[[file:.kiro/steering/10-requirements.md]].
