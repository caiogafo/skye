# Implementation Plan: policy

## Overview
Milestones in build order for the `policy` component (codename isobar): the model and the evaluation first, then entities, loading and
validation, the authorizer integration and modes, policy sets with sources and cache, audit and metrics, and finally packaging,
budgets and the Cedar alignment. Status is judged from the code in `src/skye/policy` (a placeholder that raises `ImportError`, D40)
and from the Port in `src/skye/base/interfaces/authorizer.py`, which exists with `Decision`; nothing else is built, so every task is
open. Each task cites the steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it
honors. Task IDs cited from other documents are `policy:N.k`. Open decisions O9 and O10 stay open: a task that depends on one says so
and is built only as far as the decision allows.

## Tasks
- [x] 1. The Port (what exists)
  - [x] 1.1 `AuthorizerInterface` (`authorize(principal, action, resource) -> Decision`) and the `Decision` enum (`permit`, `forbid`) in `base`
    - Evidence: `src/skye/base/interfaces/authorizer.py`; `tests/unit/test_port_signatures.py`; `tests/unit/test_port_docstrings.py`.
    - _Requirements: 4.2_

- [ ] 2. Model and evaluation
  - [ ] 2.1 `Effect`, `Scope` (any, exact entity, set, membership), `Policy` (id, annotations, effect, scope, when, unless) and `PolicySet` as frozen dataclasses
    - _Requirements: 35.1, 35.2, 35.3; D24_
  - [ ] 2.2 `PolicyEngine.decide`: default deny, forbid wins, determining policy ids in the result, no side effect
    - _Requirements: 35.4, 35.5, 35.6_
  - [ ] 2.3 Condition parser and evaluator: comparisons, boolean operators, set membership, attribute presence, string prefix and suffix, entity hierarchy membership; loops, functions, I/O and regular expressions rejected at parse time; test whether the expression checker of `skye.base.dsl` can serve before writing a second one
    - _Requirements: 35.8, 35.9; D55_
  - [ ] 2.4 A condition that cannot be evaluated makes that policy not match and is recorded in the result; evaluation bounded by the size of the set, hierarchy walks use a visited set
    - _Requirements: 35.7, 35.10_

- [ ] 3. Entities, loading and validation
  - [ ] 3.1 `Entity` and the caller-supplied `EntityProvider`; an unknown entity has no attributes and no parents
    - _Requirements: 36.1, 36.3_
  - [ ] 3.2 Principals from an IAM identity and from JWT claims through a replaceable mapping function (default: the verified identity unchanged; the final rule waits for O10)
    - _Requirements: 36.2; O10_
  - [ ] 3.3 Load a policy set from JSON and TOML with the standard library; export it back to the representation it was loaded from; round-trip test
    - _Requirements: 36.4, 36.7_
  - [ ] 3.4 Report every error of a set together, each with the policy id and the position
    - _Requirements: 36.6_
  - [ ] 3.5 `PolicySchema` of entity types, actions and attributes given as data (a tool is an action; the caller builds it from the capability registry); reject the whole set at load time for an unknown action or attribute
    - _Requirements: 36.8, 36.9_
  - [ ]* 3.6 Cedar-like text syntax in `loader.py`, after the owner settles the first-release scope
    - Note: blocked on open decision O9; not started until it is settled.
    - _Requirements: 36.5; O9_

- [ ] 4. Authorizer integration and modes
  - [ ] 4.1 `PolicyEngine` satisfies `AuthorizerInterface`: `authorize` forwards to `decide` with an empty context; an unknown principal, action or resource is `forbid`; a malformed identifier raises
    - _Requirements: 37.1, 4.2_
  - [ ] 4.2 Enforce and log-only modes per policy set; in log-only mode return `permit` and record the decision that enforce would have made
    - _Requirements: 37.3_
  - [ ] 4.3 Make the public surface importable: replace the placeholder `ImportError` of `skye.policy` with the real exports, lazily (D40, `tests/unit/test_placeholder_packages.py` loses `policy`)
    - _Requirements: 37.1; D40_

- [ ] 5. Policy sets, sources and cache
  - [ ] 5.1 Sources: a file, an environment variable, and an external store (the `storage` Port when the caller passes one; DynamoDB through `boto3` imported lazily when named)
    - _Requirements: 37.4_
  - [ ] 5.2 Cache a loaded set with a time to live and refresh it inside the request that notices the expiry, with no background thread (the lifetime default waits for O10)
    - _Requirements: 37.5; O10_
  - [ ] 5.3 Version and SHA-256 content hash on every policy set
    - _Requirements: 37.6_

- [ ] 6. Audit and metrics
  - [ ] 6.1 One structured JSON log line per decision (principal, action, resource, decision, determining policies, set version and hash, latency); context values only when a setting enables them
    - _Requirements: 37.7_
  - [ ] 6.2 Counters for allow, deny and error through the `observer` Port of `base`; skipped when no observer is configured
    - _Requirements: 37.8_

- [ ] 7. Packaging, budgets and Cedar alignment
  - [ ] 7.1 No third-party import at module level; confirm the import-matrix and the standard-library-only checks pass for `policy`
    - _Requirements: 38.1, 2.2_
  - [ ] 7.2 Entry in `budgets.toml` for import time and an evaluation-time limit for a typical policy set; values from the owner (O10), measured first
    - _Requirements: 38.2; O10_
  - [ ] 7.3 Document in `docs/policy/` which parts of Cedar are implemented and which are left out; keep permit, forbid, scope and condition semantics identical to Cedar for the parts implemented
    - _Requirements: 38.3, 38.4_
  - [ ] 7.4 Conformance cases written from the Cedar documentation, each citing its page; replace them with an official suite if O9 finds one with a compatible licence
    - _Requirements: 38.5; O9_
  - [ ] 7.5 Unit tests for the cases listed in the testing strategy of `design.md`, including the eight correctness properties
    - _Requirements: 35, 36, 37_
