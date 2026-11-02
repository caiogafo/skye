---
component: agents
---

# Requirements Document

## Introduction

The Agent Runtime feature provides a base class that implements the agent loop and lets users customize it with hooks that run before and after every operation. The default agent that ships with Skye is built on this base class and uses the same hook mechanism for its own behaviour (limits, safety, policy, observability). The loop is designed for serverless: its state is serializable, it can stop before a time limit and resume in a later invocation, and it does not use parallel processes.

Status: requirements draft, to be reviewed before design. Items marked OPEN are decisions for the owner.

Hooks may call a decision model (Jev, a "System One" model that returns a constrained choice with probabilities) for quick branching decisions: which tools to expose, whether an action is risky, whether to continue. This is a use of the `models` component, not a part of the loop.

The requirements themselves live in `.kiro/steering/10-requirements.md`; each requirement below is one user story of this component, and each acceptance criterion is a pointer to the steering criterion it realizes (never a copy). Questions that were open in the former text are in `.kiro/steering/12-decisions.md`.

## Glossary

- **Agent loop**: The repeated cycle of building a model request, calling the model, running the tools it asks for, and adding the results to the conversation, until the agent produces a final answer or a stop condition is met
- **BaseAgent**: The abstract class that implements the agent loop and the hook points
- **Agent**: The default agent shipped with Skye, a BaseAgent with default hooks
- **Operation**: A step of the loop that has its own pre and post hook point (run, step, toolset selection, model call, tool call, memory read, memory write, safety check, policy check)
- **Hook**: A user-provided function or object attached to an operation
- **Interceptor**: A hook that can change, replace, retry or stop an operation. Not to be confused with an observer
- **Observer**: A hook that only watches an operation and cannot change it (see EventHandlerInterface)
- **Hook provider**: A class that bundles several hooks, so a feature can be added or removed as one unit
- **AgentState**: The complete state of a run (messages, step number, toolset, usage), serializable to JSON
- **Checkpoint**: A saved AgentState in an external store, used to resume a run
- **ToolProvider**: The interface the agent uses to obtain the tools for its operation, implemented by the local CapabilityRegistry and by the Gateway client
- **Suspended**: A run result that means "stopped on purpose, resumable from this checkpoint"

## Requirements

### Requirement 1: Agent loop in a base class

**User Story:** As a developer, I want the agent loop in one reusable class, so that I can build my own agent without rewriting it.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 39.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 39.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 39.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 39.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 2: Operations and hook points

**User Story:** As a developer, I want a hook before and after each operation, so that I can customize behaviour at the exact point I need.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 39.5 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 39.6 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 39.7 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 39.8 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 3: Hook semantics

**User Story:** As a developer, I want hooks that can change what happens, not only watch it.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 40.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 40.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 40.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 40.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 40.5 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL realize Requirement 40.6 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 4: Customization

**User Story:** As a developer, I want several ways to customize, so that a small change does not need a new class.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 40.7 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 40.8 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 40.9 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 5: Default behaviour as hooks

**User Story:** As a developer, I want the default agent's own rules to be visible and removable, so that nothing is hidden in the loop.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 41.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 41.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 41.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 41.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 6: Observers and interceptors

**User Story:** As a developer, I want to keep using event handlers for logging, without giving them the power to change the run.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 40.10 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 40.11 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 7: Toolset and the Gateway

**User Story:** As a developer, I want the agent to ask for the tools its operation needs, instead of holding a fixed list.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 42.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 42.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 42.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 8: State and resumability

**User Story:** As a platform engineer, I want a run to survive the end of a Lambda invocation.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 42.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 42.5 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 42.6 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 42.7 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 9: Lambda constraints

**User Story:** As a platform engineer, I want the loop to behave correctly in Lambda.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 42.8 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 42.9 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 10: Errors and limits

**User Story:** As a developer, I want clear behaviour when something fails, so that a bad tool does not end the run by surprise.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 42.10 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 42.11 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 42.12 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 42.13 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 11: Dependencies and budgets

**User Story:** As a maintainer, I want the runtime to stay light.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 43.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 43.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 43.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 12: Testing

**User Story:** As a maintainer, I want the loop and hooks tested without a real model.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 43.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 43.5 of #[[file:.kiro/steering/10-requirements.md]].
