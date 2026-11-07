---
component: flows
codename: stream
---

# Requirements Document

## Introduction

Sequencing of units into steps with conditions and error handling. This spec is at the requirements stage: the design and the tasks come after the requirements are approved.

The requirements themselves live in `.kiro/steering/10-requirements.md`; each requirement below is one user story of this component, and each acceptance criterion is a pointer to the steering criterion it realizes (never a copy).

## Requirements

### Requirement 1: Flows

**User Story:** As a developer, I want to sequence units into steps with conditions and error handling, so that I can express a workflow as data.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 50.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 50.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 50.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 2: Composition

**User Story:** As a maintainer, I want agents, teams and flows to compose through one abstraction, so that orchestration is uniform and no import cycle appears.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 5.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 5.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 5.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 5.4 of #[[file:.kiro/steering/10-requirements.md]].

## Notes to integrate (from the `.skye` work of 2026-11-07; the owner asked for them here, to be absorbed when this spec's requirements and design are written)

**Decision of the owner: the flow runtime is part of version 1 of `flows`, and it is NOT built yet** (it is built after the language work, not now).
What exists today: the `.skye` parser and checker (`skye.base.dsl`), the model of a flow (`FlowSpec`, `StepSpec`, `ParallelSpec`, `ChoiceSpec`), the writer
(`to_text`), the loading API (`skye.load`, `skye.flows.Flow.from_file` / `from_text`, which validate and hold the spec) and `Flow.run`, which raises
`NotImplementedError` until the runtime exists. The reference examples are in `.agents/tasks/uxui-dsl-examples.md` (F1 to F5, F7, F8 and the version 1
variant of F9) and the decisions are D50 to D61 in `.kiro/steering/12-decisions.md` (D51 scope, D52 step and registry, D54 to D58 the language).

What the runtime has to do (to become requirements, a design and tasks):
- **Run a validated `FlowSpec`** with `Flow.run(input)` (sync) and `Flow.arun(input)` (async, the `x`/`ax` rule of D43), steps resolved by name from the `registry` the caller passes (`registry.NAME`), `flow.NAME` and `router.NAME` references from the same file; a step is a `Runnable`; the result of a step is stored at `step.<Name>.output`.
- **One event at a time, to completion:** take the next node, run its step, apply `set` and `emit` after a success, take `next`; `choice` branches are checked in order with `skye.base.dsl.evaluate` over the context (never `eval`), `else` always matches; `next = end` returns the output of the last step.
- **Parallel:** `asyncio.TaskGroup`; `join = all | any` (`any` cancels the others), `on_branch_error = cancel | continue` (a failed branch gives an empty output); changes to the context are applied one at a time, in document order, so two branches never write at once.
- **`foreach`:** one run of the step or sub-flow per element, in parallel, `item` as the element, the output a list in the order of the input.
- **Retry and time:** `retry = { max, after, backoff }` on the step, `timeout` with `asyncio.timeout`, `on_timeout`/`on_error` transitions; the default error end (D54): the flow stops, the error is raised to the caller with the step name, and a record goes to `observe` through the observer Port (never by import).
- **Loops:** `max_visits` is counted at run time; a re-entry over the limit raises an error naming the step.
- **Isolation:** `flows` imports only `base` (and `prompts` when enabled); a flow inside a flow is a `Runnable`; no persistence in version 1.
- **Tests:** every example above runs with fake `Runnable`s and a fake clock (no sleeping), including the failure paths; `tests/budget` import matrix and cold-start budgets stay green; the skill (`src/skye/utils/claude_skill/skye/references/flow.md`, `python-api.md`) is updated in the same change and loses the "not built yet" lines (rule of `00-rules.md`).

Version 2, already decided and not part of this work: waiting for events with persistence (`wait`, `on_event`, snapshots in `store`, delivery guarantee O34), `to_mermaid()` and `skye render` (open decision O38), `include` (D51).
