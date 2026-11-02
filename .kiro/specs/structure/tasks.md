# Implementation Plan: structure

## Overview

This plan executes the target module and folder structure defined in `design.md`, governed by the testable requirements in `requirements.md` (the source of truth). It is a **structure-only migration**: it moves and renames packages and declares boundaries. It introduces **no behavior change** — every code-moving step is a pure structural move.

### Overall ordering principle (read this first)

- **Every task leaves the test suite green and the budgets green.** Run `make budget-fast` locally after each task; `make budget` green is part of the definition of done.
- **Guardrail tests come first.** The AST import-matrix test, the codename test, and the extras/footprint tests are written before any move, so the target structure is enforced from the first step. The three known import violations (`completion` → `capabilities`, `providers` → `capabilities`, `interfaces` → `memory`) are marked known-failing (xfail) until the moves remove them.
- **Moves use `git mv` plus TEMPORARY re-exports.** Each code-moving task is: `git mv` the files to the new location → add a temporary re-export shim at the old import path → update references → run tests and budgets. A later task (Group 10) removes every shim once all call sites use the new paths. Nothing breaks mid-migration.
- **No behavior change.** A move never edits logic; it only changes where code lives and how it is imported. Where a split is required (e.g. `providers/base.py`), the split preserves behavior and only separates responsibilities into new modules.
- **No source change in a non-coding sense.** Every task below is a concrete coding step (write a test, `git mv`, add a shim, update imports, adjust `budgets.toml`). There are no research, deployment, or manual-testing tasks.

## Tasks

- [x] 1. Guardrail tests first (enforce the structure before any move)
  - [x] 1.1 Write the AST import-matrix test
    - Create a deterministic test modeled on `tests/budget/test_policy.py` that parses every module under `src/nimbus` with the `ast` module and resolves each import to its owning Component and Layer.
    - Encode the 4 Layers (`base=0`, `adapters=1`, `services=2`, `runtime=3`) and the per-Component `Allowed_Imports_Matrix` from the design.
    - Enforce the three conditions: (i) no upward import (Layer ceiling), (ii) no out-of-set import — including that `teams`/`flows` must NOT import `models`, (iii) no orchestrator cross-import among `agents`/`teams`/`flows`.
    - On violation, report the importing Component+Layer and the imported Component+Layer, and exit non-zero.
    - Mark the three known violations (`completion` → `capabilities`, `providers` → `capabilities`, `interfaces` → `memory`) as known-failing/xfail; they are expected to fail until the moves remove them.
    - _Requirements: 2.3, 2.5, 2.6, 2.7, 12.3, 12.6, 12.8, 12.9_

  - [x] 1.2 Write the codename test
    - Create a deterministic test asserting the 14 Component Codenames each match `^[a-z]{3,7}$`, are unique, number exactly 14, and never appear in any package name, file name, or import.
    - Check the `Runnable` conceptual codename `vapor` separately: it matches `^[a-z]{3,7}$` and is unique with respect to the 14, and is NOT counted in the "exactly 14 entries" invariant.
    - On violation, report the offending Codename and location and fail.
    - _Requirements: 9.2, 9.3, 9.6, 9.7, 9.8, 9.9_

  - [x] 1.3 Write the extras-declare-exactly test and the clean-import/footprint test
    - Write the extras-declare-exactly test: compare each Extra's declared libraries against the third-party libraries its Component's code imports, reusing the `[imports.max_files]` machinery in `budgets.toml`; report any missing or unused declaration.
    - Write the clean-import/footprint test modeled on `tests/budget/test_footprint_budget.py`: a fresh `import nimbus` imports nothing in `forbidden_at_import`, stays within `max_modules_loaded` and `max_import_ms`, and tracks `known_leaks`/`known_import_failures`.
    - _Requirements: 7.1, 7.2, 7.3, 7.6, 8.1, 8.6_

- [x] 2. Create the base package foundation
  - [x] 2.1 Create the `base` package and move core models
    - Create `nimbus/base/__init__.py`.
    - `git mv` `messages.py`, `completion.py`, `exceptions.py`, `config.py` into `nimbus/base/`.
    - Add temporary re-export shims at the old top-level paths so existing imports keep working.
    - _Requirements: 3.1, 3.2_

  - [x] 2.2 Move the Ports into `base/interfaces` and add the new Ports
    - `git mv` `interfaces/*` into `nimbus/base/interfaces/` with temporary re-export shims at the old paths.
    - Add `base/interfaces/runnable.py` (the single `Runnable` Port: one input → one output) and `base/interfaces/decision.py` (the `DecisionModel` Port).
    - Keep the memory **Port** in `base/interfaces/memory.py`; the memory implementation stays in the `memory` Component, removing the `interfaces` → `memory` import.
    - _Requirements: 3.2, 3.3, 4.4, 12.1_

  - [x] 2.3 Add the pure capability schema to base
    - Create `nimbus/base/capability_schema.py` as a pure contract (name, description, parameter schema), standard library only.
    - Update `base/completion.py` to reference the base capability schema instead of the `capabilities`/`tools` Component, removing the `completion` → `capabilities` violation.
    - _Requirements: 2.7_

  - [x] 2.4 Move the lazy-import helper into base as a thin wrapper
    - Reduce `providers/lazy_import.py` to a thin `missing_extra` helper in `base` over stdlib `importlib`, raising `MissingExtraError` (a `NimbusError` subclass) that wraps the underlying `ImportError`/`ModuleNotFoundError` and names the missing Extra.
    - Keep a temporary re-export at the old path for call sites not yet updated.
    - _Requirements: 6.2, 6.3_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass and `make budget-fast` is green; ask the user if questions arise.

- [x] 4. models component (adapters) with the shared stdlib transport
  - [x] 4.1 Rename `providers` → `models`
    - `git mv` `providers/` to `nimbus/models/` with temporary re-export shims at the old `providers` import paths.
    - _Requirements: 1, 4.1_

  - [x] 4.2 Split the shared transport out of the base adapter
    - Split `providers/base.py` into `models/base.py` plus `models/transport/{http,streaming,sigv4,retry,error_mapping,token_counter,multimodal}.py`.
    - `http.py` uses stdlib `urllib.request` + `json`; `streaming.py` is a stdlib SSE (`text/event-stream`) parser; `sigv4.py` signs with stdlib `hashlib`/`hmac`/`datetime`; `retry.py` keeps the max-3-attempts policy; `error_mapping.py` and `token_counter.py` carry over the existing shared logic.
    - Preserve behavior — this is a responsibility split, not a rewrite.
    - _Requirements: 4.2, 4.3_

  - [x] 4.3 Consolidate the LLM adapters and implement the Runnable port
    - Collapse `openai_provider` + `azure_provider` into `models/llm/openai_compatible.py` (one parametrized adapter keyed by `base_url` + `api_key`).
    - Move `anthropic_provider` → `models/llm/anthropic.py` (Messages API over stdlib REST); move `bedrock_provider` → `models/llm/bedrock.py` (shared SigV4 signer, no boto3 required).
    - Make the model adapters implement the `Runnable` Port so a model is usable anywhere a `Runnable` is accepted.
    - _Requirements: 4.1, 4.8, 12.2, 12.7_

  - [x] 4.4* Stage the Google own-dialect adapter (formerly Vertex)
    - Add a Google adapter as its own dialect under `models/llm/google_provider.py` and `models/embeddings/google_*.py` rather than reusing the OpenAI-compatible path (recorded as an assumption in the design).
    - Rename note: Google renamed Vertex AI to Gemini Enterprise Agent Platform in April 2026, so the provider, the registered name and the extra are now `google` (class `GoogleProvider`; extra `google`). Read every `vertex`/`Vertex` in `requirements.md` and `design.md` as `google`. The SDK package stays `google-cloud-aiplatform`.
    - The module move and rename are already done in the working tree; what remains here is the own-dialect work (REST over the stdlib transport instead of the SDK).
    - _Requirements: 4.1_

  - [x] 4.5 Move remote_api onto the stdlib transport to eliminate the HTTP leak
    - Rewrite the `remote_api` HTTP calls to use the shared stdlib `urllib` transport so the `httpx`/`requests` imports are eliminated at the source (not merely deferred behind a lazy import).
    - Drive the `known_leaks` (`httpx`, `requests`) and `known_import_failures` entries toward empty as the imports disappear.
    - _Requirements: 7.4, 7.5_

  - [x] 4.6 Unify the two registries (Overlap A)
    - Keep the registry **Port** in `base/interfaces/registry.py` (merging `interfaces/route_registry.py`).
    - Place the single implementation in `models/registry.py` (merging `providers/registry.py`), consumed by the router through the base Port.
    - _Requirements: 10.1_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass and `make budget-fast` is green; ask the user if questions arise.

- [x] 6. store component (Overlap B)
  - [x] 6.1 Create the shared `store` Component
    - Create `nimbus/store/` and move `routes/storage_backends.py` into `store/{memory,file,dynamodb,redis}.py`, each backend a distinct module behind the storage Port in `base`.
    - Designate DynamoDB the first-choice durable backend; prefer the pure-Python driver where a backend offers both pure-Python and compiled drivers.
    - Add temporary re-export shims at the old `routes/storage_backends.py` path.
    - _Requirements: 5.1, 5.2, 5.4, 5.5, 5.6, 10.2_

- [x] 7. router / tools / prompts (services)
  - [x] 7.1 Rename `routes` → `router` and merge health tracking
    - `git mv` `routes/` to `nimbus/router/` with temporary re-export shims.
    - Merge `providers/health.py` into `router/health_tracker.py`, since health is consumed by routing.
    - _Requirements: 1, 10_

  - [x] 7.2 Rename `capabilities` → `tools` and split the capability models
    - `git mv` `capabilities/` to `nimbus/tools/` with temporary re-export shims.
    - Split `capability_models.py`/`schema.py` so the pure schema lives in `base/capability_schema.py` and the runtime pieces (registry, handler, decorator, MCP client) stay in `tools`.
    - _Requirements: 1, 2.7_

  - [x] 7.3 Reorganize the prompts Component
    - Reorganize `prompts/` into `loaders.py`, `messages.py`, and `templates/`, reusing the liteprompt design (loaders, role-based messages, registry, truncation) but NOT its Jinja2 engine — recorded as a target direction.
    - _Requirements: 1_

- [x] 8. Declared-but-minimal packages
  - [x] 8.1 Ensure the declared-but-minimal packages exist
    - Ensure `memory`, `guard`, `observe` exist as declared-but-minimal packages (each with `__init__.py`).
    - Create the NEW `policy`, `gateway`, `agents`, `teams`, `flows` packages as declared-but-minimal; `teams` and `flows` are runtime orchestrators whose detailed content belongs to their own specs.
    - _Requirements: 6.7, 2.2_

- [x] 9. Overlap C consolidation (cost, error, token)
  - [x] 9.1 Place the cost/error/token Ports in base and impls in models/transport
    - Keep the `cost_calculator`, `error_handler`, and `token_counter` **Ports** in `base/interfaces/`.
    - Place the implementations in `models/transport/` (cost impl, `error_mapping.py`, `token_counter.py`), each concept in exactly one port location and one implementation location.
    - _Requirements: 10.3_

- [x] 10. Curate the public API
  - [x] 10.1 Reduce `nimbus/__init__.py` to the curated four
    - Reduce the top-level re-export set to exactly `messages`, `completion`, `exceptions`, `config`.
    - Remove any re-export that would cause an optional or provider library to be imported, so `import nimbus` in a core-only install pulls no optional/provider library.
    - _Requirements: 6.5, 6.6, 7.1_

- [x] 11. extras / budgets fixes
  - [x] 11.1 Correct the `memory` Extra and align all Extras
    - Remove `psycopg2-binary` (unused, LGPL) from the `memory` Extra and declare `asyncpg`.
    - Make each Extra declare exactly the libraries its Component's code imports, respecting the dependency preference order (stdlib first, then runtime-present libs, then pure-Python, compiled last).
    - Update `budgets.toml` (`[imports.max_files]`, `known_leaks`, `known_import_failures`) to match the new structure.
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 12. Remove the temporary re-export shims
  - [x] 12.1 Update all call sites to the new paths and delete the shims
    - Update every remaining reference to use the new Component import paths.
    - Delete all temporary re-export shims added during the migration.
    - Remove the xfail marks for the three known violations (`completion` → `capabilities`, `providers` → `capabilities`, `interfaces` → `memory`), now resolved.
    - Ensure the AST import-matrix test, the codename test, the extras-declare-exactly test, and the footprint test are all green.
    - _Requirements: 2.6, 2.7, 6.5, 7.1_

- [x] 13. Final checkpoint - budgets green
  - [x] 13.1 Run the full budget suite
    - Run `make budget-fast` and `make budget`; the whole suite green (all guardrail tests plus budgets) is the definition of done.
    - _Requirements: 2.6, 7.3, 8.6_

- [x] 14. teams/flows extras and MCP client (decided parts only)
  - [x] 14.1 Declare the `teams` and `flows` extras as empty extras
    - Add `[project.optional-dependencies].teams` and `[project.optional-dependencies].flows` to `pyproject.toml`, each with zero third-party libraries, installable as `nimbus[teams]` / `nimbus[flows]`.
    - Add `teams` and `flows` to `[extras_policy].known_empty` in `budgets.toml` (joining agents/guard/prompts).
    - Add `teams` and `flows` rows to the extras table / packaging surface so they are covered by the optional-module packaging rules like every other extra.
    - Verify installing `teams` does not pull `flows` and vice versa; the extras-declare-exactly and known_empty budget tests pass.
    - _Requirements: 14.1, 14.2, 14.4, 14.5, 14.6_
  - [x] 14.2 Confirm core works with neither teams nor flows installed
    - Verify `import nimbus` never imports the `teams` or `flows` implementation modules, and that the clean-import and AST import-matrix tests pass with neither extra present (they are optional exactly like `agents`).
    - _Requirements: 14.7_
  - [x] 14.3 Build the tri-faceted MCP client in `tools` (built-in + fastmcp behind one Port)
    - Implement the MCP client inside the `tools` Component exposing tools, prompts, and resources: return Nimbus `Capability` objects for tools, Nimbus prompt objects reusing the `prompts` prompt type, and a `Resource` type defined internal to `tools` (no base Port, no new Component).
    - Provide a built-in standard-library JSON-RPC-over-HTTP MCP client and a `fastmcp`-backed implementation behind the same Port, returning identical Nimbus types; convert any `mcp.types.*`/`fastmcp` protocol type to the Nimbus type at exactly one boundary point so no protocol type leaks outside `tools`. Cover 100% of the fields/behaviors Nimbus consumes; reject malformed/absent required fields at the boundary with an error naming the type and field.
    - Associate the MCP dependency (`fastmcp` today) with the `tools` Extra: installing `nimbus[tools]` provides MCP and `fastmcp` is the optional full-capability alternative to the built-in client. There is no separate `mcp` extra and MCP is not folded into `gateway` (supersedes the interim gateway decision).
    - Extend the AST import-matrix test: `tools → prompts` is an allowed peer import (for the MCP prompt facet); `gateway → prompts` is not required for MCP. Selection between built-in and fastmcp follows task 15.1 (import-time, env/config).
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10_
  - [x] 14.4 Prototype the standard-library MCP client (future target, optional)
    - Optionally stage a standard-library MCP client (JSON-RPC over stateless HTTP) on top of `models/transport/http.py`, aiming to drive the `mcp` extra toward zero third-party libraries. Optional because it is a future target, not a current requirement; the `fastmcp` extra remains until this lands.
    - _Requirements: 15.4_
  - [x] 14.5 Final budgets checkpoint for the appended work
    - Run `make budget-fast` and `make budget`; the whole suite green (new empty-extra entries plus the MCP decided-scope matrix rule) is the definition of done for this group.
    - _Requirements: 14.1, 15.6_

- [x] 15. Backend selection, dev/test SDK validation, MCP tri-faceted client, boundary adapters
  - [x] 15.1 Implement import-time backend selection via env + config (no user code change)
    - Add a single selection mechanism, per backend, choosing the built-in standard-library implementation or a vendor/external implementation behind the same Port; both expose identical signatures/return types.
    - Read the choice from an environment variable (e.g. `NIMBUS_<BACKEND>_IMPL` = `builtin`|`sdk`) and from the config file (e.g. `nimbus.yaml`), with the environment variable taking precedence and an optional global default; default to `builtin` when unspecified.
    - Decide once at import/construction; use one implementation for the whole life of the instance; no per-call fallback and no runtime switching. A selected SDK's runtime error maps to a Nimbus error and propagates.
    - Emit exactly one import-time warning if the installed SDK version differs from the dev-validated reference version; emit a warning on fallback when a requested SDK fails to import; never import a vendor SDK unless selected.
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 17.9, 17.10_
  - [x] 15.2 Add official SDKs as dev/test-only dependencies and write differential tests
    - Declare official vendor SDKs (and `fastmcp`) in a dev/test dependency group (e.g. `[dependency-groups].dev`), never in `[project.optional-dependencies]` for validation and never as a runtime dependency.
    - Write differential tests that run the same input through the built-in implementation and the SDK implementation and assert equivalence on the subset Nimbus consumes: exact structured fields (field-subset), numeric epsilon for numeric/timing values, error-category-level equivalence; not 1:1 with the full SDK surface.
    - Keep the core-only footprint/clean-import/forbidden_at_import tests in a separate SDK-free environment; ensure SDK presence in dev/CI does not fail them. Allow differential tests needing live credentials/network to skip without failing the suite.
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7_
  - [x] 15.4 Enforce the general built-in-vs-external-library boundary rule
    - Add a test/check asserting no external-library type (provider SDK types, `mcp`/`fastmcp` protocol types) is exposed outside its owning Component — external types are converted to Nimbus types at a single boundary point; both impls sit behind the same Port returning identical Nimbus types.
    - Confirm the rule holds for `models` (REST vs SDK) and `tools` (built-in vs fastmcp); document it as the pattern for future `observe`/`store`/`prompts`/`agents` external backends without new Component/Port.
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_
  - [x] 15.5 Expose agent types via the agents registry behind the Runnable/agent Port
    - Ensure `agents` exposes its agent types (e.g. a ReAct agent) through the agents registry behind the `Runnable`/agent Port, extensible per the extension-point rule; concrete agent-type implementations are deferred to the future `agents` spec (only the registry/boundary is set up here).
    - _Requirements: 20.6, 13.1_
  - [x] 15.6 Final budgets checkpoint for this group
    - Run `make budget-fast` and `make budget`; the full suite green (selection mechanism, differential tests in dev env, MCP client, boundary-leak check) is the definition of done for this group.
    - _Requirements: 17.3, 18.4, 19.8_

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster first pass (for example task 4.4, the Google own-dialect adapter, and task 14.4, the standard-library MCP client prototype).
- Each task references specific requirements for traceability.
- Checkpoints ensure incremental validation; the suite and `make budget-fast` must be green at each one.
- The migration never changes behavior — every code-moving task is `git mv` + a temporary re-export + a reference update; the temporary re-export shims are removed in task 12.1.

## Task Dependency Graph

Execution waves (tasks within a wave are independent and can run in parallel; a wave runs only after all earlier waves complete):

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["2.3", "2.4"] },
    { "id": 4, "tasks": ["4.1", "6.1", "7.3", "8.1"] },
    { "id": 5, "tasks": ["4.2", "7.1", "7.2"] },
    { "id": 6, "tasks": ["4.3", "4.5", "4.6"] },
    { "id": 7, "tasks": ["4.4", "9.1"] },
    { "id": 8, "tasks": ["10.1"] },
    { "id": 9, "tasks": ["11.1"] },
    { "id": 10, "tasks": ["12.1"] },
    { "id": 11, "tasks": ["13.1"] },
    { "id": 12, "tasks": ["14.1", "14.3"] },
    { "id": 13, "tasks": ["14.2", "14.4"] },
    { "id": 14, "tasks": ["14.5"] },
    { "id": 15, "tasks": ["15.1"] },
    { "id": 16, "tasks": ["15.2"] },
    { "id": 17, "tasks": ["15.4", "15.5"] },
    { "id": 18, "tasks": ["15.6"] }
  ]
}
```

The same ordering as a diagram:

```mermaid
graph TD
    subgraph guardrails["Guardrail tests (first)"]
        T11["1.1 AST import-matrix test"]
        T12["1.2 codename test"]
        T13["1.3 extras + footprint tests"]
    end
    subgraph base["base foundation"]
        T21["2.1 create base + move core models"]
        T22["2.2 move Ports + add runnable/decision"]
        T23["2.3 base capability schema"]
        T24["2.4 lazy-import helper in base"]
    end
    subgraph models["models + store"]
        T41["4.1 rename providers → models"]
        T42["4.2 split shared transport"]
        T43["4.3 consolidate LLM adapters + Runnable"]
        T44["4.4* Google dialect (optional)"]
        T45["4.5 remote_api on stdlib transport"]
        T46["4.6 unify registries (Overlap A)"]
        T61["6.1 create store (Overlap B)"]
    end
    subgraph services["router / tools / prompts"]
        T71["7.1 rename routes → router + health"]
        T72["7.2 rename capabilities → tools + split"]
        T73["7.3 reorganize prompts"]
    end
    subgraph minimal["declared-but-minimal"]
        T81["8.1 memory/guard/observe + policy/gateway/agents/teams/flows"]
    end
    T91["9.1 Overlap C: cost/error/token"]
    T101["10.1 curate public API"]
    T111["11.1 extras / budgets fixes"]
    T121["12.1 remove shims + unxfail"]
    T131["13.1 make budget-fast + make budget"]
    subgraph extrasmcp["teams/flows extras + MCP client (decided)"]
        T141["14.1 declare teams/flows empty extras"]
        T142["14.2 core works without teams/flows"]
        T143["14.3 MCP client decided scope (tools+prompts)"]
        T144["14.4* stdlib MCP client (optional)"]
        T145["14.5 final budgets checkpoint"]
    end
    subgraph selectionmcp["backend selection + SDK validation + MCP tri-faceted + boundary"]
        T151["15.1 import-time backend selection (env + config)"]
        T152["15.2 dev/test SDKs + differential tests"]
        T154["15.4 built-in-vs-external boundary rule"]
        T155["15.5 agents registry behind Runnable/agent Port"]
        T156["15.6 final budgets checkpoint"]
    end

    guardrails --> T21
    T21 --> T22 --> T23 --> T24
    T24 --> T41
    T41 --> T42 --> T43 --> T44
    T43 --> T45
    T42 --> T46
    T24 --> T61
    T41 --> T71
    T41 --> T72
    T24 --> T73
    T24 --> T81
    T46 --> T91
    T42 --> T91
    services --> T101
    models --> T101
    T81 --> T101
    T91 --> T101
    T45 --> T111
    T61 --> T111
    T101 --> T121
    T111 --> T121
    T121 --> T131
    T131 --> T141
    T131 --> T143
    T141 --> T142
    T143 --> T144
    T141 --> T145
    T143 --> T145
    T142 --> T145
    T144 --> T145
    T145 --> T151
    T151 --> T152
    T151 --> T155
    T151 --> T154
    T152 --> T154
    T154 --> T156
    T155 --> T156
```
