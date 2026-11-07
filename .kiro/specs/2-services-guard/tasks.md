# Implementation Plan: guard

## Overview
Milestones in build order for the `guard` component (codename halo): the Port that exists, the built-in filters, the chain, the
pre-flight check, and packaging. Status is judged from the code in `src/skye/guard` (a placeholder) and the Ports in
`src/skye/base/interfaces`. Each task cites the steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`)
or the decision it honors. Task IDs cited from other documents are `guard:N.k`. Which filters ship first is an assumption in
`design.md`; the owner may change the list before task 2.

## Tasks
- [x] 1. What exists
  - [x] 1.1 `SafetyFilterInterface` and `SafetyResult` in `base`, and the `DecisionModel` Port
    - Evidence: `src/skye/base/interfaces/safety.py`, `src/skye/base/interfaces/decision.py`; `tests/unit/test_port_signatures.py`, `tests/unit/test_port_docstrings.py`.
    - _Requirements: 51.1, 9.8_

- [ ] 2. Filters and chain
  - [ ] 2.1 `SizeLimitFilter` and `BlocklistFilter`
    - _Requirements: 51.1_
  - [ ] 2.2 `PatternFilter` with named regular expressions and the ready patterns for e-mail, phone and card numbers (Luhn)
    - _Requirements: 51.1_
  - [ ] 2.3 `FilterChain`: ordered, merged violations, lowest confidence of the violating filters, optional stop at the first violation
    - _Requirements: 51.1_
  - [ ] 2.4 Tests: each filter, empty content, Luhn valid and invalid, chain merge, a user-written filter inside a chain, a non-string input
    - _Requirements: 51.1, 23.2_
  - [ ] 2.5 Port-compliance test over every built-in filter
    - _Requirements: 16.7_

- [ ] 3. Pre-flight checks
  - [ ] 3.1 `PreflightCheck` over a `DecisionModel`: options, allowed option and threshold from the caller, async form as the real one, a required failure mode
    - _Requirements: 51.2, 9.8_
  - [ ] 3.2 Tests with a fake decision model: allowed, refused, below the threshold, unavailable in each failure mode
    - _Requirements: 51.2, 23.2_

- [ ] 4. Packaging and budgets
  - [ ] 4.1 Make `skye.guard` importable with its real exports (D40: remove the placeholder `ImportError`); `models` is imported lazily, only where a pre-flight check is built
    - _Requirements: 7.3, 51.3; D40_
  - [ ] 4.2 Check that `guard` imports only `base` and `models`, no third-party library, and that no runtime component imports it; keep `guard` in `known_empty`
    - _Requirements: 2.2, 4.1, 51.3, 7.1_
  - [ ] 4.3 No log line carries the checked content; a test reads the captured logs
    - _Requirements: 18.3_
  - [ ] 4.4 Entry in `budgets.toml` for import time; the docs page `docs/guard/` and a runnable example
    - _Requirements: 7.5, 15.5, 24.2_
