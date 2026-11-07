---
component: router
codename: jet
---

# Requirements Document

## Introduction

The model router: configuration, fallbacks and health, over the models. This spec is at the requirements stage: the design and the tasks come after the requirements are approved.

The requirements themselves live in `.kiro/steering/10-requirements.md`; each requirement below is one user story of this component, and each acceptance criterion is a pointer to the steering criterion it realizes (never a copy).

## Requirements

### Requirement 1: Router and model configuration

**User Story:** As a platform engineer, I want to configure model routing with fallbacks in code or in a `.skye` file, so that my applications stay available when a provider has issues and I do not hardcode secrets.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 17.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 17.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 17.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 17.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 2: Tests

**User Story:** As a developer, I want an organized and sufficient test suite, so that I can trust the library and find the tests I need.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 23.3 of #[[file:.kiro/steering/10-requirements.md]].

## Notes to integrate (from the `.skye` work of 2026-11-07; the owner asked for them here, to be absorbed when this spec's requirements and design are written)

Found while checking that `.skye` carries everything the old `examples/routing/router_config.yaml` said (the file read by the router before YAML was removed, D62):

- **`retry_after` and `exponential_backoff` are read and not applied.** The language reads them in `retry_policy "<error>" { max_retries, retry_after, exponential_backoff }` (the old `retry_after_seconds` and `exponential_backoff`), but `RetryPolicyConfig` has only `error_type` and `max_retries` and the router's retry loop waits for nothing. The YAML had the same fields and ignored them. **Decision of the owner: not now.** Requirement to add: the retry loop waits `retry_after` before the next attempt, doubles the wait after each failure when `exponential_backoff` is true, and the wait is injectable (a clock) so the tests do not sleep; `RetryPolicyConfig` gets the two fields; `to_config` and `to_skye` write them. Until then `references/router.md` of the skill says they are not applied.
- **`priority` and `cost_per_1k_prompt_tokens` / `cost_per_1k_completion_tokens` on a target.** The old file had them on 3 targets; the router does not read them (they were kept as extra fields), and `.skye` does not carry them. **Decision of the owner: noted for version 2**, to declare as fields only if a strategy reads them. Today `priority_based` selects by success rate, and the `cost_based` strategy is accepted by the language and by `RoutingStrategy` but `RoutingStrategySelector` has no branch for it (it falls through to "first available model"): when it is implemented it needs the cost per 1k tokens of each target (`ModelConfig` in `base/config.py` already has `cost_per_1k_prompt_tokens` and `cost_per_1k_completion_tokens`), and then those two fields become real target fields.
- **Extra fields of a target** (`ModelTarget.extras`) are kept by the Python API but are not exported by `to_config` / `to_skye` and are not accepted by a `target { }` block (the checker reports an unknown field with a suggestion).
