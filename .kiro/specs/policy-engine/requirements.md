# Requirements Document: Policy Engine

## Introduction

The Policy Engine decides whether a principal may perform an action on a resource. Its model is inspired by Cedar, the authorization language from AWS: rules are permit or forbid statements over a principal, an action, a resource and a context. Anything that is not permitted is denied, and a forbid always wins. Nimbus implements a small subset of that model in pure Python with no dependency, so it fits in a Lambda package and can run inside the Gateway, the agent loop and the model router.

Status: requirements draft, to be reviewed before design. Items marked OPEN are decisions for the owner.

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

1. THE Policy Engine SHALL represent a policy as an effect (permit or forbid), a scope over principal, action and resource, and optional when and unless conditions over context and attributes
2. THE Policy Engine SHALL allow a scope element to be any, an exact entity, a set of entities, or a membership test (in a group or collection)
3. THE Policy Engine SHALL give every policy an identifier and optional annotations (description, owner)

### Requirement 2: Evaluation semantics

**User Story:** As a security owner, I want predictable decisions.

#### Acceptance Criteria

1. THE Policy Engine SHALL deny a request unless at least one permit policy matches
2. WHEN any forbid policy matches, THE Policy Engine SHALL deny the request, whatever the permits
3. THE Policy Engine SHALL return the decision and the identifiers of the policies that determined it
4. THE Policy Engine SHALL evaluate without side effects and give the same decision for the same inputs
5. WHEN a condition cannot be evaluated (a missing attribute, a type error), THE Policy Engine SHALL treat that policy as not matching and record the error

### Requirement 3: Conditions

**User Story:** As a security owner, I want conditions on attributes and context, so that rules can depend on more than names.

#### Acceptance Criteria

1. THE Policy Engine SHALL support comparisons, boolean operators, set membership, attribute presence tests, string prefix and suffix tests, and membership in an entity hierarchy
2. THE Policy Engine SHALL NOT support loops, user-defined functions, I/O or regular expressions in conditions
3. THE Policy Engine SHALL bound evaluation time by the size of the policy set, with no unbounded recursion

### Requirement 4: Entities

**User Story:** As a platform engineer, I want to describe who and what exists, so that policies can use groups and attributes.

#### Acceptance Criteria

1. THE Policy Engine SHALL take entities from an entity provider supplied by the caller, as identifier, attributes and parents
2. THE Policy Engine SHALL support principals from IAM identities and from JWT claims, mapped by a configurable function
3. THE Policy Engine SHALL treat an unknown entity as having no attributes and no parents

### Requirement 5: Policy representation

**User Story:** As a security owner, I want to write policies in a format I can review and store.

#### Acceptance Criteria

1. THE Policy Engine SHALL load policies from JSON and TOML using the standard library
2. THE Policy Engine SHALL define a text syntax close to Cedar for the same policies (OPEN: first release or later, and how much of the Cedar grammar)
3. THE Policy Engine SHALL give clear errors with the policy identifier and the position of the problem
4. THE Policy Engine SHALL export a policy set to the representation it was loaded from, without changing its meaning

### Requirement 6: Schema and validation

**User Story:** As a platform engineer, I want mistakes found when policies load, not when a request is denied.

#### Acceptance Criteria

1. THE Policy Engine SHALL validate policies against a schema listing entity types, actions and attributes
2. THE Policy Engine SHALL build the schema from the Gateway Registry, so that every tool is an action
3. WHEN a policy names an unknown action or attribute, THE Policy Engine SHALL reject the policy set at load time

### Requirement 7: Integration points

**User Story:** As a developer, I want one engine for every place that needs a decision.

#### Acceptance Criteria

1. THE Policy Engine SHALL provide one interface that takes principal, action, resource and context and returns a decision
2. THE Gateway SHALL use it for tool listing, tool discovery and tool calls
3. THE ModelRouter SHALL be able to use it to restrict which models and regions a principal may use
4. THE agent loop SHALL be able to use it through a hook provider at the policy check operation
5. THE memory systems SHALL be able to use it for read and write access

### Requirement 8: Enforcement modes

**User Story:** As a security owner, I want to try a policy before enforcing it.

#### Acceptance Criteria

1. THE Policy Engine SHALL support enforce and log-only modes, set per policy set
2. WHEN in log-only mode, THE Policy Engine SHALL return allow and record the decision it would have made

### Requirement 9: Loading and versions

**User Story:** As a platform engineer, I want to change policies without redeploying.

#### Acceptance Criteria

1. THE Policy Engine SHALL load a policy set from a file, an environment variable or an external store (DynamoDB through boto3 in Lambda)
2. THE Policy Engine SHALL cache a loaded policy set with a time to live and refresh it inside the request that notices the expiry, not in a background thread
3. THE Policy Engine SHALL give each policy set a version and a content hash and include both in every decision log

### Requirement 10: Observability

**User Story:** As a security owner, I want every decision recorded.

#### Acceptance Criteria

1. THE Policy Engine SHALL write one structured JSON log line per decision with principal, action, resource, decision, determining policies, policy set version and latency
2. THE Policy Engine SHALL NOT log context values unless a setting enables it
3. THE Policy Engine SHALL publish counters for allow, deny and error through the observability module

### Requirement 11: Dependencies and budgets

**User Story:** As a maintainer, I want the engine to stay light.

#### Acceptance Criteria

1. THE Policy Engine SHALL use only the standard library, with no compiled dependency and no third-party import at module level
2. THE Policy Engine SHALL have an entry in budgets.toml for import time, with a limit on evaluation time for a typical policy set (OPEN: values)
3. THE Policy Engine SHALL pass the existing budget tests

### Requirement 12: Cedar alignment

**User Story:** As a security owner, I want to move to Cedar later without rewriting policies.

#### Acceptance Criteria

1. THE Policy Engine SHALL document which parts of Cedar it implements and which it leaves out
2. THE Policy Engine SHALL keep the permit, forbid, scope and condition semantics identical to Cedar for the parts it implements
3. THE Policy Engine SHALL be tested with policies and requests whose expected decisions come from the Cedar documentation (OPEN: availability and licence of an official conformance suite)

## Open questions for the owner

1. Text syntax in the first release, or JSON and TOML first?
2. How closely do we promise Cedar compatibility?
3. Identity: map IAM roles and JWT claims to principals in one fixed way, or let each application define it?
4. Defaults: policy set cache lifetime and the evaluation time limit.
