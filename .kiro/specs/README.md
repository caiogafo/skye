# Specs progression

One spec per component, named `<n>-<layer>-<scope>` (`20-repo.md`, "Canonical names for specs"). This is the progression view across the 15 components.
Status: **migrated** (Kiro format, cites steering), **legacy** (old format, listed in `LEGACY_SPECS` and to be migrated in place,
sometimes under an old folder name), **requirements only** (the spec has its requirements; design and tasks come next), **missing** (no spec folder yet). The one cross-cutting spec `structure` is not a
component and is listed separately.

| # | Component | Codename | Status | Spec folder |
|---|-----------|----------|--------|-------------|
| 1 | base | stratus | migrated | `0-base-base/` |
| 2 | auth | ozone | migrated | `0-base-auth/` |
| 3 | models | zephyr | migrated | `1-adapters-models/` (was `model-providers`) |
| 4 | store | lake | migrated | `1-adapters-store/` |
| 5 | router | jet | migrated | `2-services-router/` |
| 6 | tools | updraft | migrated | `2-services-tools/` (was `capability-support`) |
| 7 | prompts | cirrus | migrated | `2-services-prompts/` (was `prompts-support`) |
| 8 | memory | dew | migrated | `2-services-memory/` |
| 9 | guard | halo | migrated | `2-services-guard/` |
| 10 | policy | isobar | migrated | `2-services-policy/` (was `policy-engine`) |
| 11 | observe | radar | migrated | `2-services-observe/` |
| 12 | gateway | horizon | requirements only | `3-runtime-gateway/` (was `gateway`; kept while O19 is open) |
| 13 | agents | cyclone | migrated | `3-runtime-agents/` (was `agent-runtime`) |
| 14 | teams | front | migrated | `3-runtime-teams/` |
| 15 | flows | stream | migrated | `3-runtime-flows/` |

Cross-cutting (not a component): `0-base-structure` — system structure, the docs wiki and the old consolidation work; `0-base-uxui` — the
public surface a user touches (import paths, names, Port contracts, examples, docstrings; decision D35, was `uxui`).

No spec is legacy any more: the four old folders (`prompts-support`, `policy-engine`, `agent-runtime`, `gateway`) were renamed with `git mv`, their `requirements.md` carries `codename` and `previous_name`, and `LEGACY_SPECS` in `tests/budget/test_specs_format.py` is empty. Every component spec has requirements, design and tasks except `gateway`, which has its requirements only: its design and tasks wait for open decision O19 (`12-decisions.md`), which asks whether a separate `gateway` stays a component or its work becomes the job of the `tools` registry. Until the owner decides, the spec keeps its place at layer 3 and Requirements 44 to 48 stay as they are. "Migrated" here means the spec files follow the Kiro format and cite steering; most tasks of `policy`, `agents`, `store` (partly), `router` (partly), `memory`, `guard`, `observe`, `teams` and `flows` are still open code work.
