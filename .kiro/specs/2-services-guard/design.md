Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, Optional services, DecisionModel, Extras and budgets)

# Design Document: guard

## Overview
`guard` is the services layer-2 component (codename halo). It provides safety filters that check the input and the output of a model
call, and pre-flight checks that may ask a decision model, behind the `SafetyFilterInterface` Port of `base` (Requirement 51.1,
51.2). It imports only `base` and `models` (`11-design.md`, "Allowed imports"; `models` only for the decision model of a pre-flight
check). Runtime components never import it: they receive a filter through the Port, by injection or through the safety hook of the
agent (Requirement 51.3, 4.1; D9). It uses only the standard library, ships with the core and its extra is empty (`known_empty` in
`budgets.toml`). The layer, the allowed imports, the Ports, the decision model and the extras policy are in the steering sections
named above and are not restated here.

## Current state
`skye.guard` is a placeholder: `__all__` is empty and any attribute raises `ImportError("skye.guard is planned, not available yet")`
(D40). The Port exists in `base`: `SafetyFilterInterface` (`validate_input`, `validate_output`, `get_policies`) and `SafetyResult`
(`is_safe`, `violations`, `confidence`, `metadata`). The `DecisionModel` Port exists in `base` and is asynchronous. Nothing else is
built.

## Architecture
```
guard/
  filters.py     built-in filters: SizeLimitFilter, BlocklistFilter, PatternFilter
  chain.py       FilterChain: runs filters in order, merges the results, stops at the first violation when asked
  preflight.py   PreflightCheck: asks a DecisionModel a yes/no question about a request before the model call
  result.py      helpers over SafetyResult (merge, is_blocking)
```
Every filter satisfies `SafetyFilterInterface` by structure, so a user's own class works in a chain with no base class (D37).

### Filters (Requirement 51.1)
A filter takes a string and returns a `SafetyResult`; it never raises for unsafe content, only for a non-string input (Port footer). The
first built-in filters are small and have no model: `SizeLimitFilter` (maximum characters), `BlocklistFilter` (case-insensitive words
and phrases) and `PatternFilter` (named regular expressions from the standard library `re`, with ready patterns for e-mail addresses,
phone numbers and card numbers checked with the Luhn sum). These three are an assumption about what the owner wants first; they are
the smallest set that makes the Port useful and each is replaceable. Detection of hate speech, violence or prompt injection is a
model-based filter and is not in this design: it would be a thin REST adapter to a moderation service or a decision-model filter, added
only when the owner asks.

`FilterChain` applies filters in order to the input or the output and merges the violations. The merged `is_safe` is true only if
every filter says so; the confidence is the lowest of the filters that reported a violation. `get_policies` is the union of the
filters' policies.

### Pre-flight checks (Requirement 51.2)
A pre-flight check asks a `DecisionModel` (`decide(prompt, options)`) a question over the request before the model call, for example
"is this request allowed for this application", with a fixed set of options. It returns a `SafetyResult`: `is_safe` is true when the
chosen option is the allowed one and its probability is at least a threshold the caller sets. The decision model, the options and the
threshold are settings of the caller; the check chooses none of them (the same rule the gateway follows for its selector,
Requirement 46.14). When the decision model is unavailable the check applies the caller's failure mode, fail closed or fail open,
with no default hidden in the code: the constructor requires it. `DecisionModel.decide` is asynchronous, so the pre-flight check has
the async form `avalidate_input` as the real one and a synchronous `validate_input` that runs it.

### Placement in the run
The agent's safety provider calls `validate_input` at the safety operation before the model call and `validate_output` after it
(Requirement 39.5, 41.1). The provider is in `agents`; `guard` only supplies the object. A denied input becomes a deny outcome of the
hook with the violations as the reason.

## Data Models
`SafetyResult` is the one in `base`. Filters and the chain are plain classes with their configuration as constructor arguments; no
filter keeps per-call state (Port footer).

## Error Handling
Unsafe content is a result, never an exception. A malformed filter configuration (a bad regular expression, a negative limit) raises
`ConfigurationError` at construction naming the field. A pre-flight failure follows the configured failure mode and is recorded in the
result metadata. Logging is structured and never contains the content that was checked, only the filter name, the policy names and
the counts.

## Testing Strategy
Tests in `tests/unit/guard/`: each built-in filter on safe and unsafe text, the Luhn check on valid and invalid card numbers, empty
content is safe, the chain order and merge, the lowest confidence rule, a non-string input raises, a user-written filter works in a
chain, the pre-flight check with a fake decision model (allowed, refused, below the threshold, unavailable in each failure mode), and
that no log line contains the checked text. The compliance checker runs every built-in filter through the Port.

## Correctness Properties
1. Empty content is safe for every built-in filter.
2. A chain is safe if and only if every filter is safe, and its violations are the union of theirs.
3. A filter never raises for any string, however unsafe.
4. The same content and configuration give the same result.
5. A pre-flight below its threshold, or with the model unavailable under fail closed, is not safe.
6. Importing `guard` imports no third-party library and no runtime component.

## Open points (not decided here)
- Which filters ship first (the three above are an assumption) and whether a model-based moderation filter is wanted.
- The failure mode of a pre-flight check when the decision model is unavailable: required of the caller in this design.
- Whether `guard` may import `models` at all at module level or only where a pre-flight check is built (the matrix allows it; the design imports it lazily).
