Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, Composition, Optional services, The `.skye` language, Extras and budgets)

# Design Document: flows

## Overview
`flows` is the runtime layer-3 component (codename stream). It reads a `flow` block of a `.skye` file and runs it: steps in sequence,
conditions, parallel steps, bounded loops, `foreach`, retry, timeout and error transitions (Requirement 50.1, 50.2, 50.5, 50.6).
A step is a `Runnable` resolved by name from a registry the caller passes, never by import, so `flows` imports nothing outside `base`
(Requirement 50.4, 5.1; D52). `flows` is itself a `Runnable`, so a flow can be a step of another flow, a member of a team or a tool
of an agent. It never imports `models`, `agents`, `teams`, `policy`, `guard`, `observe` or `memory`; those arrive as objects in the
registry or as Ports (Requirement 4.1, 5.4). It uses the standard library only and has no extra. The layer, the allowed imports, the
composition rule, the `.skye` language and the extras policy are in the steering sections named above and are not restated here.

## Current state
What exists, judged from the code in `src/skye/flows/flow.py`, `src/skye/base/dsl/` and `tests/unit/flows/test_loading.py`:
- The `.skye` parser and checker in `base` (`skye.base.dsl`): the model of a flow (`FlowSpec`, `StepSpec`, `ParallelSpec`,
  `ChoiceSpec`, `BranchSpec`, `ContextSpec`, `RetrySpec`, `SetSpec`), expression checking and `evaluate`, the writer `to_text`, the
  load-time checks of Requirement 54.4 including "a loop has `max_visits`", and the rejection of `wait` and `on_event`
  (Requirement 50.5, `tests/unit/dsl/test_conformance.py`).
- `Flow.from_file`, `Flow.from_text`, `Flow.check`, `Flow.to_text`, `Flow.name` and the registry-name check.
- `Flow.run` raises `NotImplementedError("The flow runtime is not built yet ...")`; `tests/unit/flows/test_loading.py` asserts it.
- `Flow` imports `skye.utils.skye_files` (the file reader and the diagnostics error), a standard-library helper that sits in layer 0
  with `base` (`tests/budget/test_import_matrix.py`, `NON_COMPONENT_TO_COMPONENT`).

The owner decided that the runtime belongs to version 1 of `flows` and is built after the language work. Version 2 (waiting for
events with persistence, `include`) is out of this spec's first scope (D51); `to_mermaid()` moved to version 1 (D88).

## Architecture
```
flows/
  flow.py        Flow: loading (exists) and the entry points run / arun / invoke / ainvoke
  runtime.py     the interpreter: one run, one context, one event at a time
  context.py     the run context: declared fields with their types, step outputs, set and emit
  parallel.py    parallel blocks and foreach with asyncio.TaskGroup
  cycles.py      the visited set and the depth bound over nested flows (Requirement 5.3)
```

### Running a flow (Requirement 50.2)
`Flow.arun(input)` is the real form and `Flow.run(input)` runs it to completion (the `x` and `ax` rule, D43); `invoke` and `ainvoke`
make `Flow` satisfy `Runnable`. The input fills the declared context fields (a missing required field is a validation error naming
it). The interpreter takes the first node, runs it, and follows its transition, one node at a time, to completion:
- A **step** with `run` resolves `registry.NAME` (or `flow.NAME`, `router.NAME` from the same file) to a `Runnable`, evaluates `input`
  over the scope `{context, step, env, item}` with `skye.base.dsl.evaluate`, awaits `invoke`, stores the output at `step.<Name>.output`,
  applies `set` and `emit` after a success, and takes `next`. A step with no `run` is allowed when it has `set`, `emit` or `foreach`
  (D58).
- A **choice** checks its `when` branches in order with `evaluate`; the `else` branch always matches; the branch's `set`, `emit` and
  `next` apply. Expressions are never passed to `eval` (D55).
- `next = end` finishes and returns the output of the last step.

### Parallel and foreach (Requirement 50.2; D56)
A `parallel` block runs its branches with `asyncio.TaskGroup`. `join = "all"` waits for every branch; `join = "any"` returns the first
to finish and cancels the others. `on_branch_error = "cancel"` cancels the siblings on the first failure; `"continue"` lets the others
finish and gives a failed branch an empty output. Changes to the context made by branches are collected and applied one at a time in
document order after the block, so two branches never write at once. `foreach` runs the step or sub-flow once per element, in
parallel, with `item` bound to the element, and the output is a list in the order of the input. A concurrency limit is an argument
of `Flow`, with no hidden default beyond a documented one.

### Retry, time and errors (Requirement 50.1, 50.2; D54)
`retry = { max, after, backoff }` re-runs a failed step up to `max` times, waiting `after` and doubling the wait when `backoff` is
true. The wait goes through an injectable clock (a coroutine `sleep` the caller can replace), so tests never sleep. `timeout` uses
`asyncio.timeout`; a timeout goes to `on_timeout` and, without one, is an error. An error goes to `on_error`; without one the flow
takes the default error end: the flow stops, the error is raised to the caller naming the step, and a record goes to the observer
Port when one was given (never by import). A retry of the step happens before the `on_error` transition.

### Loops and cycles (Requirement 50.3, 5.3; D56)
`max_visits` is counted at run time per step; a re-entry over the limit raises an error naming the step. For nested flows, each run
carries a visited set of flow names and a depth counter (default bound 100, Requirement 5.3); entering a flow already on the path
stops at that point and raises an error naming the cycle. This covers a flow that contains itself directly or through another flow.

### Isolation
No state outlives a run: the context and the outputs live in the run and are returned or discarded. Persistence is version 2. No
multiprocessing and nothing that continues after the call returns (`00-rules`, "Serverless first"). Tasks started by a parallel block
finish or are cancelled before `arun` returns.

## Data Models
The `base` dataclasses are the model of a flow and are not duplicated. New runtime dataclasses: `RunContext` (typed fields, outputs,
visits), `FlowError` (step name, cause, path of flows), all in the `SkyeError` hierarchy where they are errors.

## Error Handling
A load error is a `ConfigurationError` with every diagnostic (file, line, column, reason, fix; Requirement 54.3). A run error names the
step and keeps the cause (`raise ... from e`). A `Runnable` that raises is a step failure and follows retry, then `on_error`. A
`foreach` over a value that is not a list is a run error naming the step. A condition that cannot be evaluated is a run error, not a
silent false.

## Testing Strategy
Tests in `tests/unit/flows/` run every reference example F1 to F5, F7, F8 and the version 1 form of F9 of the examples file, with fake
`Runnable`s and a fake clock: sequence, condition and else, parallel with `all`, `any`, cancel and continue, a bounded loop and the
error when the bound is passed, retry with backoff, timeout with and without `on_timeout`, `on_error`, the default error end with the
observer record, `foreach` order, a sub-flow as a step, a cycle, `set` and `emit`, a missing input field. The existing loading tests
stay and the `run` test changes from "not built" to a real run. The import-matrix and cold-start budget tests stay green. The skill
(`src/skye/utils/claude_skill/skye/references/flow.md` and `python-api.md`) is updated in the same change and loses the "not built
yet" lines (`00-rules`, "The Claude skill that ships with the package").

## Correctness Properties
1. A flow with no error ends exactly at `next = end`, and its result is the output of the last step.
2. Choice branches are tried in order and the first true one is taken; `else` is taken only when none is.
3. A step that is re-entered more than `max_visits` times stops the run with an error naming it.
4. `foreach` returns outputs in the order of the input, whatever order the runs finish in.
5. With `join = "any"` the losing branches are cancelled before the block returns.
6. Context changes from parallel branches are applied in document order.
7. A retry waits the configured time through the injected clock and never sleeps in tests.
8. A flow that contains itself, directly or through another, raises an error naming the cycle, and the depth never passes the bound.
9. `flows` imports nothing outside `base`, and no component imports `flows`.

## Open points (not decided here)
- Settled, outside this spec's first scope: persistence (version 2) guarantees at-least-once delivery with an idempotency key per step (Requirement 50.7, D87).
- Settled: `skye render` and `to_mermaid()` are version 1 (Requirement 54.21, D88), built in `base/dsl` and the command line under `0-base-uxui`, not in `flows`.
- The default concurrency limit of `parallel` and `foreach`.
- Whether the observer record of the default error end goes through the `observer` Port passed to `Flow`, or through an event hook shared with `agents`; the design uses the Port.
- `Flow` imports `skye.utils`; the import matrix allows it, but the spec's rule "imports only `base`" (Requirement 50.4) names `base` alone. Decide whether the note in `11-design.md` should name `utils` or the file reader should move into `base`.
