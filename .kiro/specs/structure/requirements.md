# Requirements Document

## Introduction

This specification defines the target module and folder structure of the Nimbus library. It is a cross-cutting, structure-only spec: it establishes package boundaries, layer dependency rules, naming rules, codename (watermark) rules, optional-module packaging rules, and the resolution targets for known overlaps. It does NOT move code and does NOT change any source in this phase; those actions belong to later phases and to the design and tasks documents.

The structure is driven by binding product constraints: a serverless-first deployment packaged as a zip-based runtime, a strong size/weight budget enforced by `budgets.toml` and the budget tests, strict modularity with lazy imports, and provider adapters that prefer the standard library over heavy SDKs. Nimbus is at version 0.1.0 with almost no users, so a breaking rename is acceptable when the migration is documented.

### Assumptions (explicitly flagged)

- **Assumption A1 (pydantic vs dataclasses tension):** Product constraint 6 requires that the structure NOT depend on pydantic, because core models are planned to move from pydantic to dataclasses in a later step. This conflicts with the workspace `python-standards` steering, which mandates Pydantic v2 for data structures. This spec assumes the structure constraint wins **for structural/boundary purposes only** (the `base` package must not require pydantic to import), and that the pydantic-to-dataclasses migration is handled in a separate later spec. This tension is recorded here and must not be silently resolved.
- **Assumption A2 (one distribution):** Based on owner-confirmed decision 3, this spec assumes one distribution with extras for now; splitting into multiple distributions is explicitly out of scope and revisited later.
- **Assumption A3 (declared-but-minimal packages):** Based on owner-confirmed decision 4, this spec assumes `memory`, `guard`, `observe`, `policy`, `gateway`, and `agents` remain as declared packages with minimal content in this step; only `base`, `models`, `store`, `router`, `tools`, and `prompts` receive real structural content now.
- **Assumption A4 (codename theme):** The codename-to-component mapping (cloud/weather words) is taken as given by the owner and treated as fixed input, not derived.
- **Assumption A5 (no execution):** All rename, move, merge, split, and overlap-resolution requirements in this document are DECLARATIONS of target state to be executed in later phases; no requirement in this document authorizes changing source code, moving files, or editing other specs during this requirements phase.
- **Assumption A6 (provider rename vertex → google):** The provider formerly named `vertex` is renamed `google` (Google renamed Vertex AI to the Gemini Enterprise Agent Platform in April 2026). Throughout this spec, read every `vertex`/`Vertex` as `google`: `models/llm/google_provider.py`, `models/embeddings/google_*.py`, class `GoogleProvider`, registered name `"google"`, and the extra `google`. The SDK package remains `google-cloud-aiplatform`.

## Glossary

- **Nimbus**: The Python library whose structure this spec defines. Also the importable top-level package `nimbus`.
- **Structure_Spec**: This specification and the artifacts it governs (the target tree, boundary rules, naming rules).
- **Component**: A named top-level unit of the library (for example `base`, `models`, `store`). Each Component maps to one package folder, one spec folder, and one documentation section that share the same short name.
- **Layer**: A horizontal grouping of Components with a defined import direction. The four Layers are `base`, `adapters`, `services`, and `runtime`.
- **Base_Package**: The `nimbus/base/` package holding models, errors, config, and ports. It is the `base` Layer realized as a real package.
- **Port**: An interface (abstract contract) defined in `Base_Package`, with no I/O and no dependency on any Layer below `base`.
- **Adapter**: A concrete implementation of a Port, living in the `adapters` Layer (`models`, `store`).
- **Decision_Model**: A model kind that returns a constrained choice with calibrated probabilities rather than free text (codenamed "Jev"), implemented in `models` and governed by a `DecisionModel` Port in `Base_Package`.
- **LazyImporter**: The existing mechanism that defers importing an optional dependency until first use, so that importing a package does not import optional or provider libraries.
- **Extra**: A `pyproject.toml` optional-dependencies group (for example `[project.optional-dependencies].bedrock`) that installs the libraries required by an optional Component.
- **MissingExtraError**: A custom Nimbus exception in the NimbusError hierarchy, raised when code uses an optional Component whose Extra is not installed; it wraps the underlying ImportError or ModuleNotFoundError and names the missing Extra.
- **Codename**: A single cloud/weather word (at most 7 letters) assigned to each Component as a watermark. A Codename is never used as an identifier anywhere in code, imports, config, logs, or spec folders.
- **Budget_Tests**: The tests under `tests/budget` and the GitHub "budgets" workflow that enforce the limits in `budgets.toml`.
- **Allowed_Imports_Matrix**: The declared, testable set of permitted import directions between Layers and Components.
- **Overlap**: A place in the current codebase where two constructs serve the same role (for example two registries) and must be unified by the target structure.
- **teams**: The runtime Component that coordinates multiple units (for example multiple agents) toward a shared objective; codenamed "front". The role of a member within a team (including a possible `supervisor` role) is a concept owned by `teams`, distinct from a unit's own identity; the detailed member/role model is deferred to the `teams` spec.
- **flows**: The runtime Component that sequences units into a defined order of steps (shortened from "workflows" to satisfy the 7-letter Component-name limit); codenamed "stream".
- **Runnable**: The universal composition contract (one input → one output) implemented by model adapters (`models`), `agents`, `teams`, and `flows` (and optionally `tools`); composition always holds other units as `Runnable` references rather than importing their implementation modules. Its conceptual codename is `vapor`, a documentation-only watermark that is not a Component Codename and is not counted among the 14 Component Codenames.
- **mcp (Extra)**: the optional Extra providing the MCP client dependency (`fastmcp` today); the future target is a standard-library JSON-RPC-over-HTTP client that returns the Extra to zero third-party libraries.
- **MCP resource Port (hypothesis)**: a proposed small `base` Port to list and read a resource by URI (MIME type + text or bytes), implemented by the MCP client and consumed by `prompts` and `memory`; not decided — recorded as an open question.
- **Backend selection (auto-detect with explicit preference)**: the rule that Nimbus defaults to its built-in standard-library implementation and uses a vendor SDK only when the SDK is installed and explicitly requested via configuration or the registry; a missing or out-of-range SDK falls back to the built-in implementation with a warning, and an unselected SDK is never imported.
- **Differential test**: a test that runs identical input through Nimbus's built-in standard-library implementation and the official vendor SDK implementation of the same backend and asserts their observable results match within a declared tolerance; it runs only where the SDK is installed (development or CI), never in the core-only budget environment.
- **MCP Resource (type)**: a type internal to the `tools` Component representing an MCP resource (listed and read by URI, with a MIME type and text or bytes), returned by the MCP client; it is not a `base` Port and introduces no new Component.
- **Boundary adapter (built-in vs external library)**: the general rule that a Component offering both a built-in and an external-library implementation places them behind one Port returning identical Nimbus types, converting the external library's types to Nimbus types at a single boundary point so those types never leak outside the Component.

## Requirements

### Requirement 1: Component naming rules

**User Story:** As a Nimbus maintainer, I want every component to use one short, plain, shared name, so that a reader knows from the name alone what a folder, spec, package, or documentation section contains.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define each Component with a single name that is between 3 and 7 lowercase ASCII letters (a-z) inclusive, contains no digits, spaces, hyphens, or underscores, and matches the pattern ^[a-z]{3,7}$.
2. THE Structure_Spec SHALL use a single identical Component name string for that Component's package folder, its spec folder, its module package, and its documentation section heading.
3. THE Structure_Spec SHALL define the Component set as exactly these 14 names and no others: base, models, store, router, tools, prompts, memory, guard, policy, observe, gateway, agents, teams, flows.
4. THE Structure_Spec SHALL define the cross-cutting spec set as exactly these 3 names and no others: structure, wiki, budgets.
5. WHERE a Component name is used at the class or function level, THE Structure_Spec SHALL allow descriptive identifiers (for example ModelRouter, CapabilityRegistry) while keeping the Component folder name constrained to the pattern ^[a-z]{3,7}$.
6. IF a proposed Component name exceeds 7 letters, contains fewer than 3 letters, contains any character outside a-z, OR exactly matches an existing name already present in the Component set or the cross-cutting spec set, THEN THE Structure_Spec SHALL reject that name, retain the existing name set unchanged, and record a conflict entry identifying the rejected name and the violated rule.

### Requirement 2: Layer dependency rules (allowed-import direction)

**User Story:** As a Nimbus maintainer, I want strict, one-directional dependencies between layers, so that a base model never depends on a higher-level concern and the architecture stays testable.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define exactly four Layers and SHALL assign each Layer an ordinal from most foundational to most dependent: base=0, adapters=1, services=2, runtime=3.
2. THE Structure_Spec SHALL assign Components to Layers as: base Layer = {base}; adapters Layer = {models, store}; services Layer = {router, tools, prompts, memory, guard, observe}; runtime Layer = {policy, gateway, agents, teams, flows}.
3. THE Structure_Spec SHALL require that a Component in the Layer with ordinal N import only from Components in a Layer with ordinal less than or equal to N.
4. THE Base_Package SHALL import only the Python standard library and SHALL perform no file-system, network, or process I/O.
5. IF a Component in a Layer with ordinal N imports from a Component in a Layer with ordinal greater than N, THEN THE Allowed_Imports_Matrix check SHALL report the import as a violation and SHALL identify the importing Component and its Layer and the imported Component and its Layer.
6. THE Structure_Spec SHALL require a deterministic test, implemented with static analysis of the abstract syntax tree in the manner of `tests/budget/test_policy.py`, that enforces the Allowed_Imports_Matrix, produces the same result for the same input, and exits with a non-zero status when a violation is present.
7. THE Structure_Spec SHALL record the following known import violations to be removed by the target structure: `completion.py` imports `capabilities`; `providers` imports `capabilities`; and `interfaces` imports `memory`.

### Requirement 3: Base package contents and ports

**User Story:** As a Nimbus maintainer, I want a real `base` package that holds the models, errors, config, and ports, so that every other component depends on one standard-library-only foundation.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define `base` as a real importable package located at `nimbus/base/` containing an `__init__.py`, not only a conceptual layer.
2. THE Base_Package SHALL contain all four of the following module groups: the core models (messages, completion, capability schema), the error hierarchy, configuration loading, and the Ports (interfaces).
3. THE Base_Package SHALL define each Port as an interface that performs no I/O operations (no network, filesystem, or database access) and contains no import statement referencing the adapters, services, or runtime Layers.
4. IF any module in the Base_Package declares an import of a package outside the Python standard library other than the Ports contract, THEN THE Structure_Spec SHALL treat this as a violation and reject the Base_Package as non-compliant.
5. THE Structure_Spec SHALL NOT require pydantic as an import dependency of the Base_Package.
6. THE Structure_Spec SHALL record Assumption A1 (the pydantic-versus-dataclasses tension with the python-standards steering) as an entry explicitly labeled as an open, unresolved tension whose scope is limited to this spec.

### Requirement 4: Models component and the DecisionModel port

**User Story:** As a Nimbus maintainer, I want `models` to hold adapters for every model API kind — LLMs, embeddings, and decision models — behind ports defined in base, so that the router, gateway, and guard can select models without vendor lock-in.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define `models` as the Component that holds adapters to every model API kind: large language models, embedding models, and Decision_Models.
2. THE Structure_Spec SHALL place one shared HTTP transport, retry policy, error mapping, and token counting inside the `models` Component such that every adapter reuses the same instances and no adapter defines its own transport, retry policy, error mapping, or token counter.
3. WHEN an adapter issues a request through the shared HTTP transport and the request fails with a transient error, THE models Component SHALL retry the request up to a configurable maximum of 3 retries after the initial request (4 total attempts) before mapping the failure to a Nimbus error.
4. THE Base_Package SHALL define exactly one `DecisionModel` Port whose response returns a single choice selected from a caller-supplied finite set of allowed options together with a probability for each allowed option, where every probability is in the range 0.0 to 1.0 and the probabilities sum to 1.0.
5. IF a `DecisionModel` Port call receives an empty set of allowed options, THEN THE models Component SHALL reject the call with a Nimbus error indicating that at least one option is required and SHALL NOT return a choice.
6. THE Structure_Spec SHALL place the Decision_Model implementation (codenamed Jev) inside `models` as a third model kind alongside large language models and embeddings.
7. THE Structure_Spec SHALL record that the `DecisionModel` Port is consumed by `gateway` for tool selection, by `router` for selecting the cheapest capable model, and by `guard` for pre-flight checks.
8. WHERE a provider offers a REST API reachable with the Python standard library, THE Structure_Spec SHALL prefer a thin standard-library adapter over the provider software development kit.

### Requirement 5: Shared store component

**User Story:** As a Nimbus maintainer, I want all external state backends in one shared `store` package consumed through ports, so that durable state is not duplicated inside each service.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define `store` as exactly one shared Component containing the in-memory, file, DynamoDB, and Redis state backends, with each backend exposed as a distinct module within that single `store` Component.
2. WHERE a Port for a store backend exists in the Base_Package, THE Structure_Spec SHALL require that services consume that backend only through the Base_Package Port and SHALL prohibit services from importing the backend implementation directly.
3. IF a service requires a store backend for which no Base_Package Port exists, THEN THE Structure_Spec SHALL require that a Port be defined in the Base_Package before the backend is consumed, so that no service imports a backend implementation without an intervening Port.
4. THE Structure_Spec SHALL require that DynamoDB be designated the first-choice durable backend, and SHALL require that any durable-state requirement default to DynamoDB unless an alternative backend is explicitly declared.
5. THE Structure_Spec SHALL NOT place a copy or re-implementation of any storage backend inside any service Component, such that each of the in-memory, file, DynamoDB, and Redis backends appears in exactly one location, the shared `store` Component.
6. WHERE a store backend offers both a pure-Python driver and a compiled driver, THE Structure_Spec SHALL require selection of the pure-Python driver as the default, and SHALL permit the compiled driver only when the selection is explicitly declared.

### Requirement 6: Optional-module packaging and lazy import

**User Story:** As a Nimbus maintainer, I want every optional component bounded by an extra and loaded lazily, so that the core install stays within budget and imports no optional library.

#### Acceptance Criteria

1. THE Structure_Spec SHALL classify each of the 14 Components defined in Requirement 1 as exactly one of always-present (installed by the core, no Extra) or optional (installed by an Extra), such that the classification forms a complete partition of the 14-Component set.
2. WHERE a Component is optional, THE Structure_Spec SHALL require that importing that Component's package does not import the Component's optional library at module import time, and SHALL require that the optional library be imported only through the LazyImporter at first use.
3. IF code uses an optional Component whose Extra is not installed, THEN THE Nimbus package SHALL raise a custom Nimbus exception named MissingExtraError that wraps the underlying ImportError or ModuleNotFoundError and identifies the missing Extra by name.
4. THE Structure_Spec SHALL keep one distribution with Extras, consistent with Assumption A2.
5. THE Structure_Spec SHALL limit the `nimbus/__init__.py` re-export set to exactly messages, completion, exceptions, and config, and SHALL require that this set be testable against the `forbidden_at_import` set in `budgets.toml`.
6. THE Structure_Spec SHALL remove from `nimbus/__init__.py` any re-export that would cause an optional or provider library to be imported.
7. THE Structure_Spec SHALL retain `memory`, `guard`, `observe`, `policy`, `gateway`, and `agents` as declared packages with minimal content in this step, consistent with Assumption A3.

### Requirement 7: Clean import of the top-level package

**User Story:** As a Nimbus user deploying to a serverless runtime, I want `import nimbus` to pull in no provider SDK or optional library, so that the deployed package stays small and imports fast.

#### Acceptance Criteria

1. WHEN a fresh interpreter executes `import nimbus` in a core-only install, THE Nimbus package SHALL NOT import any library listed in the `forbidden_at_import` set of `budgets.toml`, which covers provider software development kits and optional-Extra libraries.
2. WHEN a library listed in the `forbidden_at_import` set of `budgets.toml` is present in the environment and a fresh interpreter executes `import nimbus`, THE Nimbus package SHALL NOT import that library as a side effect.
3. WHEN a fresh interpreter executes `import nimbus` in a core-only install, THE number of modules loaded SHALL NOT exceed the `max_modules_loaded` value of 340 recorded in `budgets.toml`, and the import time SHALL NOT exceed the `max_import_ms` value of 250 milliseconds, measured as the best of 5 runs.
4. THE Structure_Spec SHALL record that `nimbus/capabilities/remote_api.py` currently imports httpx and requests at module level as the `known_leaks` entries in `budgets.toml`, and that both imports are to be moved behind the LazyImporter.
5. WHEN a known import leak is resolved, THE Structure_Spec SHALL require that the corresponding entry be deleted from the `known_leaks` list in `budgets.toml`.
6. IF `import nimbus` imports a library listed in the `forbidden_at_import` set of `budgets.toml` that is not an expected `known_leaks` entry, THEN THE Budget_Tests SHALL report a failure and identify the offending library.

### Requirement 8: Extras declare exactly the imported libraries

**User Story:** As a Nimbus maintainer, I want each extra to declare exactly the libraries its code imports, so that installs are correct and the budget stays honest.

#### Acceptance Criteria

1. THE Structure_Spec SHALL require that each Extra declare exactly the set of libraries that the corresponding Component's code imports, with no missing declaration and no unused declaration.
2. THE Structure_Spec SHALL record that the `memory` Extra currently declares psycopg2-binary, that psycopg2-binary is unused and LGPL-licensed, and that it is to be removed.
3. THE Structure_Spec SHALL record that the `memory` Component's code uses `redis.asyncio` and `asyncpg`, that `asyncpg` is currently undeclared, and that `asyncpg` is to be declared by the `memory` Extra.
4. THE Structure_Spec SHALL require that the corrected `memory` Extra declarations match exactly the libraries the `memory` code imports.
5. THE Structure_Spec SHALL require that Extra declarations respect the dependency preference order recorded in `budgets.toml`: standard library first, then libraries already present in the target serverless runtime, then pure-Python packages, and compiled packages last.
6. IF an Extra declares a library the corresponding Component does not import OR omits a library the corresponding Component does import, THEN THE Budget_Tests SHALL report the specific mismatch.

### Requirement 9: Codename watermark rules

**User Story:** As a Nimbus maintainer, I want each component to carry a quiet codename watermark that never leaks into code, so that the theme is present without ever being needed to understand the system.

#### Acceptance Criteria

1. THE Structure_Spec SHALL assign each Component exactly one Codename from the fixed mapping: base=stratus, models=zephyr, store=lake, router=jet, tools=updraft, prompts=cirrus, memory=dew, guard=halo, policy=isobar, observe=radar, gateway=horizon, agents=cyclone, teams=front, flows=stream.
2. THE Structure_Spec SHALL require that each Codename be between 3 and 7 lowercase ASCII letters matching the pattern ^[a-z]{3,7}$.
3. THE Structure_Spec SHALL require that the Codename mapping contain exactly 14 entries, one per Component, and that all Codenames be unique.
4. THE Structure_Spec SHALL restrict Codename appearance to exactly these four places and no others: the `codename` front-matter field of the Component's spec and docs section; one italic line under each docs section index; the last line of the package `__init__.py` module docstring; and one glossary page in the documentation wiki.
5. THE Structure_Spec SHALL prohibit a Codename from appearing anywhere else, including any import path, folder name, file name, class name, function name, configuration key, log field, or spec folder name.
6. THE Structure_Spec SHALL require a deterministic test that verifies every Codename matches the pattern ^[a-z]{3,7}$, that all Codenames are unique, that the mapping contains exactly 14 entries, and that no Codename appears in a package name, a file name, or an import.
7. IF a Codename appears in a package name, a file name, or an import, THEN the deterministic Codename test SHALL report a failure and identify the offending Codename and location.
8. THE Structure_Spec SHALL assign the `Runnable` Port the conceptual Codename `vapor` as a documentation-only watermark, distinct from the 14 Component Codenames; this watermark SHALL appear only in documentation (the glossary or wiki and the Port's module docstring) and SHALL NOT be counted among the 14 Component Codenames nor appear in any import path, folder name, file name, class name, function name, configuration key, or spec folder name.
9. THE Structure_Spec SHALL require that `vapor` be unique with respect to the 14 Component Codenames and match the pattern ^[a-z]{3,7}$.

### Requirement 10: Overlaps to be resolved by the structure

**User Story:** As a Nimbus maintainer, I want the known duplications recorded as resolution targets, so that the design unifies them without this phase executing any change.

#### Acceptance Criteria

1. THE Structure_Spec SHALL record the two registries (`interfaces/route_registry.py` and `providers/registry.py`) as a single Overlap entry that names both source paths and the one target structure location into which they are to be unified.
2. THE Structure_Spec SHALL record the two storage concepts (`interfaces/storage.py` and `routes/storage_backends.py`) as a single Overlap entry that names both source paths and identifies the `store` Component as the one unification target.
3. THE Structure_Spec SHALL record the scattered cost, error, and token interfaces-and-implementations as an Overlap entry that lists, for each of the three concepts, its interface placement in `base` as a Port and its implementation placement in the responsible Component.
4. THE Structure_Spec SHALL list every Overlap entry with exactly one intended resolution location per entry, and each entry SHALL be expressed as a recorded target only.
5. IF any Overlap entry or planned spec rename references code, THEN THE Structure_Spec SHALL record it as a future action and SHALL NOT move, edit, delete, or rewrite any existing code or spec in this phase.
6. THE Structure_Spec SHALL record the planned spec renames as the exact set of eight mappings (nimbus to base, model-providers to models, capability-support to tools, prompts-support to prompts, policy-engine to policy, agent-runtime to agents, gateway unchanged, and nimbus-consolidation folded into structure), with each mapping stated as a future action.

### Requirement 11: Scope guard for this phase

**User Story:** As the Nimbus owner, I want this phase to produce requirements only, so that no code or other spec is changed before design is agreed.

#### Acceptance Criteria

1. THE Structure_Spec SHALL confine all output of this phase to a single file at `.kiro/specs/structure/requirements.md`.
2. WHEN an operation in this phase would otherwise create, modify, or delete a file whose path matches `src/nimbus` (including any subpath), THE Structure_Spec SHALL NOT perform that operation and SHALL record the blocked path as an out-of-scope item; THE Structure_Spec SHALL NOT be required to record paths for operations that were never attempted.
3. IF any operation in this phase would delete, rewrite, or overwrite an existing file under `.kiro/specs` other than `.kiro/specs/structure/requirements.md`, THEN THE Structure_Spec SHALL NOT perform that operation and SHALL record the protected path as an out-of-scope item.
4. THE Structure_Spec SHALL NOT create `.kiro/specs/structure/design.md` or `.kiro/specs/structure/tasks.md` in this phase.
5. THE Structure_Spec SHALL express every boundary, naming, codename, packaging, and overlap-resolution item as a declaration of target state, each stated as a single testable condition to be executed in a later phase.
6. WHERE an item is not grounded in an explicit source statement, THE Structure_Spec SHALL label that item as an assumption consistent with Assumption A5, and SHALL leave every source-grounded item unlabeled.

### Requirement 12: Composition abstraction for orchestrators

**User Story:** As a Nimbus maintainer, I want agents, teams, and flows to compose each other through a single abstraction, so that orchestration is uniform and no import cycle is introduced.

#### Acceptance Criteria

1. THE Base_Package SHALL define a single `Runnable` Port that declares one invocation operation accepting exactly one input argument and returning exactly one output value.
2. THE Structure_Spec SHALL require that the `agents`, `teams`, and `flows` implementation modules each declare a type that conforms to the `Runnable` Port invocation operation.
3. THE Structure_Spec SHALL require that the `teams` and `flows` implementation modules reference composed units only through the `Runnable` Port type defined in `base` and SHALL NOT contain any import statement targeting the `agents`, `teams`, or `flows` implementation modules.
4. WHEN a `teams` or `flows` unit composes another unit, THE composing unit SHALL hold the composed unit as a `Runnable` Port reference such that no import edge is created between orchestrator implementation modules.
5. IF a composition nests a unit within itself at runtime, whether directly or transitively, THEN THE composing unit SHALL detect the cycle using a visited-set of unit identities for correctness AND SHALL also enforce a hard maximum nesting depth with a default of 100 levels as a safety net, SHALL stop traversal at the detection point reached either by the visited-set or by reaching the depth cap, and SHALL raise a Nimbus error indicating the cyclic composition without recursing beyond the depth bound.
6. WHEN the deterministic abstract-syntax-tree import test runs, THE Structure_Spec SHALL require that test to report any direct import among the `agents`, `teams`, and `flows` implementation modules as a violation and SHALL require the test to fail with a non-zero exit status when at least one such violation is detected.
7. THE Structure_Spec SHALL require that the `models` Component implement the `Runnable` Port for its model adapters, so that a model adapter is usable anywhere a `Runnable` is accepted, including as a step in a `flows` unit or a member of a `teams` unit.
8. WHEN a `teams` or `flows` unit uses a model, an agent, a team, or a flow as a composed unit, THE composing unit SHALL reference that unit through the `Runnable` Port and SHALL NOT import the `models`, `agents`, `teams`, or `flows` implementation modules.
9. THE Structure_Spec SHALL require that the `teams` and `flows` implementation modules import at most the `base` Component plus their optional feature consumers (`prompts`, `memory`, `guard`, `observe`, `policy`), and SHALL NOT import the `models`, `agents`, `teams`, or `flows` implementation modules.
10. THE Structure_Spec SHALL require that the concept of a unit's role within a team (for example a `supervisor` role) be owned by the `teams` Component and SHALL NOT be defined in the `base` Component or the `agents` Component.
11. THE Structure_Spec SHALL require that the `Runnable` Port remain a pure input-to-output contract with no notion of team role, such that a `teams` unit associates a role with a composed unit through membership metadata defined in `teams` rather than through the `Runnable` Port.
12. THE Structure_Spec SHALL record that a unit's role within a team is distinct from the unit's own identity, so that the same `Runnable` may hold different roles in different teams; this is a boundary-level statement only, and the concrete TeamMember shape, the role set, and supervisor routing logic are out of scope for this spec and belong to the future `teams` spec.

### Requirement 13: Single extension point per integration kind

**User Story:** As a Nimbus maintainer, I want every external integration to enter through one extensible point, so that adding an integration never requires edits scattered across the core.

#### Acceptance Criteria

1. THE Structure_Spec SHALL require that each integration kind (model provider, store backend, tool or capability, observability exporter) be added through exactly one extension point consisting of a Port defined in `base` plus a registry, with the concrete implementation placed in the owning Component (models, store, tools, observe respectively).
2. WHERE a new model provider is added, THE Structure_Spec SHALL require that the provider be added as configuration or a thin dialect within `models` without modifying any file outside the `models` Component, consistent with provider-agnosticism.
3. WHERE a new store backend is added, THE Structure_Spec SHALL require that the backend be exactly one new module in the `store` Component that implements the storage Port, with no modification to any file outside the `store` Component.
4. THE Structure_Spec SHALL require that adding any integration described in this requirement introduce no import that violates the Allowed_Imports_Matrix.
5. IF adding an integration described in this requirement requires modifying any file in the `base` Component or in any Component other than the single owning Component, THEN THE Structure_Spec SHALL require that the integration be rejected automatically by a structural tooling check (in continuous integration or the abstract-syntax-tree import-matrix and boundary tooling) that scans the modified files against the owning Component's scope and blocks the change with an automated message identifying the out-of-scope Component that was modified, without relying on manual review.
6. WHERE a new tool or capability, or a new observability exporter, is added, THE Structure_Spec SHALL require that it be registered through the registry of its single owning Component (tools or observe respectively) without modifying any file outside that Component.
### Requirement 14: Extras for teams and flows

**User Story:** As a Nimbus maintainer, I want `teams` and `flows` to each have their own extra under the same rules as every other optional component, so that any library they later need is declared exactly and budgeted.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define exactly one Extra named `teams` and exactly one Extra named `flows`, each governed by the same rules as every other Extra: it declares exactly the set of third-party libraries that its code imports with no library omitted and no library included that the code does not import, it lists standard library imports before third-party imports, it declares no compiled package (no package requiring a build step or distributing platform-specific binaries), and it is recorded as an entry in `budgets.toml`.
2. THE Structure_Spec SHALL record that `teams` and `flows` each declare zero third-party libraries at creation, and SHALL list both `teams` and `flows` as entries in the `known_empty` set of `budgets.toml`.
3. WHERE `teams` or `flows` later requires one or more third-party libraries, THE Structure_Spec SHALL require that each such library be declared by the spec that introduces it as an exact match to the import present in that component's code, and that the affected Extra be removed from the `known_empty` set of `budgets.toml` in the same change.
4. IF an attempt is made to install the `teams` Extra, THEN THE Structure_Spec SHALL require that the resolved dependency set exclude every library unique to the `flows` Extra.
5. IF an attempt is made to install the `flows` Extra, THEN THE Structure_Spec SHALL require that the resolved dependency set exclude every library unique to the `teams` Extra.
6. THE Structure_Spec SHALL require that the `teams` Extra and the `flows` Extra each be declared as an optional-dependencies group in `pyproject.toml`, appear as a row in the design's extras table, and be covered by the optional-module packaging requirements (Requirement 6), consistent with how every other Extra is declared and packaged.
7. THE Structure_Spec SHALL require that core code continue to function with neither the `teams` nor the `flows` Extra installed, such that `import nimbus` never imports the `teams` or `flows` implementation modules and the clean-import and import-matrix tests pass with neither Extra present.

### Requirement 15: MCP is a client only, for tools, resources, and prompts

**User Story:** As a Nimbus maintainer, I want MCP reimplemented as a client only (tools, resources, prompts), with the server side out of scope, so that Nimbus consumes MCP without adding a second prompt abstraction and the gateway remains the only MCP-server concern.

#### Acceptance Criteria

1. THE Structure_Spec SHALL require that the MCP implementation expose client-side capabilities only, covering exactly three MCP concern types (MCP tools, MCP resources, MCP prompts), and SHALL place every MCP server-side concern out of scope for this spec, delegating Nimbus-acts-as-MCP-server behavior to the `gateway` Component.
2. THE Structure_Spec SHALL require that MCP tools reuse the existing capability interfaces defined in the `tools` Component and SHALL NOT define any additional tool or capability interface, base class, or registry outside the `tools` Component.
3. THE Structure_Spec SHALL require that MCP prompts reuse the existing prompt interfaces defined in the `prompts` Component and SHALL NOT define any additional prompt interface, base class, or template abstraction outside the `prompts` Component.
4. THE Structure_Spec SHALL require that MCP remain the Extra named `mcp`, depending on `fastmcp` and retaining its existing entry in `budgets.toml`, and SHALL record as a future target (not a current requirement) a standard-library MCP client using JSON-RPC over stateless HTTP on top of `base`'s HTTP transport that reduces the `mcp` Extra to zero third-party runtime dependencies.
5. THE Structure_Spec SHALL record, as OPEN QUESTIONS explicitly flagged as undecided and to be resolved in the design, exactly two items: (a) where MCP resources live, and (b) whether the MCP client code lives inside the `tools` Component or in its own Component.
6. THE Structure_Spec SHALL add import-matrix rules only for the already-decided placements, namely MCP tools residing in the `tools` Component and MCP prompts reusing the `prompts` Component, and SHALL NOT add any import-matrix rule for the two placements recorded as OPEN QUESTIONS in criterion 5.
7. WHERE the open MCP-resource hypothesis is adopted, THE Structure_Spec SHALL record, as an explicitly-flagged hypothesis and not a decision, a resource Port in `base` that lists resources and reads a resource by URI returning a MIME type and either text or bytes, implemented by the MCP client, consumed by `prompts` as a context source and by `memory` as a retrieval source, introducing no new Component.
8. WHERE the open MCP-resource hypothesis is recorded, THE Structure_Spec SHALL document in the design the comparison of that hypothesis against placing the resource Port in `tools` as a read-only capability and against placing it in `store`, recording `store` as rejected on the stated ground that `store` covers only what the framework writes.
### Requirement 16: MCP client lives in gateway; mcp folded into the gateway extra (SUPERSEDED by Requirement 19)

*This requirement is superseded by Requirement 19 (MCP client lives in `tools`); it is retained for history and its acceptance criteria no longer apply.*

**User Story:** As a Nimbus maintainer, I want the MCP client implemented inside the `gateway` Component reusing the tools and prompts interfaces, so that MCP needs no new Component, no resource Port in base, and installing `gateway` is enough to use MCP.

#### Acceptance Criteria

1. THE Structure_Spec SHALL place the MCP client code inside the `gateway` Component, resolving the open question of client-code location (Requirement 15.5(b)), and SHALL NOT define any separate MCP Component.
2. THE Structure_Spec SHALL implement MCP resources inside the `gateway` Component as a gateway-internal concept, resolving the open question of resource location (Requirement 15.5(a)).
3. THE Structure_Spec SHALL NOT define an MCP-resource Port in the `base` Component and SHALL NOT introduce any new Component for MCP resources, recording that the base-resource-Port hypothesis of Requirement 15.7 is rejected.
4. THE Structure_Spec SHALL require that the `gateway` MCP client implement MCP tools by reusing exactly the capability interfaces defined in the `tools` Component and implement MCP prompts by reusing exactly the prompt interfaces defined in the `prompts` Component, and SHALL NOT define any second tool/capability or prompt abstraction.
5. THE Structure_Spec SHALL extend the Allowed_Imports_Matrix so that the `gateway` Component may import exactly the `base`, `tools`, and `prompts` Components in addition to its existing allowed imports, and SHALL record that these three imports are downward imports that introduce no import cycle.
6. THE Structure_Spec SHALL associate the `fastmcp` dependency with the `gateway` Extra as an optional dependency and SHALL NOT define a separate `mcp` Extra, such that installing `nimbus[gateway]` is sufficient to use MCP.
7. WHERE `fastmcp` is installed, THE gateway SHALL use `fastmcp` in place of the built-in client.
8. WHERE `fastmcp` is not installed, THE gateway SHALL use the built-in standard-library MCP client, and executing `import nimbus` SHALL NOT trigger an import of `fastmcp`.
9. THE Structure_Spec SHALL record that the future target built-in MCP client is a standard-library client using JSON-RPC over stateless HTTP on top of the shared HTTP transport, SHALL require that the built-in path depend on no third-party library, and SHALL record `fastmcp` as the optional full-capability alternative.

### Requirement 17: Interchangeable official SDK vs built-in implementation (auto-detect with explicit preference)

**User Story:** As a Nimbus user, I want to swap Nimbus's built-in standard-library implementation for an official vendor SDK interchangeably, so that I can opt into an SDK when I need it without the SDK ever being imported when I do not.

#### Acceptance Criteria

1. THE Structure_Spec SHALL make each backend (for example a model provider, or the MCP client) selectable between the Nimbus built-in standard-library implementation and an official vendor SDK implementation, chosen via configuration or the registry, with the two implementations interchangeable behind the same Port such that both expose identical Port method signatures and return types.
2. WHILE no SDK backend is explicitly requested via configuration or the registry, THE Nimbus library SHALL use the built-in standard-library implementation.
3. WHEN an SDK backend is explicitly requested via configuration or the registry AND the corresponding vendor SDK is installed, THE Nimbus library SHALL use the vendor SDK implementation.
4. WHILE no SDK backend is explicitly requested, THE Nimbus library SHALL NOT import any vendor SDK, consistent with the `forbidden_at_import` rule in `budgets.toml`.
5. THE Structure_Spec SHALL NOT impose a locked or gating supported version range on a selectable vendor SDK; the library SHALL NOT refuse or block an SDK solely because of its version number.
6. WHEN an SDK backend is explicitly requested, THE Nimbus library SHALL decide once, at import or construction of the backend, which implementation to use: IF the vendor SDK imports successfully THEN the backend instance SHALL use the SDK implementation for the entire life of that instance, ELSE the backend instance SHALL use the built-in standard-library implementation for the entire life of that instance, without raising a fatal error; and WHEN the vendor SDK fails to import and the backend falls back to the built-in standard-library implementation at import or construction, THE Nimbus library SHALL emit one warning or log message identifying the failed SDK import and the fallback to the built-in standard-library implementation.
7. THE Structure_Spec SHALL require that a single backend instance use exactly one implementation (either the SDK or the built-in) for its entire life, and SHALL NOT mix the two implementations across calls on the same instance and SHALL NOT switch implementation at runtime after the initial selection.
8. IF a method of a selected SDK backend raises an error at runtime (for example due to a changed or incompatible SDK API), THEN THE Nimbus library SHALL map that error to a Nimbus error and propagate it to the caller, and SHALL NOT silently fall back to the built-in implementation for that call or reset the instance to the built-in implementation; resolving the incompatibility (installing a compatible SDK version or no longer requesting the SDK) is the user's action and takes effect at the next construction of the backend.
9. THE Structure_Spec SHALL record, for each vendor SDK, the SDK version against which Nimbus was validated in development (an informational reference, not a gate), and WHEN a backend selects the SDK implementation at import AND the installed SDK version differs from that recorded validated version, THE Nimbus library SHALL emit exactly one warning at import time identifying the SDK, the installed version, and the validated version, while still using the installed SDK; WHILE no SDK backend is explicitly requested, no vendor SDK SHALL be imported and no version check SHALL run (consistent with the `forbidden_at_import` rule in `budgets.toml`), and selecting an SDK backend SHALL introduce no import that violates the Allowed_Imports_Matrix while the SDK remains an optional dependency declared by the owning Component's Extra.
10. THE Structure_Spec SHALL require that the choice between the built-in standard-library implementation and the vendor SDK implementation be expressed entirely through configuration or environment and require no change to user application code, since both implementations share the same Port; specifically: the choice SHALL be settable per backend via an environment variable (for example `NIMBUS_<BACKEND>_IMPL` with value `builtin` or `sdk`) and via a key in the configuration file (for example `nimbus.yaml`), with an optional global default; WHEN both an environment variable and a configuration-file value are present for the same backend, THE environment variable SHALL take precedence; and WHILE no selection is specified for a backend, THE Nimbus library SHALL default that backend to the built-in standard-library implementation.

### Requirement 18: Official SDKs are dev/test-only, used as differential-test oracles

**User Story:** As a Nimbus maintainer, I want the official vendor SDKs installed only in development and CI as validation oracles, never in production, so that I can prove the built-in standard-library implementations are equivalent without shipping any SDK.

#### Acceptance Criteria

1. THE Structure_Spec SHALL declare every official vendor SDK used for validation in a development/test dependency group (for example `[dependency-groups].dev`), and SHALL NOT declare any such SDK in `[project.optional-dependencies]` for that validation purpose, so that no production or end-user install (`nimbus` or `nimbus[...]`) installs an SDK for validation.
2. THE Structure_Spec SHALL provide differential tests that, for each backend having both a built-in standard-library implementation and an official SDK implementation, run the same input through both and assert 100% compatibility on the subset of fields and behaviors that Nimbus actually consumes rather than one-to-one equivalence with the full SDK surface, where for that subset the structured fields match exactly by field-subset comparison, each numeric or timing value matches within a declared numeric epsilon, and error mapping matches at the error-category level (an equivalent category, not an exact error type or code), treating the SDK as the oracle only for what Nimbus uses.
3. THE Structure_Spec SHALL require that the differential tests run only in an environment where the official SDKs are installed (development or CI), and SHALL require that the core-only footprint and clean-import tests continue to run in a separate core-only environment where no SDK is installed.
4. WHEN the official SDKs are installed in a development or CI environment, THE presence of those SDKs SHALL NOT cause the `forbidden_at_import` or clean-import checks to fail, because those checks run in the separate core-only environment; `import nimbus` SHALL still import no SDK.
5. THE Structure_Spec SHALL NOT ship, declare as a runtime dependency, or require any official vendor SDK in a production install; the production default remains the built-in standard-library implementation.
6. THE Structure_Spec SHALL record that Requirement 18 (SDKs as dev/test validation oracles, pinned in the dev/test dependency group to the validated version) is independent of Requirement 17 (a user's explicit opt-in to an SDK backend at runtime, selected once at import with one implementation per instance and no runtime switching): the dev/test-validated SDK version is the informational reference that Requirement 17's import-time version-mismatch warning compares the production-installed version against, and a user opt-in under Requirement 17 remains the user's own choice.
7. WHERE a differential test for a backend requires live credentials or network access that are unavailable, THE Structure_Spec SHALL allow that differential test to be skipped without failing the suite, while still running every differential test whose prerequisites are present.

### Requirement 19: MCP client lives in tools, tri-faceted, built-in and fastmcp behind one Port

**User Story:** As a Nimbus maintainer, I want the MCP client in the `tools` Component returning Nimbus types, with the built-in client and fastmcp interchangeable behind one Port, so that MCP tools/prompts/resources are consumed uniformly and swapping implementations needs no user code change.

#### Acceptance Criteria

1. THE Structure_Spec SHALL place the MCP client code inside the `tools` Component, and SHALL record that this supersedes Requirement 16 (which had placed the MCP client in `gateway`): the MCP client is in `tools`, not `gateway`, and MCP is not folded into the `gateway` Extra.
2. THE Structure_Spec SHALL require that the MCP client be tri-faceted, exposing MCP tools, MCP prompts, and MCP resources, such that it returns Nimbus `Capability` objects for tools (the `tools` capability type), Nimbus prompt objects for prompts (the `prompts` prompt type), and `Resource` objects for resources.
3. THE Structure_Spec SHALL define the `Resource` type internal to the `tools` Component, and SHALL NOT define a resource Port in `base` and SHALL NOT introduce a new Component for resources.
4. THE Structure_Spec SHALL require that the built-in MCP client (a standard-library JSON-RPC-over-HTTP client) and the official `fastmcp` client both implement the same Port and both return the identical Nimbus types for tools, prompts, and resources, so that selecting one or the other requires no change to user application code.
5. THE Structure_Spec SHALL require that any official MCP/`fastmcp` protocol type (for example `mcp.types.Tool`, `mcp.types.Prompt`, `mcp.types.Resource`) be converted to the corresponding Nimbus type at exactly one boundary point within the `tools` MCP client, such that no official protocol type is returned from or leaks outside the `tools` Component.
6. THE Structure_Spec SHALL require that the conversion from official MCP/`fastmcp` types to Nimbus types cover 100 percent of the fields and behaviors that Nimbus consumes (consistent with Requirement 18.2), and SHALL NOT require coverage of the full official SDK surface.
7. THE Structure_Spec SHALL associate the MCP client dependency (`fastmcp` today) with the `tools` Extra, such that installing `nimbus[tools]` provides MCP and `fastmcp` is the optional full-capability alternative to the built-in client; this supersedes Requirement 16.6's folding of MCP into the `gateway` Extra.
8. THE Structure_Spec SHALL require that selection between the built-in MCP client and `fastmcp` follow Requirement 17 (import-time selection via configuration or environment, one implementation per instance, no runtime mixing), such that `import nimbus` imports neither the built-in MCP client's optional dependency nor `fastmcp` unless selected.
9. IF the `tools` MCP client receives an official MCP/`fastmcp` protocol type whose fields required by the Nimbus conversion (per criterion 6) are absent or malformed, THEN THE Structure_Spec SHALL require the conversion boundary to reject the input with an error indicating the failing type and field, and SHALL NOT return a partially populated Nimbus type.
10. IF the MCP client implementation selected at import time (per criterion 8) is unavailable because its optional dependency is not installed, THEN THE Structure_Spec SHALL require that `import nimbus` surface an error indicating the missing dependency and the selected implementation, and SHALL NOT silently fall back to the other implementation.

### Requirement 20: Built-in vs external-library adapter is a general boundary rule

**User Story:** As a Nimbus maintainer, I want one general rule for any component that offers a built-in implementation and an external-library implementation behind the same Port, so that external libraries are adapted at the boundary without changing user code or leaking their types.

#### Acceptance Criteria

1. WHERE a Component offers both a built-in standard-library implementation and an implementation backed by an external library, THE Structure_Spec SHALL require both implementations to sit behind the same Port and return values of identical Nimbus types (same declared return type and Port method signatures), such that user application code requires zero source changes regardless of which implementation is selected.
2. THE Structure_Spec SHALL require that the external-library implementation be an adapter that converts every external-library input and output type into a Nimbus type at exactly one boundary point within the owning Component, such that no symbol, class, or instance originating from the external library is exposed in any Port return value, Port parameter, or public API of that Component.
3. IF any external-library type is exposed outside the owning Component through a Port return value, Port parameter, or public API, THEN THE Structure_Spec SHALL mark the Component as non-conformant with this boundary rule and SHALL require the leak to be adapted to a Nimbus type before the Component is accepted.
4. THE Structure_Spec SHALL require that selection between the built-in and external-library implementation follow Requirement 17 (import-time selection via configuration or environment, exactly one implementation per Component instance, no runtime mixing) and Requirement 18 (the external library validated as a dev/test differential-test oracle, not shipped to production).
5. THE Structure_Spec SHALL record that this general rule already governs the `models` Component (standard-library REST adapters versus official provider SDKs, Requirement 17) and the `tools` MCP client (built-in versus `fastmcp`, Requirement 19), and SHALL require that any future external-library backend for `observe`, `store`, `prompts`, or `agents` apply this same rule without introducing a new Component or a new Port beyond the owning Component's existing Port.
6. THE Structure_Spec SHALL require that the `agents` Component expose its multiple agent types (for example a ReAct agent) through the `agents` registry behind the `Runnable`/agent Port, extensible per Requirement 13, while the concrete agent-type implementations are defined in the future `agents` spec and are out of scope for this structure spec.
