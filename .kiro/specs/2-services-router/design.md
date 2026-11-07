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
strategies are round robin, simple shuffle, least busy, latency based, rate-limit aware, weighted and priority based. `cost_based` is
accepted by the language and by `RoutingStrategy` but has no branch in `apply_strategy`: it falls through to "first available". It is
a gap, not a feature (see the notes below and task 3.1).

### Fallbacks, retries and cooldown (Requirement 17.2)
When the selected target fails, `_try_model` records the failure, may put the target in cooldown (the allowed-fails-per-minute policy
per error type) and returns `None`; the router then walks the fallback chain of the alias, each entry a registered model id or an
alias, and raises `ProviderError` naming what was tried if every one failed.

The audit found these gaps against Requirement 17.2 and the rules of `00-rules`:
- `retry_policy` (`max_retries` per error type) is stored, exported and re-read, but the routing loop never retries a target; only the
  fallback chain is walked. The same is true of `retry_after` and `exponential_backoff`, which the language reads.
- "Record which configuration served each request" is not done: the response does not say which target served it.
- `_try_model` calls the synchronous `model.complete` inside an `async def`, which blocks the event loop; it should call `acomplete`
  of the model or move the call to a worker thread.
- `_try_model` logs with f-strings; the rule is a message plus `extra={...}`.
- `ModelRouter.__init__` starts the storage connection with `asyncio.create_task` or `asyncio.run`, so building a router inside a
  running loop leaves an unawaited task; connection should happen lazily at the first call.

### Health, usage and cooldown
`ModelHealth` keeps success and failure counts, latency and the cooldown expiry; `RateLimitTracker` keeps requests and tokens per
minute window and the active-request count, with atomic `increment` of the storage Port. Both are keyed by model id.

### Notes absorbed from the `.skye` work of 2026-11-07 (owner decisions)
- **`retry_after` and `exponential_backoff` are read and not applied.** Decision of the owner: not now. The requirement to add, when it
  is taken up (steering first): the retry loop waits `retry_after` before the next attempt, doubles the wait after each failure when
  `exponential_backoff` is true, and the wait is injectable (a clock) so tests do not sleep; `RetryPolicyConfig` gets the two fields;
  `to_config` and `to_skye` write them. Until then the skill reference `references/router.md` says they are not applied.
- **`priority` and `cost_per_1k_prompt_tokens` / `cost_per_1k_completion_tokens` on a target.** Decision of the owner: noted for
  version 2, to declare as fields only if a strategy reads them. `priority_based` selects by success rate today. `ModelConfig` in
  `base/config.py` already has the two cost fields; when `cost_based` is implemented they become real target fields.
- **Extra fields of a target** (`ModelTarget.extras`) are kept by the Python API, are not exported by `to_config` or `to_skye`, and are
  not accepted by a `target { }` block (the checker reports an unknown field with a suggestion).

## Data Models
`Validated` dataclasses (D24; the project's own validated base): `ModelTarget`, `RouteConfig`, `FallbackConfig`, `RetryPolicyConfig`,
`AllowedFailsPolicyConfig`, `ModelHealthMetrics`, `UsageStats`, `CooldownInfo`. The strategy enum is in `base`.

## Error Handling
A configuration problem raises `ConfigurationError` with the field and the reason. A provider failure is mapped to the standard error
by the model adapter; the router records it, tries the next target, and raises `ProviderError` only when the chain is exhausted. The
swallowing of the original exception in `_try_model` loses the last error; the final `ProviderError` should chain the last one
(`raise ... from last`).

## Testing Strategy
Unit tests in `tests/unit/router/` cover configuration, files, export and shorthand, aliases, exports and strategy selection. Stress
tests in `tests/stress/` cover failover, rate limiting under load and concurrent routing (Requirement 23.3). Missing: unit tests for
`ModelHealth` and `RateLimitTracker` on their own, for the cooldown and allowed-fails policy, for tag routing, and for a router built
inside a running loop; none for `cost_based` because it has no behaviour yet.

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
- Whether `retry_policy` retries a target before falling back (the loop, the order against fallbacks, the wait): needs the steering requirement first (see the notes above).
- Where the serving configuration is reported (a field on the response, an event, or both) for Requirement 17.2.
- Whether the router's default storage stays `InMemoryBackend` or follows Requirement 12.2 (see the `store` spec).
