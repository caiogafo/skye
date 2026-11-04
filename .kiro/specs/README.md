# Specs progression

One spec per component, named `<n>-<layer>-<scope>` (`20-repo.md`, "Canonical names for specs"). This is the progression view across the 15 components.
Status: **migrated** (Kiro format, cites steering), **legacy** (old format, listed in `LEGACY_SPECS` and to be migrated in place,
sometimes under an old folder name), **requirements only** (the spec has its requirements; design and tasks come next), **missing** (no spec folder yet). The one cross-cutting spec `structure` is not a
component and is listed separately.

| # | Component | Codename | Status | Spec folder |
|---|-----------|----------|--------|-------------|
| 1 | base | stratus | requirements only | `0-base-base/` |
| 2 | auth | ozone | migrated | `0-base-auth/` |
| 3 | models | zephyr | migrated | `1-adapters-models/` (was `model-providers`) |
| 4 | store | lake | requirements only | `1-adapters-store/` |
| 5 | router | jet | requirements only | `2-services-router/` |
| 6 | tools | updraft | migrated | `2-services-tools/` (was `capability-support`) |
| 7 | prompts | cirrus | legacy | `prompts-support/` (to be renamed `2-services-prompts/`) |
| 8 | memory | dew | requirements only | `2-services-memory/` |
| 9 | guard | halo | requirements only | `2-services-guard/` |
| 10 | policy | isobar | legacy | `policy-engine/` (to be renamed `2-services-policy/`) |
| 11 | observe | radar | requirements only | `2-services-observe/` |
| 12 | gateway | horizon | legacy | `gateway/` (to be renamed `3-runtime-gateway/`) |
| 13 | agents | cyclone | legacy | `agent-runtime/` (to be renamed `3-runtime-agents/`) |
| 14 | teams | front | requirements only | `3-runtime-teams/` |
| 15 | flows | stream | requirements only | `3-runtime-flows/` |

Cross-cutting (not a component): `0-base-structure` — system structure, the docs wiki and the old consolidation work; `0-base-uxui` — the
public surface a user touches (import paths, names, Port contracts, examples, docstrings; decision D35, was `uxui`).

Legacy specs: their requirements are migrated to the new format (steering requirements 29 to 48 and pointer criteria); `design.md` and `tasks.md` still hold the old content, and the folders keep the old names (`agent-runtime`, `gateway`, `policy-engine`, `prompts-support`) until they are renamed.

