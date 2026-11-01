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
3. WHEN an adapter issues a request through the shared HTTP transport and the request fails with a transient error, THE models Component SHALL retry the request up to a configurable maximum of 3 attempts before mapping the failure to a Nimbus error.
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
5. IF a composition nests a unit within itself at runtime, whether directly or transitively, THEN THE composing unit SHALL detect the cycle using a visited-set of unit identities or a configurable depth bound with a default maximum nesting depth of 100 levels, SHALL stop traversal at the detection point, and SHALL raise a Nimbus error indicating the cyclic composition without recursing beyond the depth bound.
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
5. IF adding an integration described in this requirement requires modifying any file in the `base` Component or in any Component other than the single owning Component, THEN THE Structure_Spec SHALL require that the integration be rejected with an indication identifying the out-of-scope Component that was modified.
6. WHERE a new tool or capability, or a new observability exporter, is added, THE Structure_Spec SHALL require that it be registered through the registry of its single owning Component (tools or observe respectively) without modifying any file outside that Component.
