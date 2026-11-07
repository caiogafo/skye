Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, Composition, Optional services, Extension points, Extras and budgets)

# Design Document: agents

## Overview
`agents` is the runtime layer-3 component (codename cyclone). It holds one reusable agent loop, `BaseAgent`, with a hook point before
and after each of nine operations, and a default `Agent` built on it whose own rules (limits, safety, policy, observability,
checkpointing) are hook providers that can be listed, replaced and removed (Requirements 39 to 41). The run is serverless-safe: its
state serializes to JSON, it can stop before a time limit and resume in a later invocation, and it uses no multiprocessing and no
work that outlives the call (Requirement 42). It imports only `base` and `models` (`11-design.md`, "Allowed imports"); `tools` and
`prompts` only when the matching hook is on, never `teams` or `flows`. It never imports `policy`, `guard`, `observe` or `memory`:
those arrive as the Ports `authorizer`, `safety`, `observer` and `memory` (Requirement 4.1, D9). It is part of the core with no extra
(Requirement 43.2). This document describes only the internals of `agents`; the layer, the allowed imports, the Ports, the
composition and extension-point rules and the extras policy are in the steering sections named above and are not restated here.

Today `skye.agents` holds only the agent-type registry (`register_agent_type`, `get_agent_type`) and a `ReActAgent` stub that raises
`NotImplementedError` (`src/skye/agents/registry.py`, `tests/unit/agents/test_registry.py`). The loop, the hooks and the state are
not built. The Ports it needs exist in `base`: `Runnable`, `ToolProvider` with `CapabilityContext`, the model Port, the storage Port,
`EventHandlerInterface`, `SafetyFilterInterface`, `AuthorizerInterface`, `ObserverInterface`, `MemoryInterface`, and the capability
primitive that runs one call and never raises (D42, D45).

## Architecture
```
agents/
  operations.py   Operation: the nine operations in one enumeration (run, step, toolset, model_call, tool_call, memory_read, memory_write, safety, policy)
  state.py        AgentState (messages, step, scope token, usage, checkpoint id, failures), RunResult, EndReason, Suspended; to_json / from_json
  hooks.py        HookContext, pre outcomes, post outcomes, HookSpec (operation, function, fail mode, time limit, filter), HookProvider, HookRegistry
  base_agent.py   BaseAgent: the loop, the dispatch of hooks, the toolset, concurrency, suspension and resumption
  agent.py        Agent: BaseAgent plus the default providers, with the list of active hooks
  providers/      limits.py, safety.py, policy.py, observability.py, checkpoint.py: the five replaceable hook providers
  registry.py     the agent-type registry (exists)
```

### The loop (Requirement 39)
`BaseAgent` takes a model (or a router, both reached through the model and `Runnable` Ports), a `ToolProvider`, optional memory and
optional hook providers (39.2). A run is a sequence of steps. A step asks for the toolset, calls the model, and when the model asks
for tools runs them and feeds the results back; it ends when the model gives a final answer. The run ends for one of four reasons:
final answer, maximum steps, a hook stopped it, or it was suspended; the result says which, as an `EndReason` (39.3). The default
`Agent` subclasses `BaseAgent` and adds providers; it does not copy the loop (39.4).

Each operation has a pre point and a post point, and an error point called when the operation fails (39.5, 39.6). A hook receives a
`HookContext` with the `AgentState`, the operation name and the payload: the request before, the result after (39.7). Operations are
one enumeration so a hook is registered by name (39.8).

Synchronous and asynchronous forms follow the `x` and `ax` rule (D43): `BaseAgent.invoke` is the async `Runnable` method and `run`
the synchronous one that runs it. The names `BaseAgent` and `Agent` and the list of operations are open decision O11; the
design uses the names of Requirements 39 to 41 and the nine operations of 39.5.

### Hooks (Requirement 40)
A pre hook returns one of four outcomes: continue, continue with a modified payload, skip and supply the result, deny with a reason
(40.1). A post hook returns one of four: keep the result, replace it, retry the operation with a modified payload within the retry
limit, or stop the run (40.2). An outcome is a small frozen dataclass or enum member, not a string. Pre hooks run in registration
order and post hooks in reverse (40.3). A hook is a function or a coroutine function; the agent awaits only the second kind (40.4).

When a hook raises, the hook's setting decides: fail closed stops the operation, fail open logs and continues. The default is fail
closed for hooks that protect (safety, policy, limits) and fail open for observers (40.5). Each hook has a time limit, and the whole
operation has a retry limit; their default values are open (40.6, O11) and are constructor arguments with no value hardcoded until
the owner settles them. A hook can be restricted to tools or models by name or tag (40.8).

There are three ways to customize and one documented order (40.7, 40.9): a subclass overrides the method of a hook point; a caller
registers and removes hooks on an instance by operation name; a provider registers several hooks together. The order is: subclass
override first, then instance hooks in registration order, then providers in the order they were passed. That order is written in the
module docstring and tested.

The existing `EventHandlerInterface` methods (model invoke start, end and error; capability invoke start, end and error; execution
step; execution complete) are called by `BaseAgent` at the matching points (40.10). Handlers are observers: their errors do not stop
the run and they never change a payload or a result (40.11).

### Default agent (Requirement 41)
The five providers are limits (steps, tokens, cost, time), safety (the `safety` Port), policy (the `authorizer` Port),
observability (the `event_handler` and `observer` Ports) and checkpointing (41.1). The limits provider is on by default; the safety
and policy providers turn on when a safety filter or an authorizer is configured (41.2, 41.3). `Agent.hooks()` returns the active
hooks in execution order (41.4). The policy provider calls the authorizer at the policy check operation with the principal, the tool
name as the action and the tool identifier as the resource; its failure mode is closed.

### Toolset, state and resumption (Requirement 42)
Tools come only through a `ToolProvider`, asked at the toolset operation, at the start of a run, and again when a hook or the model
asks for different tools (42.1). A local `CapabilityRegistry` is a `ToolProvider`, so an agent works with no gateway (42.2). With a
gateway client the scope token lives in the `AgentState` and travels in the `CapabilityContext` of every call, together with the
operation description (42.3); who writes the description is open decision O12, so `BaseAgent` takes it as an argument or a callable
and writes none itself.

`AgentState` holds the whole run and round-trips through `json` (42.4). It never holds a live object: tool calls are the serialisable
`CapabilityCall` of D45 and results are `CapabilityMessage` with their `status` (D42). A checkpoint is written through the `storage`
Port at configurable points, after each step by default (42.5); whether checkpointing is on by default in Lambda or opt-in is open
decision O13. The remaining time comes from a function the caller passes (the Lambda context or any deadline); when it is below a
margin, the agent stops before the next step and returns a `Suspended` result carrying the checkpoint identifier (42.6). Given that
identifier the agent resumes from the saved state (42.7).

Several tool calls in one step run concurrently, up to a configurable limit, with `asyncio.gather` under a semaphore, and the results
keep the order the model asked for (42.9). A run uses no multiprocessing and starts nothing that continues after it returns (42.8).
A model failure first uses the fallbacks and retries of the router (42.10). A tool failure goes back to the model as a
`CapabilityMessage` with status `error`, unless a hook stops the run (42.11); the default per error type is open (O13), so the
first version returns every tool failure to the model and exposes a hook point where the owner's rule will go. The run stops after a
configurable number of consecutive failed steps (42.12). Tokens and cost are counted per run from the model responses and returned in
the result (42.13).

## Data Models
Dataclasses and enums only (D24, Requirement 43.1): `AgentState`, `RunResult` (end reason, final message, usage, steps, checkpoint
id), `Suspended`, `HookContext`, the pre and post outcomes, `HookSpec`, `Operation`, `EndReason`. Messages, `CapabilityCall`,
`CapabilityMessage` and usage are the `base` types.

## Error Handling
A hook error follows its fail mode. A model failure that survives the router raises the provider error out of the operation after the
error hooks ran, and the run ends with that reason. A tool failure is data, not an exception: the capability primitive never raises.
A malformed checkpoint raises a validation error naming the field. Everything is in the `SkyeError` hierarchy with context.

## Testing Strategy
Tests use a scripted model that returns prepared responses and tool calls (43.4). Requirement 43.4 says the library provides it,
while D38 keeps the offline demo model only in `examples/`; the scripted model for these tests therefore lives in `tests/fixtures/`
and the tension is listed under "Open points". The tests cover each hook outcome (continue, modify, skip, deny, retry, replace,
stop), the hook order, fail open and fail closed, suspension and resumption, and concurrent tool calls (43.5), plus the state
round-trip, the end reasons, the consecutive-failure limit, the event handlers as observers, and that `agents` imports none of the
four optional services (the import-matrix test).

## Correctness Properties
1. A run ends with exactly one `EndReason` (39.3).
2. Pre hooks run in registration order and post hooks in reverse order for every operation (40.3).
3. A `deny` or `skip` outcome stops the operation before it runs and its result is a `CapabilityMessage` with status `denied` or `skipped` for a tool call (40.1, D42).
4. An `AgentState` saved to JSON and loaded gives an equal state (42.4).
5. A run suspended with a checkpoint and then resumed ends with the same result as an uninterrupted run, for a deterministic model (42.6, 42.7).
6. The results of concurrent tool calls come back in the order the model asked for them (42.9).
7. An event handler that raises, or tries to change a payload, does not change the run (40.11).
8. The agent never imports `policy`, `guard`, `observe` or `memory` (4.1).

## Open points (not decided here)
- **O11** names `BaseAgent` and `Agent`, the operation list (a streaming-chunk hook), streaming hooks per chunk or per response, the defaults for retry limit, hook time limit, maximum steps and consecutive failures, and the budget values: the design leaves these as arguments.
- **O12** who writes the operation description: an argument of the agent in this design.
- **O13** the default for a tool failure per error type and whether checkpointing is on by default in Lambda: returned to the model and opt-in until settled.
- Requirement 43.4 (the library provides a scripted model) against D38 (the demo model lives only in `examples/`): needs a steering decision before the fixture moves into the package.
- Whether `ReActAgent` of the registry becomes the default `Agent` or a separate type.
