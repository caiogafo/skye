Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, Composition, Optional services, DecisionModel, Extras and budgets)

# Design Document: teams

## Overview
`teams` is the runtime layer-3 component (codename front). It coordinates several units toward a shared objective: a team holds
members, each a `Runnable` with a name, a role and metadata, and a supervisor decides who works next and how work is routed
(Requirement 49.1, 49.3). A team is itself a `Runnable`, so it can be a step of a flow, a member of another team or a tool of an
agent (Requirement 5.1). `teams` owns the concept of a role, a free string that belongs to the team and not to the unit
(Requirement 49.2, 5.2). It imports only `base` (and `prompts` only when enabled); it never imports `models`, `agents`, `flows` or
another orchestrator, nor the four optional services (`11-design.md`, "Allowed imports"; Requirement 4.1, 5.4). It uses the standard
library only and ships with no extra of its own. The layer, the allowed imports, the composition rule, the decision model and the
extras policy are in the steering sections named above and are not restated here.

## Current state
`skye.teams` is a placeholder: `__all__` is empty and any attribute raises `ImportError("skye.teams is planned, not available yet")`
(D40). The `Runnable` Port exists in `base`, and so does the import-matrix check that keeps `teams` away from `models`, `agents` and
`flows`. Nothing else is built, so every task is open. There is no teams example, and the docs page `docs/teams/index.md` is one line.

## Architecture
```
teams/
  member.py        TeamMember: name, role, runnable, metadata
  team.py          Team: members, a supervisor and a strategy; satisfies Runnable
  supervisor.py    SupervisorInterface and the built-in supervisors
  strategies.py    parallel, hand-off and vote
  cycles.py        the visited set and the depth bound
  result.py        TeamResult: the output, the contributions of the members, who ran and in which order
```

### Members and roles (Requirement 49.1, 49.2)
`TeamMember` is a frozen dataclass: a unique `name` inside the team, a `role` (a free string chosen by the team type, never an
enumeration), a `runnable` and `metadata`. The same `Runnable` may appear in two teams with different roles because identity (the
name and the object) and role (what it does in this team) are separate fields. Members are resolved from objects the caller passes;
`teams` never looks a unit up by import. A name that is not unique, or a member that is not a `Runnable` (checked with
`isinstance`, the Port is a runtime-checkable Protocol), is a validation error naming the field.

### Supervisor (Requirement 49.3)
A supervisor answers one question: given the objective, the state so far and the members, who works next, with which input, or is
the team done. It is an interface (`SupervisorInterface`, an abstract base with `next_step`) so users write their own; it has an
asynchronous form as the real one. Two supervisors ship: a **fixed order** supervisor (members in the order given, then done) and a
**decision** supervisor that asks a decision model received as a `Runnable` (the Port exists; `teams` does not import `models`) to
choose the next member from the finite set of names. The decision supervisor takes the model, the prompt text and a threshold as
settings of the caller; it picks none of them and, when the model is unavailable, applies the failure mode the caller chose
(a required argument, as in `guard`). The prompt may be built with `prompts` when that component is enabled, passed in as a callable,
never imported.

### Strategies (Requirement 49.4)
- **Parallel**: every selected member receives the same input and runs at once with `asyncio.TaskGroup`; the result gathers the
  outputs in member order. A failing member follows a setting: cancel the others, or continue and record the failure.
- **Hand-off**: the members run one after another; the output of one is the input of the next, and the supervisor may skip or
  repeat a member. A bound on the number of hand-offs is required (default documented), to stop a loop.
- **Vote**: every selected member answers the same input in parallel and a rule chooses the result: the most frequent output
  (`majority`) or a function the caller passes. A tie follows a setting (first in member order, or an error). Votes compare outputs
  by equality after an optional normalizing function.
Each strategy is a small class with one method, so a user can add one; a strategy name is a string that selects a built-in.

### Cycles (Requirement 49.5, 5.3)
A team that holds itself, directly or through members that are teams, is detected with a visited set and a depth bound (default 100):
the check runs when a team is built and again when it runs, since a member's contents can change. It raises an error naming the path.
The bound also applies to nesting with `flows` and `agents` that hold a team, since they pass through the same `Runnable` calls: the
visited set is carried in a context variable of `contextvars`, so it works without any of the three importing the others.

### Result and errors
`Team.invoke(input)` returns the final output (a `TeamResult` converts to it) and `TeamResult` records which member ran, in which
order, with which output and error. A member exception follows the strategy setting; an error that stops the team keeps the member
name and the cause (`raise ... from e`).

### Serverless
No state outlives a call: the team keeps no memory of earlier runs. Nothing runs in the background and no process is started.
Anything a team must remember between calls is the memory of a member, reached through that member.

## Data Models
Dataclasses and plain classes only (D24): `TeamMember`, `TeamResult`, `MemberRun` (name, role, output, error, duration). Supervisors
and strategies are plain classes with their settings as constructor arguments.

## Error Handling
Configuration errors (a duplicate name, an unknown strategy, an empty team) raise `ConfigurationError` at construction naming the
field. Run errors keep the member name. The default for a failing member in a parallel run is to cancel the others (the same default
as `flows`, D56); a user can choose to continue.

## Testing Strategy
Tests in `tests/unit/teams/` use fake `Runnable`s: member validation, the same `Runnable` with two roles, the fixed supervisor, the
decision supervisor with a fake decision model (a choice, an unknown name, the model unavailable under each failure mode), each
strategy (order of the outputs, cancellation, continue, hand-off bound, vote with a tie), a team inside a team, a team that contains
itself directly and transitively, the depth bound, and a team as the step of a `Flow` object built in the test. The import-matrix
test already guards that `teams` imports only `base`; a test checks that `teams` does not import `models`, `agents` or `flows`. The
budget tests keep the import time small.

## Correctness Properties
1. A team with members passes the `Runnable` compliance check.
2. Parallel outputs are in member order, whatever order the members finish in.
3. A hand-off never runs more members than its bound.
4. A vote returns an output produced by at least one member, and the same votes give the same result.
5. A team that contains itself, directly or transitively, raises an error naming the cycle.
6. The role of a member does not change the identity of its `Runnable`; the same object can hold two roles in two teams.
7. `teams` imports nothing outside `base`.

## Open points (not decided here)
- The names `TeamMember`, `Team` and `SupervisorInterface` and the built-in supervisors are the design's proposal; Requirement 49 fixes only `TeamMember`.
- The default bound on hand-offs and the tie rule of a vote.
- Whether the decision supervisor's model is a `DecisionModel` Port (asynchronous `decide`) or any `Runnable` that returns a choice; Requirement 49.3 says "a decision model received as a `Runnable`".
- A `.skye` block for teams: the language has `router`, `flow` and `prompt` only (D50); a `team` block would be a language change and is not proposed here.
