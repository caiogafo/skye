# Implementation Plan: router

## Overview
Milestones in build order for the `router` component (codename jet): what exists, the gaps the audit of the code against Requirement 17
found (retries, the serving configuration, blocking calls, logging, lazy storage connection), the unfinished strategy and the missing
tests. Status is judged from the code in `src/skye/router` and the tests in `tests/unit/router` and `tests/stress`. Each task cites the
steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it honors. Task IDs cited from
other documents are `router:N.k`. The owner's decisions about `retry_after`, `exponential_backoff`, `priority` and the cost fields (D68) are in
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

- [x] 2. Gaps against Requirement 17.2
  - [x] 2.1 Record which configuration served each request and expose it with the configuration metadata for observability
    - Note: the response does not name the serving target today; the place (a response field, an event, both) is an open point.
    - Evidence (2026-11-08): `ModelRouter._record_serving` in `src/skye/router/model_router.py` puts the record in `response.metadata["router"]` and `ModelRouter.last_serving`; `tests/unit/router/test_serving_record.py` (alias, target, index, attempts, fallback, async path, copy, no secret).
    - _Requirements: 17.2, 17.6_
  - [x] 2.2 Apply `retry_policy`: retry a target `max_retries` times for its error type before the fallback chain
    - Note: `retry_policy` is stored and exported and never used by the routing loop. `retry_after` and `exponential_backoff` stay out until the owner's requirement is written in steering (owner decision of 2026-11-07).
    - Evidence (2026-11-08): the retry loop in `_try_model` of `src/skye/router/model_router.py` (same target first, MRO match, bounded by `max_retries`, stops on cooldown); `tests/unit/router/test_retry_policy.py`. `retry_after` and `exponential_backoff` stay out (task 6.1).
    - _Requirements: 17.2, 17.6_
  - [x] 2.3 Chain the last error into the final `ProviderError` (`raise ... from last`) instead of dropping it in `_try_model`
    - Evidence (2026-11-08): the final `ProviderError` is raised `from` the last error in `src/skye/router/model_router.py`; `tests/unit/router/test_retry_policy.py::test_the_final_provider_error_chains_the_last_error`.
    - _Requirements: 18.1_
  - [x] 2.4 Count the allowed fails per minute (they were counted over 24 hours)
    - Evidence (2026-11-08): `RECENT_FAILURES_WINDOW_SECONDS` and `recent_failure_count` in `src/skye/router/health_tracker.py`; `tests/unit/router/test_cooldown_policy.py::test_failures_older_than_a_minute_do_not_count_toward_the_allowed_fails`.
    - _Requirements: 17.7_

- [x] 3. Strategies
  - [x] 3.1 Implement `cost_based` selection from the cost per 1k tokens of each target, or remove the value from the enum and the language
    - Note: today it falls through to the first available target; the choice between implementing and removing is the owner's. The cost fields become real target fields only when this is implemented.
    - Evidence (2026-11-08, D68): `estimated_cost` and the `cost_based` branch in `src/skye/router/routing_strategies.py`; `cost_per_1k_*` on `ModelTarget` and `TargetSpec`; `tests/unit/router/test_cost_based.py` (cheapest, no cost last, ties, token estimate, negative rejected, the `.skye` block).
    - _Requirements: 17.1, 17.5; D68_

- [ ] 4. Serverless and Python rules
  - [x] 4.1 Call the model without blocking the loop (`acomplete`, or a worker thread) in `_try_model`
    - Note: `_try_model` calls the synchronous `model.complete` inside an `async def`.
    - Evidence (2026-11-08): `src/skye/router/model_router.py` calls `acomplete` or runs `complete` in `asyncio.to_thread`; `tests/unit/router/test_retry_policy.py::test_acomplete_of_the_model_is_awaited_on_the_loop`, `test_a_model_without_acomplete_runs_in_a_worker_thread`.
    - _Requirements: 17.2; Python rules of `00-rules`_
  - [x] 4.2 Connect the storage backend lazily at the first call instead of `asyncio.create_task` or `asyncio.run` in `__init__`
    - Evidence (2026-11-08): lazy connection in `src/skye/router/model_router.py` (`_storage_connected`, `_storage_connecting`, no task in `__init__`); `tests/unit/router/test_router_in_loop.py`, `test_retry_policy.py::test_a_router_built_inside_a_running_loop_starts_no_task`.
    - _Requirements: 17.2; Serverless rules of `00-rules`_
  - [x] 4.3 Structured logging (a message plus `extra={...}`) in place of the f-strings in `model_router.py`; never log a key or a substituted secret value
    - Evidence (2026-11-08): no f-string log call remains in `src/skye/router/model_router.py` (checked with `grep`); `tests/unit/router/test_retry_policy.py::test_failures_are_logged_with_structured_fields_and_no_key`.
    - _Requirements: 18.3, 17.4_
  - [ ] 4.4 `mark_model_failed` without `asyncio.create_task` / `asyncio.run` (the same clean-up as 4.2)
    - Note: it still uses both in `src/skye/router/model_router.py`; open.
    - _Requirements: 17.2; Serverless rules of `00-rules`_

- [x] 5. Tests
  - [x] 5.1 Unit tests for `ModelHealth` and `RateLimitTracker` (success rate, latency, cooldown expiry, minute window, active requests) against `InMemoryBackend`
    - Evidence (2026-11-08): `tests/unit/router/test_health_tracker.py` (success rate, latency, cooldown expiry, minute window, active requests, against `InMemoryBackend` and a fake clock).
    - _Requirements: 23.1, 23.2_
  - [x] 5.2 Unit tests for the cooldown and allowed-fails policy, for tag routing and for a router built inside a running loop
    - Evidence (2026-11-08): `tests/unit/router/test_cooldown_policy.py`, `test_tag_routing.py`, `test_router_in_loop.py`.
    - _Requirements: 23.2_
  - [x] 5.3 Unit tests for the retry policy and for the serving-configuration record, once 2.1 and 2.2 exist
    - Evidence (2026-11-08): `tests/unit/router/test_retry_policy.py`, `test_serving_record.py`.
    - _Requirements: 23.2_

- [ ] 6. Later (written, not scheduled)
  - [ ]* 6.1 `retry_after` and `exponential_backoff` with an injectable clock; `RetryPolicyConfig` gets the two fields; `to_config` and `to_skye` write them
    - Note: owner decision "not now"; requires the steering requirement first, then the skill reference `references/router.md` changes in the same change.
    - _Requirements: 17.2; D59_
  - [ ]* 6.2 `priority` and the two cost fields as `target` fields in `.skye`, and `ModelTarget.extras` accepted, only if a strategy reads them
    - Note: owner decision "version 2". The cost half was done early by D68 (task 3.1); `priority` and `ModelTarget.extras` in a block remain here.
    - _Requirements: 17.1; D59_
