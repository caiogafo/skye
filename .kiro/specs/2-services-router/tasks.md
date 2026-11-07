# Implementation Plan: router

## Overview
Milestones in build order for the `router` component (codename jet): what exists, the gaps the audit of the code against Requirement 17
found (retries, the serving configuration, blocking calls, logging, lazy storage connection), the unfinished strategy and the missing
tests. Status is judged from the code in `src/skye/router` and the tests in `tests/unit/router` and `tests/stress`. Each task cites the
steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it honors. Task IDs cited from
other documents are `router:N.k`. The owner's decisions about `retry_after`, `exponential_backoff`, `priority` and cost fields are in
`design.md` ("Notes absorbed"): a change to a requirement is made in steering first.

## Tasks
- [x] 1. What exists
  - [x] 1.1 `ModelRouter` with aliases, targets, strategies, fallbacks, cooldown, rate limits and usage statistics
    - Evidence: `src/skye/router/model_router.py`, `src/skye/router/routing_strategies.py`, `src/skye/router/health_tracker.py`; `tests/unit/router/test_alias_routing.py`, `tests/unit/router/test_routing_strategies.py`; `tests/stress/test_failover.py`, `tests/stress/test_rate_limiting.py`, `tests/stress/test_concurrent_routing.py`.
    - _Requirements: 17.1, 17.2, 23.3_
  - [x] 1.2 Configuration dataclasses and the shorthand `{"alias": ["provider/model", ...]}`
    - Evidence: `src/skye/router/config_models.py`; `tests/unit/router/test_router_config_model.py`, `tests/unit/router/test_router_shorthand.py`.
    - _Requirements: 17.1, 22.8_
  - [x] 1.3 Reading `.skye` and JSON router files, `from_config_dict`, `to_config`, `to_skye`, `${VAR}` and `env.NAME` substitution
    - Evidence: `src/skye/router/skye_file.py`; `tests/unit/router/test_router_file.py`, `tests/unit/router/test_router_from_config.py`, `tests/unit/router/test_router_export.py`, `tests/unit/router/test_router_examples_equivalence.py`, `tests/unit/router/test_sample_configs.py`.
    - _Requirements: 17.3, 17.4; D59, D62, D65_
  - [x] 1.4 The three role Ports and a clean public surface (`skye.router` without the storage re-exports)
    - Evidence: `src/skye/router/__init__.py`; `tests/unit/router/test_router_exports.py`.
    - _Requirements: 16.6; D40, D41_

- [ ] 2. Gaps against Requirement 17.2
  - [ ] 2.1 Record which configuration served each request and expose it with the configuration metadata for observability
    - Note: the response does not name the serving target today; the place (a response field, an event, both) is an open point.
    - _Requirements: 17.2_
  - [ ] 2.2 Apply `retry_policy`: retry a target `max_retries` times for its error type before the fallback chain
    - Note: `retry_policy` is stored and exported and never used by the routing loop. `retry_after` and `exponential_backoff` stay out until the owner's requirement is written in steering (owner decision of 2026-11-07).
    - _Requirements: 17.2_
  - [ ] 2.3 Chain the last error into the final `ProviderError` (`raise ... from last`) instead of dropping it in `_try_model`
    - _Requirements: 18.1_

- [ ] 3. Strategies
  - [ ] 3.1 Implement `cost_based` selection from the cost per 1k tokens of each target, or remove the value from the enum and the language
    - Note: today it falls through to the first available target; the choice between implementing and removing is the owner's. The cost fields become real target fields only when this is implemented.
    - _Requirements: 17.1_

- [ ] 4. Serverless and Python rules
  - [ ] 4.1 Call the model without blocking the loop (`acomplete`, or a worker thread) in `_try_model`
    - Note: `_try_model` calls the synchronous `model.complete` inside an `async def`.
    - _Requirements: 17.2; Python rules of `00-rules`_
  - [ ] 4.2 Connect the storage backend lazily at the first call instead of `asyncio.create_task` or `asyncio.run` in `__init__`
    - _Requirements: 17.2; Serverless rules of `00-rules`_
  - [ ] 4.3 Structured logging (a message plus `extra={...}`) in place of the f-strings in `model_router.py`; never log a key or a substituted secret value
    - _Requirements: 18.3, 17.4_

- [ ] 5. Tests
  - [ ] 5.1 Unit tests for `ModelHealth` and `RateLimitTracker` (success rate, latency, cooldown expiry, minute window, active requests) against `InMemoryBackend`
    - _Requirements: 23.1, 23.2_
  - [ ] 5.2 Unit tests for the cooldown and allowed-fails policy, for tag routing and for a router built inside a running loop
    - _Requirements: 23.2_
  - [ ] 5.3 Unit tests for the retry policy and for the serving-configuration record, once 2.1 and 2.2 exist
    - _Requirements: 23.2_

- [ ] 6. Later (written, not scheduled)
  - [ ]* 6.1 `retry_after` and `exponential_backoff` with an injectable clock; `RetryPolicyConfig` gets the two fields; `to_config` and `to_skye` write them
    - Note: owner decision "not now"; requires the steering requirement first, then the skill reference `references/router.md` changes in the same change.
    - _Requirements: 17.2; D59_
  - [ ]* 6.2 `priority` and the two cost fields as `target` fields in `.skye`, and `ModelTarget.extras` accepted, only if a strategy reads them
    - Note: owner decision "version 2".
    - _Requirements: 17.1; D59_
