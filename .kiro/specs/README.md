# Specs progression

One spec per component, named like the component (`20-repo.md`). This is the progression view across the 15 components.
Status: **migrated** (Kiro format, cites steering), **legacy** (old format, listed in `LEGACY_SPECS` and to be migrated in place,
sometimes under an old folder name), **requirements only** (the spec has its requirements; design and tasks come next), **missing** (no spec folder yet). The one cross-cutting spec `structure` is not a
component and is listed separately.

| # | Component | Codename | Status | Spec folder |
|---|-----------|----------|--------|-------------|
| 1 | base | stratus | requirements only | `base/` |
| 2 | auth | ozone | requirements only | `auth/` |
| 3 | models | zephyr | migrated | `models/` (was `model-providers`) |
| 4 | store | lake | requirements only | `store/` |
| 5 | router | jet | requirements only | `router/` |
| 6 | tools | updraft | migrated | `tools/` (was `capability-support`) |
| 7 | prompts | cirrus | legacy | `prompts-support/` |
| 8 | memory | dew | requirements only | `memory/` |
| 9 | guard | halo | requirements only | `guard/` |
| 10 | policy | isobar | legacy | `policy-engine/` |
| 11 | observe | radar | requirements only | `observe/` |
| 12 | gateway | horizon | legacy | `gateway/` |
| 13 | agents | cyclone | legacy | `agent-runtime/` |
| 14 | teams | front | requirements only | `teams/` |
| 15 | flows | stream | requirements only | `flows/` |

Cross-cutting (not a component): `structure` — system structure, the docs wiki and the old consolidation work.

Legacy specs: their requirements are migrated to the new format (steering requirements 29 to 48 and pointer criteria); `design.md` and `tasks.md` still hold the old content, and the folders keep the old names (`agent-runtime`, `gateway`, `policy-engine`, `prompts-support`) until they are renamed.

