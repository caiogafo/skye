Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, Optional services, Extras and budgets)

# Design Document: policy

## Overview
`policy` is the services layer-2 component (codename isobar). It decides whether a principal may perform an action on a resource,
with a small subset of the Cedar model: permit and forbid policies over a principal, an action and a resource, optional `when` and
`unless` conditions, default deny and forbid wins (Requirement 35). It implements the `AuthorizerInterface` Port of `base`
(Requirement 37.1), so the gateway, the agent loop, the router and the memory systems use it by injection and never import it
(Requirement 4.1, D9). It imports only `base` and `models` (`11-design.md`, "Allowed imports"), uses only the standard library and
ships with the core, with no extra (Requirement 38.1; `policy` is listed under "Shipped with the core"). This document describes only
the internals of `policy`; the layer, the allowed imports, the Ports and the extras policy are in the steering sections named above
and are not restated here.

Today `skye.policy` is a placeholder that raises `ImportError("skye.policy is planned, not available yet")` for any name (D40), and
the Port exists in `base` with its `Decision` enum (`permit`, `forbid`). Nothing else exists, so every task below is open.

## Architecture
The engine is a pure function of three inputs: a policy set, an entity provider and a request. Everything that touches the world
(loading, caching, logging, metrics) wraps that function and never enters it, so the same inputs always give the same decision
(Requirement 35.6) and the engine is safe to call from many threads and tasks (the Port is a pure read).

```
policy/
  model.py        Effect, Scope (any / exact / set / membership), Policy, PolicySet (id, version, hash, mode)
  conditions.py   parse and evaluate when/unless conditions (no loops, functions, I/O or regular expressions)
  entities.py     Entity (id, attributes, parents), EntityProvider (caller-supplied), IAM and JWT principal mapping
  engine.py       PolicyEngine: implements AuthorizerInterface; decide() returns the decision with its determining policy ids
  loader.py       PolicySet from JSON and TOML (standard library); the text syntax only once O9 is settled
  schema.py       PolicySchema (entity types, actions, attributes) and the load-time validation
  sources.py      file, environment variable and external-store sources; cache with a time to live
  audit.py        one structured log line per decision; allow, deny and error counters through the observer Port
```

### Evaluation (Requirement 35)
A request is `(principal, action, resource, context)`. A policy matches when its scope matches and its `when` is true and its
`unless` is not true. The decision is `forbid` when any forbid policy matches, else `permit` when at least one permit policy matches,
else `forbid` (default deny). The result carries the identifiers of the policies that determined it (35.5). A condition that cannot
be evaluated (a missing attribute, a type error) makes that one policy not match and records the error (35.7); it never raises into
the caller. Evaluation is bounded by the size of the policy set: the condition grammar has no recursion except nesting that the
parser limits, and a membership test walks the entity hierarchy with a visited set (35.10).

The conditions support comparison, `and`/`or`/`not`, set membership, attribute presence, string prefix and suffix, and membership in
an entity hierarchy (35.8). They are parsed with a small hand-written parser or with `ast` and never evaluated with `eval` or `exec`
(the rule of D55 for expressions). Assumption: the expression checker of `skye.base.dsl` is reused if it can express exactly this
set without regular expressions or function calls beyond it; otherwise `conditions.py` carries its own. Task 2.3 settles it by a
test that feeds both the same cases.

### Entities and principals (Requirement 36.1 to 36.3)
The caller supplies an `EntityProvider` (identifier in, attributes and parents out). An unknown entity has no attributes and no
parents (36.3). A principal comes from an IAM identity or from JWT claims through a mapping function the caller can replace (36.2).
Whether there is one fixed mapping or each application defines its own is open decision O10; the default shipped is the function
that takes a verified identity string unchanged, and the mapping hook is the replaceable part.

### Representation and validation (Requirement 36.4 to 36.9)
Policies load from JSON and TOML with `json` and `tomllib` (36.4), and a policy set exports back to the representation it came from
without changing its meaning (36.7); a round-trip test guards it. The Cedar-like text syntax (36.5) waits for open decision O9: the
design reserves `loader.py` for it and writes nothing about the grammar. A policy error is reported with the policy identifier and
the position of the problem, and all errors of a set are reported together (36.6), as the `.skye` loader does.

Validation checks the policies against a `PolicySchema` of entity types, actions and attributes (36.8). The schema is data given to
the engine: a tool is an action, and the list of tools comes from the capability registry, which the caller (or the gateway) turns
into a `PolicySchema`. `policy` never imports `gateway` or `tools`. A policy that names an unknown action or attribute rejects the
whole set at load time (36.9).

### Integration (Requirement 37.1 to 37.3)
`PolicyEngine.authorize(principal, action, resource)` is the Port call. Requirement 37.1 says the Port also takes a context, while
Requirement 4.2 and the Port in `base` today take three identifiers only. The engine therefore offers
`decide(principal, action, resource, context)` as its own method, which the Port call forwards to with an empty context, and the
Port is left as it is. Whether the Port gains an optional `context` argument is a change to Requirement 4.2 first (steering before
spec); it is listed under "Open points" and is not decided here.

Modes are set per policy set: `enforce` returns the decision; `log_only` returns `permit` and records the decision it would have made
(37.3). The gateway, router, agent and memory callers are other components and are not in this spec; their tasks cite this one.

### Policy sets, sources and cache (Requirement 37.4 to 37.6)
A source gives the text of a set: a file, an environment variable, or an external store. The external store is reached through the
`storage` Port of `base` when the caller passes one, and DynamoDB through `boto3` imported lazily when the caller names it (37.4);
the choice between the two is an assumption to confirm with the owner when task 5.1 starts. The loaded set is cached with a time to
live and refreshed inside the request that notices the expiry, with no background thread (37.5, `00-rules` serverless rules). Each
set has a version and a content hash (the SHA-256 of its canonical form) that go into every decision log (37.6). Nothing is kept
between invocations except what the warm container holds; the cache is a convenience, never state.

### Audit and metrics (Requirement 37.7, 37.8)
One JSON log line per decision with principal, action, resource, decision, determining policy ids, policy set version, hash and
latency; the context values are left out unless a setting enables them (37.7). Counters for allow, deny and error go through the
`observer` Port of `base` (`record_metric`), so `policy` does not import `observe` (37.8; D9). With no observer configured the
counters are skipped.

## Data Models
Dataclasses, frozen where they are values (D24): `Policy`, `Scope`, `PolicySet`, `Entity`, `PolicySchema`, `DecisionRecord`
(decision, determining policy ids, errors, set version, hash, latency). The `Decision` enum is the one in `base`.

## Error Handling
Errors use the `SkyeError` hierarchy with context (`raise ... from e`). A malformed policy set raises a validation error listing every
problem with policy id and position, at load time only. An evaluation error is not raised: the policy is skipped and the error is
recorded in the `DecisionRecord` and the log (35.7). A malformed identifier given to `authorize` raises, as the Port footer says; an
unknown principal, action or resource is `forbid`.

## Testing Strategy
Unit tests in `tests/unit/policy/` cover: each scope form, default deny, forbid over permit, the determining ids, a condition that
cannot be evaluated, every allowed condition operator and the forbidden ones (loops, functions, regular expressions rejected),
unknown entities, JSON and TOML loading and the export round-trip, validation errors with position, log-only mode, cache expiry
refreshed in the request, the version and hash in the log line, and that no log line holds context values by default. The
conformance cases (Requirement 38.5) use requests and expected decisions written from the Cedar documentation; whether an official
suite exists and under which licence is open decision O9, so until then the cases are written by hand and each cites the page it
comes from. The import-matrix test already guards that `policy` imports only `base` and `models`, and the budget tests guard import
time and the standard-library-only rule.

## Correctness Properties
1. With no policy, every request is `forbid` (35.4).
2. If any matching policy is a forbid, the decision is `forbid` whatever the permits (35.4).
3. The same policy set, entities and request give the same decision and the same determining ids (35.6).
4. Adding a policy that does not match a request never changes its decision (35.4, 35.6).
5. A condition error makes only that policy not match; the other policies still decide (35.7).
6. Loading a set and exporting it gives a set that loads to the same decisions (36.7).
7. A set that names an unknown action or attribute is rejected as a whole (36.9).
8. In `log_only` mode the returned decision is `permit` and the recorded decision is the enforce decision (37.3).

## Open points (not decided here)
- **O9** the text syntax in the first release, how much of the Cedar grammar, the compatibility promised and the conformance suite: affects tasks 3.6 and 7.4.
- **O10** principal mapping from IAM and JWT, cache lifetime, evaluation time limit and the budget values: affects tasks 3.2, 5.2 and 7.2.
- Whether the authorizer Port gains a `context` argument (Requirement 4.2 and 37.1 differ): a steering change comes first.
- Whether the external store goes through the `storage` Port or `boto3` directly: confirmed when task 5.1 starts.
