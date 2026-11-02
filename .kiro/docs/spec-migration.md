# Spec migration notes

Nothing here is a source of truth: requirements live in `.kiro/steering/10-requirements.md`, high-level design in `11-design.md`, decisions in
`12-decisions.md`, tasks in the spec of each component. This file records where the former specs went. The old texts are in the git history.

## `structure` (formerly the structure spec; its requirements moved to steering)
Module and folder structure. Groups 1 to 19 of its tasks are implemented in code and tested. It now also holds the former `skye` (base contracts),
`skye-consolidation` and `wiki` specs, merged into its three files. Where each old requirement went:

| Old requirement | Now (`10-requirements.md`) |
|---|---|
| 1 component names | Requirement 1 |
| 2 layers and allowed imports | Requirement 2; the table is in `11-design.md` |
| 3 `base` | Requirement 3 |
| 4 models, DecisionModel; 14 SDKs as oracles; 16 boundary rule; 20 one implementation per provider; 22 data-level compatibility | Requirement 9 |
| 5 store | Requirement 12 |
| 6 extras and lazy import; 7 clean import; 8 extras match imports; 13 teams and flows extras; 25 budget CI; 26 budget debts | Requirement 7 |
| 9 codenames | Requirement 8 |
| 10 overlaps and spec renames | history; done in code |
| 11 composition | Requirement 5 |
| 12 extension points | Requirement 6 |
| 15 and 21 MCP client | Requirement 10 |
| 17 policy is a service; runtime never imports optional services | Requirements 2 and 4 |
| 18 auth; 23 environment variables | Requirement 11 |
| 19 project rename | one-off task (group 10 of `structure/tasks.md`), decision D23 and open decisions O1, O2 |
| 24 licence | Requirement 14 |
| 27 prompts without a compiled engine | Requirement 13 (done: `prompts/engine.py`) |
| design.md | summarized in `11-design.md`; the file-by-file mapping and the correctness properties stay in `structure/design.md` as history |

The base-contracts stories (former `skye` spec) became Requirements 16 to 21 (interfaces and the standard response, router configuration, errors and
logging, token usage and cost, configuration, type safety); the consolidation stories became Requirements 17, 20, 22, 23 and 24 (router YAML and
environment substitution, configuration, terminology, tests, examples). Open tasks at closing: the rename (group 10), now redone with the final name.

## `wiki` (now group 11 of `structure/tasks.md`)
Its three tasks are done in the repository (`docs/index.md`, one section per component, `docs/glossary.md`, routing and provider pages moved). Its
rules are Requirement 15 and the "Docs wiki" section of `20-repo.md`. Remaining documentation work (front matter on every page, `docs/budgets.md`,
the docs test in `tests/docs`, the README reduced to about 150 lines) is in group 11 of `structure/tasks.md`.

## The component specs
| Old spec | New spec | Requirements | State |
|---|---|---|---|
| `model-providers` | `models` | Requirement 9 and the new 25 (embeddings), 26 (multimodal inputs), 27 (structured output), 28 (token counting); decisions D24, D25 | migrated by Kiro |
| `capability-support` | `tools` | Requirement 10 and decision D26 (MCP resources) | migrated by Kiro |
| `prompts-support` | `prompts` | new Requirements 29 to 34; decisions D20, D24 | requirements migrated; folder keeps the old name |
| `policy-engine` | `policy` | new Requirements 35 to 38; open decisions O9, O10 | requirements migrated; folder keeps the old name |
| `agent-runtime` | `agents` | new Requirements 39 to 43; open decisions O11, O12, O13 | requirements migrated; folder keeps the old name |
| `gateway` | `gateway` | new Requirements 44 to 48; open decisions O12, O14 to O18 | requirements migrated |

New component specs created at the requirements stage: `base` (Requirements 3, 16, 18 to 21), `auth` (11), `store` (12), `router` (17 and 23.3),
`memory` (52), `guard` (51), `observe` (53), `teams` (49 and 5), `flows` (50 and 5).

Still to do: the design and tasks of the specs that stop at requirements; rename the four folders that keep an old name; migrate their `design.md`
and `tasks.md` (group 12 of `structure/tasks.md`). Method: `20-repo.md`, "Creating a new spec" and "Canonical names for specs".
