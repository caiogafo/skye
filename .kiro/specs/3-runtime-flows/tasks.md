# Implementation Plan: flows

## Overview
Milestones in build order for the `flows` component (codename stream): what exists (the language, the checker and the loader), the
run context and the sequential interpreter, conditions and loops, parallel steps and `foreach`, retry, timeout and errors, cycle
detection, and packaging with the skill. Status is judged from the code in `src/skye/flows` and `src/skye/base/dsl` and from
`tests/unit/flows` and `tests/unit/dsl`. Each task cites the steering requirement numbers it satisfies (`Requirement N.k` of
`10-requirements.md`) or the decision it honors. Task IDs cited from other documents are `flows:N.k`. Version 2 (persistence,
`to_mermaid()`, `include`) is not scheduled here.

## Tasks
- [x] 1. What exists
  - [x] 1.1 The `.skye` parser, the flow model, `evaluate`, the load-time checks of Requirement 54.4 and the rejection of `wait` and `on_event`
    - Evidence: `src/skye/base/dsl/` (`build.py`, `specs.py`, `expressions.py`); `tests/unit/dsl/test_conformance.py`, `tests/unit/dsl/test_expressions.py`.
    - _Requirements: 50.5, 50.6, 54.1, 54.3, 54.4, 54.5; D54 to D58_
  - [x] 1.2 `Flow.from_file`, `Flow.from_text`, `Flow.check`, `Flow.to_text` and the registry-name check
    - Evidence: `src/skye/flows/flow.py`; `tests/unit/flows/test_loading.py`.
    - _Requirements: 50.4, 54.9; D52, D61_
  - [x] 1.3 `flows` imports no other runtime component and `import skye` does not load it
    - Evidence: `tests/unit/flows/test_loading.py` (`test_flows_imports_no_other_runtime_component`, `test_import_skye_does_not_load_flows_or_the_parser`); `tests/budget/test_import_matrix.py`.
    - _Requirements: 50.4, 5.1, 5.4_

- [ ] 2. Run context and the sequential interpreter
  - [ ] 2.1 `RunContext`: the declared fields with their types and defaults, a missing required field is a validation error naming it, the outputs at `step.<Name>.output`
    - _Requirements: 50.1, 54.4; D58_
  - [ ] 2.2 `Flow.arun` (real) and `Flow.run` (runs it), plus `invoke` and `ainvoke` so `Flow` is a `Runnable`; replace the `NotImplementedError`
    - _Requirements: 50.1, 5.1; D43_
  - [ ] 2.3 Steps: resolve `registry.NAME`, `flow.NAME`, `router.NAME` to a `Runnable`, evaluate `input` with `evaluate`, store the output, apply `set` and `emit` after a success, follow `next`, `next = end` returns the last output
    - _Requirements: 50.1, 50.2; D52, D55, D58_
  - [ ] 2.4 Choice: `when` branches in order, `else` always matches, the branch's `set`, `emit` and `next`
    - _Requirements: 50.1; D55_
  - [ ] 2.5 Tests with fake `Runnable`s for the sequence, the condition and the context (reference examples F1, F2, F8)
    - _Requirements: 50.2, 23.2_

- [ ] 3. Loops and sub-flows
  - [ ] 3.1 `max_visits` counted at run time per step; a re-entry over the limit raises an error naming the step
    - _Requirements: 50.5; D56_
  - [ ] 3.2 A flow as a step of another flow; the visited set and the depth bound (default 100) that stop a flow containing itself, directly or transitively, with an error naming the cycle
    - _Requirements: 50.3, 5.3_
  - [ ] 3.3 Tests: a bounded loop and the error past the bound, a sub-flow, a direct cycle, a transitive cycle, the depth bound (reference examples F4, F7)
    - _Requirements: 50.3, 5.3, 23.2_

- [ ] 4. Parallel and foreach
  - [ ] 4.1 `parallel` with `asyncio.TaskGroup`: `join = all | any` (`any` cancels the rest), `on_branch_error = cancel | continue` (a failed branch gives an empty output)
    - _Requirements: 50.2; D56_
  - [ ] 4.2 Context changes of branches applied one at a time in document order after the block
    - _Requirements: 50.2; D56_
  - [ ] 4.3 `foreach`: one run of the step or sub-flow per element, in parallel, `item` bound, a list output in input order; a non-list is an error naming the step; a concurrency limit argument
    - _Requirements: 50.2; D56, D58_
  - [ ] 4.4 Tests: each join and error mode, cancellation, document-order writes, `foreach` order (reference example F3, F7)
    - _Requirements: 50.2, 23.2_

- [ ] 5. Retry, time and errors
  - [ ] 5.1 `retry = { max, after, backoff }` before the `on_error` transition, the wait through an injectable clock
    - _Requirements: 50.1, 50.5; D54_
  - [ ] 5.2 `timeout` with `asyncio.timeout`, `on_timeout` and `on_error` transitions; a timeout without `on_timeout` is an error
    - _Requirements: 50.1, 50.5; D54_
  - [ ] 5.3 The default error end: the flow stops, the error reaches the caller with the step name, and a record goes to the observer Port when one was passed
    - _Requirements: 50.1, 4.1; D54_
  - [ ] 5.4 Tests with a fake clock and failing `Runnable`s: retry, backoff, timeout paths, `on_error`, the default end and its record (reference example F5)
    - _Requirements: 50.2, 23.2_

- [ ] 6. Packaging, skill and docs
  - [ ] 6.1 `import skye.flows` stays free of third-party imports; no multiprocessing and no work after the call returns; an entry in `budgets.toml` for the cold-start budget if the runtime adds modules
    - _Requirements: 7.1, 7.5; Serverless rules of `00-rules`_
  - [ ] 6.2 Update the skill (`references/flow.md`, `references/python-api.md`) and its eval in the same change, removing the "not built yet" lines; `tests/unit/dsl/test_claude_skill.py` must pass
    - _Requirements: 54.14; rule of `00-rules`_
  - [ ] 6.3 Update `docs/flows/` and add a runnable example of a flow with fake steps under `examples/flows/`
    - _Requirements: 15.5, 24.2, 24.4_
  - [ ] 6.4 Decide with the owner the `utils` note of the open points (name it in `11-design.md` or move the file reader into `base`)
    - Note: steering first, then this spec cites the result.
    - _Requirements: 50.4, 15.4_
