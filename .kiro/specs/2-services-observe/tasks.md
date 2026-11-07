# Implementation Plan: observe

## Overview
Milestones in build order for the `observe` component (codename radar): the Ports that exist, the built-in observers and the event
handler, metrics and traces, the exporter registry with the two core exporters, and packaging. Status is judged from the code in
`src/skye/observe` (a placeholder) and the Ports in `src/skye/base/interfaces`. Each task cites the steering requirement numbers it
satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it honors. Task IDs cited from other documents are
`observe:N.k`. The `flush` question of `design.md` is settled in steering before the tasks that depend on it.

## Tasks
- [x] 1. What exists
  - [x] 1.1 `ObserverInterface`, `EventType` and `EventHandlerInterface` in `base`
    - Evidence: `src/skye/base/interfaces/observer.py`, `src/skye/base/interfaces/event_handler.py`; `tests/unit/test_port_signatures.py`, `tests/unit/test_port_docstrings.py`.
    - _Requirements: 53.1_
  - [x] 1.2 The placeholder package and the empty extra `observe` in `known_empty`
    - Evidence: `src/skye/observe/__init__.py`; `budgets.toml`; `tests/unit/test_placeholder_packages.py`.
    - _Requirements: 53.3; D40_

- [ ] 2. Observers and the event handler
  - [ ] 2.1 `LoggingObserver`: JSON lines through `logging` with `extra`, a redaction list, never raises
    - _Requirements: 53.1, 18.3_
  - [ ] 2.2 `MemoryObserver` for tests and `CompositeObserver` fan-out that isolates a failing member
    - _Requirements: 53.1_
  - [ ] 2.3 `ObserverEventHandler`: the eight lifecycle methods become events; arguments and results only when enabled
    - _Requirements: 53.1, 40.10_
  - [ ] 2.4 Tests: each observer, each of the eight handler methods, redaction, a failing member, the Port-compliance checker
    - _Requirements: 53.1, 16.7, 23.2_

- [ ] 3. Metrics and traces
  - [ ] 3.1 In-process counters and gauges keyed by name and tags, and the metric sample format
    - _Requirements: 53.1_
  - [ ] 3.2 Trace and span identifiers in W3C trace-context form, the active trace in a `contextvars` variable, header parse and write
    - _Requirements: 53.1_
  - [ ] 3.3 Tests: counters and tags, concurrent tasks keep separate traces, header round trip
    - _Requirements: 53.1, 23.2_

- [ ] 4. Exporters
  - [ ] 4.1 Exporter protocol and the registry (`register_exporter`, `resolve_exporter`), in the shape of the `auth` registry: duplicate name is an error unless replacing, an unknown name lists the known ones
    - _Requirements: 53.2, 6.1, 6.2_
  - [ ] 4.2 Core exporters with no library: standard output JSON lines, and CloudWatch embedded metric format
    - _Requirements: 53.1, 7.1_
  - [ ] 4.3 Settle the `flush` question in steering (a small separate Port or a method), then add buffering for exporters that send over the network
    - Note: blocked on the first open point of `design.md`; steering first, no background thread.
    - _Requirements: 16.9; Serverless rules of `00-rules`_
  - [ ] 4.4 Tests: registry rules, an exporter that raises (the run continues, one warning, a counter), the embedded metric line against the CloudWatch documentation example
    - _Requirements: 53.2, 23.2_
  - [ ]* 4.5 An optional exporter that needs a library (for example OpenTelemetry), importing it lazily and declaring only that library in the extra `observe`; remove `observe` from `known_empty` in the same change
    - Note: only when the owner asks for a specific exporter.
    - _Requirements: 53.3, 7.1, 7.3_

- [ ] 5. Packaging and budgets
  - [ ] 5.1 Make `skye.observe` importable with its real exports (D40: remove the placeholder `ImportError`); no third-party import at import time
    - _Requirements: 7.3, 53.4; D40_
  - [ ] 5.2 Check that `observe` imports only `base` and that no runtime component imports it
    - _Requirements: 2.2, 4.1, 53.4_
  - [ ] 5.3 Entry in `budgets.toml` for import time; the docs page `docs/observe/` updated and a runnable example
    - _Requirements: 7.5, 15.5, 24.2_
