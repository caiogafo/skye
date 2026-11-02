# Specs progression

One spec per component, named like the component (`20-repo.md`). This is the progression view across the 15 components.
Status: **migrated** (Kiro format, cites steering), **legacy** (old format, listed in `LEGACY_SPECS` and to be migrated in place,
sometimes under an old folder name), **missing** (no spec folder yet). The one cross-cutting spec `structure` is not a
component and is listed separately.

| # | Component | Codename | Status | Spec folder |
|---|-----------|----------|--------|-------------|
| 1 | base | stratus | missing | — |
| 2 | auth | ozone | missing | — |
| 3 | models | zephyr | migrated | `models/` (was `model-providers`) |
| 4 | store | lake | missing | — |
| 5 | router | jet | missing | — |
| 6 | tools | updraft | migrated | `tools/` (was `capability-support`) |
| 7 | prompts | cirrus | legacy | `prompts-support/` |
| 8 | memory | dew | missing | — |
| 9 | guard | halo | missing | — |
| 10 | policy | isobar | legacy | `policy-engine/` |
| 11 | observe | radar | missing | — |
| 12 | gateway | horizon | legacy | `gateway/` |
| 13 | agents | cyclone | legacy | `agent-runtime/` |
| 14 | teams | front | missing | — |
| 15 | flows | stream | missing | — |

Cross-cutting (not a component): `structure` — system structure, the docs wiki and the old consolidation work.

Legacy specs still to migrate: `agent-runtime` (agents), `gateway`, `policy-engine` (policy), `prompts-support` (prompts).

Missing specs to create: `base`, `auth`, `store`, `router`, `memory`, `guard`, `observe`, `teams`, `flows`.
