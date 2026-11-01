# Requirements Document: Agent Runtime

## Introduction

The Agent Runtime feature provides a base class that implements the agent loop and lets users customize it with hooks that run before and after every operation. The default agent that ships with Nimbus is built on this base class and uses the same hook mechanism for its own behaviour (limits, safety, policy, observability). The loop is designed for serverless: its state is serializable, it can stop before a time limit and resume in a later invocation, and it does not use parallel processes.

Status: requirements draft, to be reviewed before design. Items marked OPEN are decisions for the owner.

## Glossary

- **Agent loop**: The repeated cycle of building a model request, calling the model, running the tools it asks for, and adding the results to the conversation, until the agent produces a final answer or a stop condition is met
- **BaseAgent**: The abstract class that implements the agent loop and the hook points
- **Agent**: The default agent shipped with Nimbus, a BaseAgent with default hooks
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

1. THE Nimbus library SHALL provide a BaseAgent class that implements the agent loop for both synchronous and asynchronous use
2. THE BaseAgent SHALL take the model (or the ModelRouter), the ToolProvider, optional memory and optional hook providers as inputs
3. THE BaseAgent SHALL stop when the model returns a final answer, when the maximum number of steps is reached, when a hook stops the run, or when the run is suspended
4. THE BaseAgent SHALL return a result that states why the run ended
5. THE default Agent SHALL be a BaseAgent subclass and SHALL NOT duplicate the loop

### Requirement 2: Operations and hook points

**User Story:** As a developer, I want a hook before and after each operation, so that I can customize behaviour at the exact point I need.

#### Acceptance Criteria

1. THE BaseAgent SHALL define these operations, each with a pre hook point and a post hook point: run, step, toolset selection, model call, tool call, memory read, memory write, safety check, policy check
2. WHEN an operation fails, THE BaseAgent SHALL call the error hooks of that operation
3. THE BaseAgent SHALL pass each hook a context object with the AgentState, the operation name and the operation payload (request before, result after)
4. THE Nimbus library SHALL list the operations in one enumeration, so that hooks can be registered by name

### Requirement 3: Hook semantics

**User Story:** As a developer, I want hooks that can change what happens, not only watch it.

#### Acceptance Criteria

1. THE pre hook of an operation SHALL be able to return one of: continue unchanged, continue with a modified payload, skip the operation and supply its result, or deny the operation with a reason
2. THE post hook of an operation SHALL be able to return one of: keep the result, replace the result, retry the operation with a modified payload (within a retry limit), or stop the run
3. THE BaseAgent SHALL run pre hooks in registration order and post hooks in reverse order
4. THE BaseAgent SHALL accept hooks written as synchronous or asynchronous functions
5. WHEN a hook raises an error, THE BaseAgent SHALL apply a per-hook setting: fail closed (stop the operation) or fail open (log and continue). THE default SHALL be fail closed for hooks that protect (safety, policy, limits) and fail open for observers
6. THE BaseAgent SHALL give a retry limit and a per-hook time limit (OPEN: default values)

### Requirement 4: Customization

**User Story:** As a developer, I want several ways to customize, so that a small change does not need a new class.

#### Acceptance Criteria

1. THE BaseAgent SHALL let a subclass override a method for each hook point
2. THE BaseAgent SHALL let a caller register and remove hooks on an instance, by operation name
3. THE BaseAgent SHALL accept hook providers that register several hooks together
4. THE BaseAgent SHALL let hooks be restricted to a subset of tools or models, by name or tag
5. THE BaseAgent SHALL document the order in which subclass overrides, instance hooks and hook providers run

### Requirement 5: Default behaviour as hooks

**User Story:** As a developer, I want the default agent's own rules to be visible and removable, so that nothing is hidden in the loop.

#### Acceptance Criteria

1. THE default Agent SHALL provide these hook providers, all optional and all replaceable: limits (steps, tokens, cost, time), safety (uses SafetyFilterInterface), policy (uses the policy engine), observability (uses EventHandlerInterface and ObserverInterface), and checkpointing
2. THE default Agent SHALL enable the limits provider by default
3. WHEN a safety filter or policy engine is configured, THE default Agent SHALL enable the matching provider automatically
4. THE default Agent SHALL expose the list of active hooks, in execution order, for inspection

### Requirement 6: Observers and interceptors

**User Story:** As a developer, I want to keep using event handlers for logging, without giving them the power to change the run.

#### Acceptance Criteria

1. THE BaseAgent SHALL call the existing EventHandlerInterface methods for model calls, tool calls, steps and completion
2. THE BaseAgent SHALL treat EventHandlerInterface implementations as observers: their errors SHALL NOT stop the run
3. THE BaseAgent SHALL NOT let an observer modify a payload or result

### Requirement 7: Toolset and the Gateway

**User Story:** As a developer, I want the agent to ask for the tools its operation needs, instead of holding a fixed list.

#### Acceptance Criteria

1. THE BaseAgent SHALL obtain tools only through a ToolProvider, at the toolset selection operation
2. THE BaseAgent SHALL run toolset selection at the start of a run, and again when a hook or the model asks for different tools
3. THE BaseAgent SHALL work with the local CapabilityRegistry as ToolProvider without any Gateway
4. WHEN the ToolProvider is the Gateway client, THE BaseAgent SHALL carry the scope token in AgentState and send it with every tool call
5. THE BaseAgent SHALL pass the operation description to the ToolProvider (OPEN: who writes it, see the Gateway spec)

### Requirement 8: State and resumability

**User Story:** As a platform engineer, I want a run to survive the end of a Lambda invocation.

#### Acceptance Criteria

1. THE BaseAgent SHALL keep the whole run in an AgentState that serializes to JSON with the standard library
2. THE BaseAgent SHALL save a Checkpoint through StorageInterface at configurable points (after each step by default)
3. WHEN the remaining time is below a configurable margin, THE BaseAgent SHALL stop before starting the next step and return a Suspended result with the checkpoint identifier
4. WHEN given a checkpoint identifier, THE BaseAgent SHALL resume the run from the saved state
5. THE BaseAgent SHALL get the remaining time from a configurable function (in Lambda, the context object; elsewhere, a deadline)

### Requirement 9: Lambda constraints

**User Story:** As a platform engineer, I want the loop to behave correctly in Lambda.

#### Acceptance Criteria

1. THE BaseAgent SHALL NOT use multiprocessing
2. THE BaseAgent SHALL NOT start work that continues after the run returns
3. WHEN a model asks for several tools in one step, THE BaseAgent SHALL run them concurrently with asyncio or threads, up to a configurable limit
4. THE BaseAgent SHALL return the results of concurrent tool calls in the order the model asked for them

### Requirement 10: Errors and limits

**User Story:** As a developer, I want clear behaviour when something fails, so that a bad tool does not end the run by surprise.

#### Acceptance Criteria

1. WHEN a model call fails, THE BaseAgent SHALL use the fallbacks and retries of the ModelRouter before failing the operation
2. WHEN a tool call fails, THE BaseAgent SHALL return the error to the model as a tool result, unless a hook stops the run (OPEN: default per error type)
3. THE BaseAgent SHALL stop after a configurable number of consecutive failed steps
4. THE BaseAgent SHALL count tokens and cost per run from the model responses and expose them in the result

### Requirement 11: Dependencies and budgets

**User Story:** As a maintainer, I want the runtime to stay light.

#### Acceptance Criteria

1. THE Agent Runtime SHALL use the standard library for models of state, hooks and results (dataclasses, enums, json), and SHALL NOT add a third-party import at module level
2. THE Agent Runtime SHALL be part of the core, and the empty extra named agents SHALL be removed from pyproject.toml
3. THE Agent Runtime SHALL have an entry in budgets.toml for import time and module count (OPEN: values) and SHALL pass the existing budget tests

### Requirement 12: Testing

**User Story:** As a maintainer, I want the loop and hooks tested without a real model.

#### Acceptance Criteria

1. THE Nimbus library SHALL provide a scripted model for tests that returns prepared responses and tool calls
2. THE Nimbus test suite SHALL cover each hook outcome (continue, modify, skip, deny, retry, replace, stop), the hook order, fail open and fail closed, suspension and resumption, and concurrent tool calls

## Note on decision models
Hooks may call a decision model (Jev, a "System One" model that returns a constrained choice with probabilities) for quick branching decisions: which tools to expose, whether an action is risky, whether to continue. It is a use of the `models` component, not a part of the loop.

## Open questions for the owner

1. Names: BaseAgent and Agent, or other names? The operation list: is anything missing (for example a streaming chunk hook)?
2. Streaming: are hooks needed on each streamed chunk, or only on the complete response?
3. Defaults: retry limit, hook time limit, maximum steps, consecutive failure limit.
4. Should a tool failure go back to the model by default, or stop the run?
5. Is checkpointing on by default in Lambda, or opt-in?
6. Where does the operation description come from (shared with the Gateway spec)?
