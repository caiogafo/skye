Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, The `.skye` language, Extras and budgets)

# Design Document: router

## Overview
`router` is the services layer-2 component (codename jet). It turns a logical model name (an alias) into a concrete model target, applies
a routing strategy, tracks health and rate limits, and falls back when a target fails (Requirement 17). It is configured in code, from a
`.skye` `router` block or from a JSON object, with `${VAR}` and `env.NAME` substitution so that no secret is hardcoded (Requirement
17.3, 17.4; D59, D62). It imports only `base`, `models` and `store` (`11-design.md`, "Allowed imports"), uses only the standard library
and ships with the core with no extra. The layer, the allowed imports, the Ports, the `.skye` rules and the extras policy are in the
steering sections named above and are not restated here.

The component exists and is large (about 2,300 lines in `src/skye/router/`), so this design records what it is and what the audit of
the code against Requirement 17 found. It is a design of the current shape plus the gaps, not a rewrite.

## Architecture
```
router/
  model_router.py      ModelRouter: registration, selection, routing, fallbacks, health and usage, configuration, from_file / to_skye
  config_models.py     ModelTarget, RouteConfig, FallbackConfig, RetryPolicyConfig, AllowedFailsPolicyConfig, ModelHealthMetrics, UsageStats, CooldownInfo
  routing_strategies.py  RoutingStrategySelector: round robin, shuffle, least busy, latency, rate-limit aware, weighted, priority
  health_tracker.py    ModelHealth and RateLimitTracker: counters kept in a StorageBackend, never in the process
  skye_file.py         RouterSpec <-> configuration dictionary; reading a .skye router block or a JSON object
```
`ModelRouter` implements the three role Ports of `base` (selection, health, configuration) and so `ModelRouterInterface` (D41). State
that must survive between invocations lives in a `StorageBackend` passed by the caller, `InMemoryBackend` by default; the health and
rate-limit trackers read and write only through it (`00-rules`, "Serverless first").

### Configuration (Requirement 17.1, 17.3, 17.4)
A route is an alias with one or more `ModelTarget`s (provider, model, temperature, maximum tokens, rate limits, weight, priority) and
a strategy. The shorthand `{"alias": ["provider/model", ...]}` builds the same objects, the first entry primary and the rest its
fallbacks (Requirement 22.8). `ModelRouter.from_file(path, name=None)` reads a `.skye` `router` block or a JSON object: the parser in
`base` returns a `RouterSpec`, `skye_file.py` turns it into the configuration dictionary, and `from_config_dict` builds the router
(D50, D59, D61). `to_config(include_secrets=False)` and `to_skye(name=None, include_secrets=False)` go the other way, through the same
dictionary (D65); secrets are written as `env.NAME` references. A field named with the suffix `_seconds` in the old format is a
duration without the suffix in `.skye` (D59). An invalid file raises `ConfigurationError` with the details; a missing environment
variable raises `ConfigurationError` and the substitution is logged at DEBUG level, without the value.

### Selection and strategies
`select_model` resolves an alias to one registered target: it takes the available targets (not in cooldown, within rate limits when the
pre-call check is on), reads the metrics the strategy needs once with `prepare`, then picks synchronously from that snapshot. The
strategies are round robin, simple shuffle, least busy, latency based, rate-limit aware, weighted, priority based and cost based
(the lowest `cost_per_1k_prompt_tokens + cost_per_1k_completion_tokens` of the target, see the notes below and task 3.1; D68).

### Fallbacks, retries and cooldown (Requirement 17.2, 17.6, 17.7)
`_try_model` calls the target, and when it fails the router applies the `retry_policy` of that error type (the most specific class in the
exception's MRO wins) and retries the **same target** immediately, up to `max_retries`; only then it walks the fallback chain of the alias,
each entry a registered model id or an alias. A failure is recorded in the health of the target; a target that reaches its
allowed-fails-per-minute count goes into cooldown and is not retried. Each attempt is logged with `extra={...}` (never a key). If every
target fails, `ProviderError` names what was tried and chains the last error (`raise ... from last`). The default policy now does retry
(a change of behaviour). `retry_after` and `exponential_backoff` are read and not applied (see the notes below).

The model is called without blocking the loop: its `acomplete` when it has one, otherwise `complete` in a worker thread. The storage
backend connects lazily at the first call, on the loop of that call, so a router built inside a running loop starts no task. The
allowed-fails policy counts failures of the **last minute** (`ModelHealth` keeps the times of the recent failures per error type in the
storage, with a 60 second window, `RECENT_FAILURES_WINDOW_SECONDS`); it used to count the failures of 24 hours.

The serving record (Requirement 17.6). Each response carries `response.metadata["router"]`: the alias, the target (model id, provider),
its index in the route, the attempts and what was tried before it, with no secret; the same dictionary (a copy) is `ModelRouter.last_serving`.
A failed request keeps the previous record.

Left as it was: `mark_model_failed` still uses `asyncio.create_task` / `asyncio.run` (task 4.4).

### Health, usage and cooldown
`ModelHealth` keeps success and failure counts, latency and the cooldown expiry; `RateLimitTracker` keeps requests and tokens per
minute window and the active-request count, with atomic `increment` of the storage Port. Both are keyed by model id.

### Notes absorbed from the `.skye` work of 2026-11-07 (owner decisions)
- **`retry_after` and `exponential_backoff` are read and not applied.** Decision of the owner: not now. The requirement to add, when it
  is taken up (steering first): the retry loop waits `retry_after` before the next attempt, doubles the wait after each failure when
  `exponential_backoff` is true, and the wait is injectable (a clock) so tests do not sleep; `RetryPolicyConfig` gets the two fields;
  `to_config` and `to_skye` write them. Until then the skill reference `references/router.md` says they are not applied.
- **`priority` on a target.** Decision of the owner: noted for version 2, to declare as a field only if a strategy reads it.
  `priority_based` selects by success rate today.
- **`cost_per_1k_prompt_tokens` / `cost_per_1k_completion_tokens` on a target are real fields (D68, owner decision of 2026-11-08).**
  They are declared on `ModelTarget` and `TargetSpec` (number or none, 0 or more), accepted by a `target { }` block and written back by
  `to_config`, `to_skye` and the JSON form. `cost_based` (`routing_strategies.py`) picks the available target with the lowest
  estimated cost: the sum of the two prices, or, when the caller passes a token estimate `(prompt_tokens, completion_tokens)` to
  `apply_strategy`, each price times its tokens / 1000. A price left out counts as 0; a target with neither comes after every priced
  target; ties keep the configured order. This pulls the cost half of task 6.2 forward; `priority` and `extras` stay there.
- **Extra fields of a target** (`ModelTarget.extras`) are kept by the Python API, are not exported by `to_config` or `to_skye`, and are
  not accepted by a `target { }` block (the checker reports an unknown field with a suggestion).

## Data Models
`Validated` dataclasses (D24; the project's own validated base): `ModelTarget`, `RouteConfig`, `FallbackConfig`, `RetryPolicyConfig`,
`AllowedFailsPolicyConfig`, `ModelHealthMetrics`, `UsageStats`, `CooldownInfo`. The strategy enum is in `base`.

## Error Handling
A configuration problem raises `ConfigurationError` with the field and the reason. A provider failure is mapped to the standard error
by the model adapter; the router records it, retries per the policy, tries the next target, and raises `ProviderError` only when the
chain is exhausted; that error chains the last one (`raise ... from last`).

## Testing Strategy
Unit tests in `tests/unit/router/` cover configuration, files, export and shorthand, aliases, exports and strategy selection. Stress
tests in `tests/stress/` cover failover, rate limiting under load and concurrent routing (Requirement 23.3). The tests of
`ModelHealth` and `RateLimitTracker` on their own, of the cooldown and allowed-fails policy, of tag routing and of a router built
inside a running loop are in `tests/unit/router/`: `test_health_tracker.py` (`ModelHealth`, `RateLimitTracker`), `test_cooldown_policy.py`,
`test_tag_routing.py`, `test_router_in_loop.py`, `test_retry_policy.py` (retry order, chained error, `acomplete`, structured log without a key),
`test_serving_record.py` and `test_cost_based.py`; they share `conftest.py` and `fakes.py` (a scripted model and a fake clock).

## Correctness Properties
1. Registering a route and resolving its alias returns one of its targets, never a target outside it.
2. A target in cooldown, or over its rate limit with the pre-call check on, is not selected while another target is available.
3. With `fallbacks` set, a failing primary leads to the fallbacks in order, and the first success is returned (17.2).
4. If every target of the chain fails, the router raises `ProviderError` that names what was tried.
5. `to_skye` then `from_file` gives a router with the same routes, and writing twice gives the same text (D65).
6. A missing environment variable in a configuration raises `ConfigurationError` and no value is logged (17.4).
7. The shorthand and the full form build equal routers (Requirement 22.8).
8. The router keeps no state between invocations outside the storage backend (Serverless first).

## Open points (not decided here)
- The wait between retries (`retry_after`, `exponential_backoff`): not applied; needs the injectable clock and the skill reference changed in the same change (task 6.1).
- Whether the serving record should also be an event for `observe` (today: the response metadata and `last_serving`).
- Requirement 17.6 and 17.7 record built behaviour (retry before fallback, the per-minute window) that has no decision line of its own; the owner confirms or changes them.
- Whether the router's default storage stays `InMemoryBackend` or follows Requirement 12.2 (see the `store` spec).
