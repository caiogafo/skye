---
component: gateway
---

# Requirements Document

## Introduction

The Gateway feature lets a Skye agent use tools without carrying a fixed list of them. The agent talks to one endpoint that speaks the Model Context Protocol (MCP). For each operation in progress, the Gateway registers and exposes only the tools that operation needs, and checks every listing and every call against the policy engine. It is inspired by Amazon Bedrock AgentCore Gateway (targets, inbound and outbound authorization, tool search, policy on every call) and is designed to run in a single AWS Lambda function.

Status: requirements draft, to be reviewed before design. Items marked OPEN are decisions for the owner.

The requirements themselves live in `.kiro/steering/10-requirements.md`; each requirement below is one user story of this component, and each acceptance criterion is a pointer to the steering criterion it realizes (never a copy). Questions that were open in the former text are in `.kiro/steering/12-decisions.md`.

## Glossary

- **Gateway**: The Skye component that exposes tools through one MCP endpoint
- **Target**: A source of tools behind the Gateway: a Lambda function, an OpenAPI document, an upstream MCP server, or a local capability
- **Tool**: A callable operation with a name, a description and a JSON Schema for its arguments (a Capability, in Skye terms)
- **Registry**: The catalogue of all tools the Gateway knows, with their target, tags and version
- **Operation**: The unit of work an agent is carrying out, described by a short text, optional tags, and the principal on whose behalf it runs
- **Toolset**: The tools exposed to one operation
- **Selector**: A strategy that ranks the tools of the Registry for an operation. Skye ships two: hybrid search and Jev
- **Scope token**: A signed, expiring token that names the toolset of an operation, so the Gateway needs no server-side session
- **Principal**: The caller, identified from IAM or from a JWT
- **Policy engine**: The component specified in `.kiro/specs/policy-engine`
- **Warm container**: A Lambda execution environment reused by later invocations
- **Decision model**: A model that does not generate text. It takes a state and typed questions (yes or no, a category, a score) and returns a choice from a fixed set, with calibrated probabilities. Jev, from TypeSafe AI, is one ("System One" model). The `models` component exposes decision models through one interface
- **Hierarchical selection**: Choosing in two steps (a domain first, then a tool inside it) when there are more candidates than a decision model accepts as labels

## Requirements

### Requirement 1: MCP endpoint

**User Story:** As an agent developer, I want one standard endpoint for tools, so that any MCP client can use the Gateway.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 44.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 44.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 44.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 44.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 2: Targets

**User Story:** As a platform engineer, I want to attach existing functions and APIs as tools, so that I do not rewrite them.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 44.5 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 44.6 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 44.7 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 44.8 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 44.9 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 3: Registry

**User Story:** As a platform engineer, I want the tool catalogue stored outside the function, so that every invocation sees the same tools.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 44.10 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 44.11 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 44.12 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 4: Toolset per operation

**User Story:** As an agent developer, I want the agent to see only the tools its current operation needs, so that the prompt stays small and the agent cannot reach tools it should not use.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 45.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 45.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 45.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 45.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 5: Discovery tool

**User Story:** As an agent, I want to ask for more tools while I work, so that an operation that changes can get what it now needs.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 45.5 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 45.6 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 45.7 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 6: Scope token

**User Story:** As a platform engineer, I want a stateless way to bind a toolset to an operation, because Lambda keeps no state between invocations.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 45.8 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 45.9 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 45.10 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 45.11 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 7: Selection strategies

**User Story:** As an agent developer, I want to choose tools with hybrid search or with a decision model, so that the agent gets the right few tools fast.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 46.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 46.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 46.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 46.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 46.5 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL realize Requirement 46.6 of #[[file:.kiro/steering/10-requirements.md]].
7. THE spec SHALL realize Requirement 46.7 of #[[file:.kiro/steering/10-requirements.md]].
8. THE spec SHALL realize Requirement 46.8 of #[[file:.kiro/steering/10-requirements.md]].
9. THE spec SHALL realize Requirement 46.9 of #[[file:.kiro/steering/10-requirements.md]].
10. THE spec SHALL realize Requirement 46.10 of #[[file:.kiro/steering/10-requirements.md]].
11. THE spec SHALL realize Requirement 46.11 of #[[file:.kiro/steering/10-requirements.md]].
12. THE spec SHALL realize Requirement 46.12 of #[[file:.kiro/steering/10-requirements.md]].
13. THE spec SHALL realize Requirement 46.13 of #[[file:.kiro/steering/10-requirements.md]].
14. THE spec SHALL realize Requirement 46.14 of #[[file:.kiro/steering/10-requirements.md]].
15. THE spec SHALL realize Requirement 46.15 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 8: Lambda constraints

**User Story:** As a platform engineer, I want the Gateway to behave correctly in Lambda, where parallel processes and background work are not available.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 48.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 48.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 48.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 48.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 9: Inbound authorization

**User Story:** As a platform engineer, I want to know who is calling, so that policy can decide what they may use.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 47.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 47.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 47.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 10: Outbound authorization

**User Story:** As a platform engineer, I want each target to be called with its own credentials, so that callers never hold them.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 47.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 47.5 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 47.6 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 11: Policy on every call

**User Story:** As a security owner, I want every listing and call authorized, so that access is enforced in one place.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 47.7 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 47.8 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 47.9 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 12: Observability

**User Story:** As a security owner, I want a record of what each agent could see and do.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 48.5 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 48.6 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 13: Size and load budgets

**User Story:** As a maintainer, I want the Gateway to stay small, because it is deployed in a Lambda package.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 48.7 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 48.8 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 14: Local mode

**User Story:** As a developer, I want to run the Gateway on my machine, so that I can test without AWS.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 44.13 of #[[file:.kiro/steering/10-requirements.md]].

Note (from decision D47 of `.kiro/steering/12-decisions.md`): the Gateway client SHALL implement the `ToolProvider` Port of `skye.base.interfaces.tool_provider` (list the tools of an operation, call one with the scope token, raise `CapabilityExecutionError` on failure), so that `CapabilityRegistry` (local) and the Gateway client (remote) are interchangeable in an agent. Local mode (this requirement) is the first implementation to write: it wraps a `CapabilityRegistry`. The component `skye.gateway` is still empty and raises `ImportError` on any name (spec 0-base-uxui, task 4.6).
