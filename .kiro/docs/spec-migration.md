# Spec migration notes

Nothing here is a source of truth: requirements and high-level design live in `.kiro/steering/10-requirements.md`
and `11-design.md`, decisions in `12-decisions.md`, tasks in the spec of each component. Files are kept as history.

## `skye-structure` (formerly `structure`; requirements moved to steering 2026-11-02)
Module and folder structure. Groups 1 to 19 of its tasks are implemented in code and tested. Where each part went:

| Old requirement | Now |
|---|---|
| 1 component names | Requirement 1 |
| 2 layers and allowed imports | Requirement 2; the table is in `11-design.md` |
| 3 `base` | Requirement 3 |
| 4 models, DecisionModel; 14 SDKs as oracles; 16 boundary rule; 20 one implementation per provider; 22 data-level compatibility | Requirement 9 |
| 5 store | Requirement 12 |
| 6 extras and lazy import; 7 clean import; 8 extras match imports; 13 teams and flows extras; 25 budget CI; 26 budget debts | Requirement 7 |
| 9 codenames | Requirement 8 |
| 10 overlaps and spec renames | history; done in code. The spec renames are the migration of the old specs (see below) |
| 11 composition | Requirement 5 |
| 12 extension points | Requirement 6 |
| 15 and 21 MCP client | Requirement 10 |
| 17 policy is a service; runtime never imports optional services | Requirements 2 and 4 |
| 18 auth; 23 environment variables | Requirement 11 |
| 19 project rename | decision D23 and open decisions O1, O2 in `12-decisions.md` |
| 24 licence | Requirement 14 |
| 27 prompts without a compiled engine | Requirement 13 (done: `prompts/engine.py`) |
| design.md | summarized in `11-design.md`; the file-by-file mapping table and the correctness properties stay here as history |

Open tasks at closing: 10.1 and 10.2 (the rename). They are done for the old name and have to be redone for the new one; they are
tracked as open decisions O1 and O2 and in `.kiro/docs/open-items.md`.

## `wiki` (now group 11 of `skye-structure`)
Documentation wiki. Its three tasks are done in the repository (`docs/index.md`, one section per component, `docs/glossary.md`,
routing and provider pages moved). Its rules are Requirement 15 and the "Docs wiki" section of `20-repo.md`. Remaining documentation
work (README reduced to about 150 lines, migration of the loose pages, `docs/budgets.md` into its area, the docs test in `tests/docs`)
is in `.kiro/docs/open-items.md` until the component specs exist; then each item becomes a task in the spec of its component.

## Specs still to migrate
`model-providers` (to `models`), `capability-support` (to `tools`), `prompts-support` (to `prompts`),
`policy-engine` (to `policy`), `agent-runtime` (to `agents`), (`skye`, `skye-consolidation` and `wiki` are merged into `skye-structure`). Method: `20-repo.md`,
"Creating a new spec" and "Canonical names for specs".
