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

- [x] 4. Serverless and Python rules
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
  - [x] 4.4 `mark_model_failed` without `asyncio.create_task` / `asyncio.run` (the same clean-up as 4.2)
    - Evidence (2026-11-11): `amark_model_failed` in `src/skye/router/model_router.py` sets the cooldown on the router's store; `mark_model_failed` runs it to the end through `_run_sync`, as the other synchronous methods do, so no task is left behind and the cooldown is stored when the call returns; `tests/unit/router/test_review_fixes.py::test_mark_model_failed_in_a_running_loop_takes_effect_at_once`, `test_mark_model_failed_outside_a_loop`.
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
  - [x]* 6.1 `retry_after` and `exponential_backoff` with an injectable clock; `RetryPolicyConfig` gets the two fields; `to_config` and `to_skye` write them
    - Note: taken up on 2026-11-11 with D104 (the router owns the retries and honours the provider's `Retry-After`), at the owner's request.
    - Evidence (2026-11-11): `RetryPolicyConfig.retry_after_seconds` and `exponential_backoff` in `src/skye/router/config_models.py`; `ModelRouter._retry_wait` and the `sleep` argument of `ModelRouter` (injectable, `asyncio.sleep` by default) in `src/skye/router/model_router.py`; `retry_after = "5s"` read as `retry_after_seconds` and written back in `src/skye/router/skye_file.py`; `references/router.md` of the skill updated; `tests/unit/router/test_review_fixes.py::test_retry_after_seconds_and_exponential_backoff_are_applied`, `test_the_error_retry_after_wins_when_it_is_longer_than_the_policy_wait`, `test_the_wait_fields_are_exported_and_read_back`.
    - _Requirements: 17.2; D59, D104_
  - [ ]* 6.2 `priority` and the two cost fields as `target` fields in `.skye`, and `ModelTarget.extras` accepted, only if a strategy reads them
    - Note: owner decision "version 2". The cost half was done early by D68 (task 3.1); `priority` and `ModelTarget.extras` in a block remain here.
    - _Requirements: 17.1; D59_

- [x] 7. Fixes found by the documentation review (2026-11-11)
  - [x] 7.1 An alias with no available target walks its fallback chain before raising
    - Evidence (2026-11-11): `_aroute_request_internal` and `_try_entry` in `src/skye/router/model_router.py` select inside the chain loop (a target in cooldown or over its `rpm` no longer stops the request); the selection error is raised only when nothing in the chain was available; `tests/unit/router/test_review_fixes.py::test_an_alias_whose_targets_are_all_in_cooldown_uses_its_fallback_chain`, `test_an_alias_over_its_rpm_uses_its_fallback_chain`, `test_with_no_fallback_the_selection_error_is_still_raised`.
    - _Requirements: 17.2_
  - [x] 7.2 `from_file` and `from_config_dict` pass `storage` and the other `ModelRouter` keyword arguments through, and reject an unknown keyword
    - Evidence (2026-11-11): `_ROUTER_KEYWORDS` and `_check_keywords` in `src/skye/router/model_router.py` (`ConfigurationError` that names the accepted keywords and the closest match; `fallbacks` and the policies are added after the file's); `tests/unit/router/test_review_fixes.py::test_from_config_dict_passes_the_storage_through`, `test_from_file_passes_the_storage_through`, `test_an_unknown_keyword_is_rejected_with_the_accepted_names`, `test_keyword_policies_are_added_after_the_file`.
    - _Requirements: 17.3; D97_
  - [x] 7.3 The default policies name the provider errors of D104, both policies match the class hierarchy, the router waits `error.retry_after` and turns the client's own retries off
    - Evidence (2026-11-11): `DEFAULT_RETRY_POLICY` (`RateLimitError` 3, `ServerError` 2, `ProviderTimeoutError` 2, `AuthenticationError` 0) and `DEFAULT_ALLOWED_FAILS_POLICY` (`RateLimitError` 100, `ContentPolicyError` 1000) in `src/skye/router/model_router.py`; `_matching_policy` serves both policies, and the allowed-fails window counts a failure under the entry that matched (`ModelHealth.record_failure(window_reason=...)`); a `retry_after` longer than the cooldown moves on to the next target; `_disable_client_retries` sets `max_retries = 0` on every client the router builds and on a registered model that has the attribute; `tests/unit/router/test_review_fixes.py::test_the_default_retry_policy_matches_the_provider_errors`, `test_the_default_policies_name_existing_error_classes`, `test_the_allowed_fails_policy_matches_through_the_class_hierarchy`, `test_the_router_waits_the_retry_after_of_the_error`, `test_a_retry_after_longer_than_the_cooldown_goes_to_the_fallback`, `test_a_target_built_by_the_router_has_its_client_retries_off`, `test_a_registered_model_with_client_retries_has_them_turned_off`.
    - _Requirements: 17.2, 17.7; D104_
  - [x] 7.4 A route with no strategy of its own uses the router's
    - Evidence (2026-11-11): `RouteConfig.strategy` defaults to `None` in `src/skye/router/config_models.py`; `_select_from_alias` falls back to `ModelRouter.strategy`; `to_config` writes a route's strategy only when it differs from the router's; `tests/unit/router/test_review_fixes.py::test_the_router_strategy_applies_to_a_python_route_without_its_own`, `test_a_route_strategy_still_wins_over_the_router`.
    - _Requirements: 17.1_
  - [x] 7.5 `RouteConfig.fallback_on_error` and `ModelTarget.max_retries` are read by the router
    - Evidence (2026-11-11): with `fallback_on_error` (the default) a failed target is followed by the other available targets of its route before the fallback chain (`_try_entry`); a target's `max_retries` replaces the policy's count for the error types the policy retries (`_retries_for`); `tests/unit/router/test_review_fixes.py::test_fallback_on_error_tries_the_other_targets_of_the_route`, `test_without_fallback_on_error_the_other_targets_are_not_tried`, `test_the_max_retries_of_a_target_overrides_the_policy_count`, `test_the_max_retries_of_a_target_does_not_retry_an_error_the_policy_does_not_retry`; `tests/unit/router/test_serving_record.py::test_a_fallback_is_recorded_with_what_was_tried` now expects both targets of the route in `tried`.
    - _Requirements: 17.2_
  - [x] 7.6 `ModelTarget.options` carries the provider settings a target has no field for
    - Evidence (2026-11-11): `options` in `src/skye/router/config_models.py` (`${NAME}` substituted and exported as written) and passed after the other settings to the provider in `_register_route`; JSON files keep the references (`substitute_env_vars_keeping_target_references` in `src/skye/router/skye_file.py`). The `.skye` target block takes `options` too (a map, `env.NAME` allowed): `TargetSpec.options` in `src/skye/base/dsl/specs.py`, the field list in `build.py`, `to_text` in `emit.py`, and the conversions in `src/skye/router/skye_file.py`; `tests/unit/router/test_target_options_skye.py` (from a file to the `ModelTarget`, the round trip keeping `env.NAME`, a shorthand entry).
    - _Requirements: 17.1, 17.4_
  - [x] 7.7 Health counts are atomic increments of the store; `set_rate_limits` on an unknown model uses the router's store
    - Evidence (2026-11-11): `ModelHealth` in `src/skye/router/health_tracker.py` keeps the success, failure, latency and per-error-type counts and the failures of the last minute (one counter per second) as `CounterStore.increment` keys; only the latest times and the latency range are read and written back; `set_rate_limits` builds the tracker with `model_id` and `storage_backend`; `tests/unit/router/test_review_fixes.py::test_concurrent_failures_and_successes_lose_no_count`, `test_set_rate_limits_on_an_unknown_model_uses_the_router_store`; `tests/unit/router/test_health_tracker.py` and `test_cooldown_policy.py` unchanged and passing.
    - _Requirements: 17.2, 17.7; D98_
  - [x] 7.8 Current docstrings, documentation, examples and skill
    - Evidence (2026-11-11): the `RoutingStrategy` docstring in `src/skye/base/interfaces/router.py` names `ROUND_ROBIN` as the router's default; the `skye.router` package docstring reads `health.success_rate` and shows `from_file(..., storage=...)`; the warnings for the fixed behaviour are removed from `docs/guides/routing/aliases-and-fallbacks.md`, `health-and-cooldown.md`, `router-state.md` and `strategies.md`, which document the error classes, the waits, `options` and `storage` through `from_file`; `examples/routing/router_config.skye`, `fallbacks_and_health.py`, `skye_config_example.py` and `README.md` use `ProviderTimeoutError` and the waits (`tests/unit/router/test_router_examples_equivalence.py` maps the old `TimeoutError` name); `references/router.md` and `references/python-api.md` of the skill and one new eval; `tests/unit/router/test_review_fixes.py::test_the_docstrings_are_current`.
    - _Requirements: 17.1, 17.2; D104_
