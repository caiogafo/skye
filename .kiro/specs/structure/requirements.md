# Requirements Document

## Introduction

This specification defines the target module and folder structure of the Nimbus library. It is a cross-cutting, structure-only spec: it establishes package boundaries, layer dependency rules, naming rules, codename (watermark) rules, optional-module packaging rules, and the resolution targets for known overlaps. Each requirement is a declaration of target state; code is moved and changed only by the task groups in `tasks.md`, following `design.md`.

The structure is driven by binding product constraints: a serverless-first deployment packaged as a zip-based runtime, a strong size/weight budget enforced by `budgets.toml` and the budget tests, strict modularity with lazy imports, and provider adapters that prefer the standard library over heavy SDKs. Nimbus is at version 0.1.0 with almost no users, so a breaking rename is acceptable when the migration is documented.

This document describes the **current, decided state**. Decisions that replaced earlier ones are listed once in the Decision log at the end; the full history is in git.

### Assumptions (explicitly flagged)

- **Assumption A1 (pydantic vs dataclasses tension):** The structure constraint is that `base` must not require pydantic to import, because core models are planned to move from pydantic to dataclasses. This conflicts with the workspace `python-standards` steering, which mandates Pydantic v2. This spec assumes the structure constraint wins **for structural/boundary purposes only**; the migration is handled in a separate later spec. The tension is recorded here and must not be silently resolved.
- **Assumption A2 (one distribution):** One distribution with extras for now; splitting into multiple distributions is out of scope and revisited later.
- **Assumption A3 (declared-but-minimal packages):** `memory`, `guard`, `observe`, `policy`, `gateway`, `agents`, `teams`, `flows`, and `auth` are declared packages with minimal content in this step (`auth` has an empty `__init__`; its strategies and sources belong to the `auth` and `models` specs). Only `base`, `models`, `store`, `router`, `tools`, and `prompts` receive real structural content now.
- **Assumption A4 (codename theme):** The codename-to-component mapping (cloud/weather words) is given by the owner and treated as fixed input.
- **Assumption A5 (declarations, not execution):** Rename, move, merge, split, and overlap-resolution requirements declare target state; they are executed by the task groups, never implicitly.
- **Assumption A6 (provider rename vertex → google):** The provider formerly named `vertex` is renamed `google`: `models/llm/google_provider.py`, `models/embeddings/google_*.py`, class `GoogleProvider`, registered name `"google"`, extra `google`. The SDK package remains `google-cloud-aiplatform`.

## Glossary

- **Nimbus**: The Python library whose structure this spec defines; also the importable top-level package `nimbus`.
- **Structure_Spec**: This specification and the artifacts it governs (target tree, boundary rules, naming rules).
- **Component**: A named top-level unit of the library (for example `base`, `models`, `store`). Each Component maps to one package folder, one spec folder, and one documentation section that share the same short name.
- **Layer**: A horizontal grouping of Components with a defined import direction. The four Layers are `base`, `adapters`, `services`, and `runtime`.
- **Base_Package**: The `nimbus/base/` package holding models, errors, config, and Ports. It is the `base` Component, in Layer 0.
- **Port**: An interface (abstract contract) defined in `Base_Package`, with no I/O and no dependency on any other Component.
- **Adapter**: A concrete implementation of a Port, living in the `adapters` Layer (`models`, `store`).
- **Decision_Model**: A model kind that returns a constrained choice with calibrated probabilities rather than free text (codenamed "Jev"), implemented in `models` and governed by the `DecisionModel` Port in `Base_Package`.
- **LazyImporter**: The mechanism that defers importing an optional dependency until first use.
- **Extra**: A `pyproject.toml` optional-dependencies group that installs the libraries required by an optional Component.
- **MissingExtraError**: A Nimbus exception raised when code uses an optional Component whose Extra is not installed; it wraps the underlying ImportError and names the missing Extra.
- **Codename**: A single cloud/weather word (at most 7 letters) assigned to each Component as a watermark; never used as an identifier in code, imports, config, logs, or spec folders.
- **Budget_Tests**: The tests under `tests/budget` and the GitHub "budgets" workflow that enforce `budgets.toml`.
- **Allowed_Imports_Matrix**: The declared, testable set of permitted import directions between Layers and Components, enforced by `tests/budget/test_import_matrix.py` (`LAYER` and `ALLOWED`).
- **Overlap**: A place in the codebase where two constructs serve the same role and must be unified by the target structure.
- **teams**: The runtime Component that coordinates multiple units (for example agents) toward a shared objective; codenamed "front". The role of a member within a team (for example `supervisor`) is owned by `teams`, distinct from a unit's identity; the member/role model is deferred to the `teams` spec.
- **flows**: The runtime Component that sequences units into steps (shortened from "workflows" for the 7-letter limit); codenamed "stream".
- **Runnable**: The universal composition contract (one input → one output) implemented by model adapters, `agents`, `teams`, `flows` (and optionally `tools`); composition holds units as `Runnable` references, never by importing their modules. Its conceptual codename `vapor` is a documentation-only watermark, not a Component Codename.
- **Authorizer Port**: A `base` Port, implemented by `policy`, that decides whether a principal may perform an action on a resource and returns `permit` or `forbid`; runtime Components receive it by injection.
- **Authentication Port**: A `base` Port (an object that applies authentication to a request by adding headers or signing it), implemented by `auth`.
- **auth (Component)**: The Layer-0 Component for authentication and credentials (strategies, credential sources, token cache); distinct from `base` because it performs I/O and needs `rsa`. Contrast with `policy` (authorization).
- **Interactive login**: An authentication step requiring a person to act at authentication time (browser, device code, multi-factor); `auth` never performs it.
- **MCP Resource (type)**: A type internal to `tools` representing an MCP resource (listed and read by URI, with a MIME type and text or bytes), returned by the MCP client; not a `base` Port.
- **Differential test**: A test that runs identical input through Nimbus's built-in implementation and the official vendor SDK of the same backend and asserts the observable results match within a declared tolerance; it runs only where the SDK is installed (development or CI).
- **Boundary adapter**: The rule that a Component offering both a built-in and an external-library implementation places them behind one Port returning identical Nimbus types, converting external types at a single boundary point.
- **Bring-your-own adapter**: A small user-written implementation satisfying the `Runnable` Port (optionally wrapping a vendor SDK) and passed where a model is expected; the only vendor-SDK path on the runtime path.
- **Skye (planned rename)**: The project's planned new name (import package `skye`, PyPI distribution `skyeai`); see Requirement 19.

## Requirements

### Requirement 1: Component naming rules

**User Story:** As a Nimbus maintainer, I want every component to use one short, plain, shared name, so that a reader knows from the name alone what a folder, spec, package, or documentation section contains.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define each Component with a single name matching `^[a-z]{3,7}$` (3 to 7 lowercase ASCII letters; no digits, spaces, hyphens, or underscores).
2. THE Structure_Spec SHALL use one identical name string for a Component's package folder, spec folder, module package, `budgets.toml` entry, and documentation section heading.
3. THE Structure_Spec SHALL define the Component set as exactly these 15 names and no others: base, auth, models, store, router, tools, prompts, memory, guard, policy, observe, gateway, agents, teams, flows.
4. THE Structure_Spec SHALL define the cross-cutting spec set as exactly these 3 names and no others: structure, wiki, budgets.
5. WHERE a name is used at class or function level, THE Structure_Spec SHALL allow descriptive identifiers (for example ModelRouter, CapabilityRegistry) while keeping Component folder names constrained to `^[a-z]{3,7}$`.
6. IF a proposed Component name exceeds 7 letters, has fewer than 3 letters, contains a character outside a-z, OR matches an existing Component or cross-cutting spec name, THEN THE Structure_Spec SHALL reject it, keep the existing set unchanged, and record a conflict entry naming the rejected name and the violated rule.

### Requirement 2: Layer dependency rules (allowed-import direction)

**User Story:** As a Nimbus maintainer, I want strict, one-directional dependencies between layers, so that a base model never depends on a higher-level concern and the architecture stays testable.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define exactly four Layers with ordinals: base=0, adapters=1, services=2, runtime=3.
2. THE Structure_Spec SHALL assign Components to Layers as: Layer 0 = {base, auth}; Layer 1 = {models, store}; Layer 2 = {router, tools, prompts, memory, guard, observe, policy}; Layer 3 = {gateway, agents, teams, flows}.
3. THE Structure_Spec SHALL require that a Component in Layer N import only from Components in Layers with ordinal strictly less than N, with the single exception that every Component MAY import `base`. No horizontal (same-Layer) import between two non-`base` Components is permitted; when a Component needs to consume another Component of its Layer, the contract SHALL be a Port in `base` and the consumer SHALL depend on that Port. The only same-Layer imports are Layer-0 Components importing `base` (`auth → base`). `base` never imports another Component.
4. THE Base_Package SHALL import only the Python standard library and SHALL perform no file-system, network, or process I/O, with one explicit exception: `base/http.py` stays inside `base` as the single standard-library-only HTTP transport (using only `urllib`/`http.client`), shared by `auth` and the adapters. This rule applies to the `base` Component, not to all of Layer 0: `auth` performs I/O (metadata and token endpoints, credential files, possibly a subprocess) and needs the pure-Python package `rsa`.
5. THE Structure_Spec SHALL set these Component-level allowed imports (the Allowed_Imports_Matrix; every unlisted row follows Layer rule 3):
   - `auth` imports only `base`.
   - `models` and `store` may import `base` and `auth`.
   - `tools` imports `base` and `auth` and NOT `prompts` (see Requirement 15.2).
   - `policy` imports `base` and `models`.
   - `memory` may also import `auth`.
   - `gateway` may import `base`, `tools`, `models`, and `auth`.
   - Runtime Components (`gateway`, `agents`, `teams`, `flows`) never import `policy`, `guard`, `observe`, or `memory` (Requirement 17.3).
6. IF a Component imports from a Component of a higher Layer, or violates the Component-level rows of criterion 5, THEN THE Allowed_Imports_Matrix check SHALL report a violation identifying the importing Component and its Layer and the imported Component and its Layer.
7. THE Structure_Spec SHALL require a deterministic test, using static analysis of the abstract syntax tree in the manner of `tests/budget/test_policy.py`, that enforces the Allowed_Imports_Matrix, gives the same result for the same input, and exits non-zero when a violation is present.
8. THE Structure_Spec SHALL record these known import violations to be removed: `completion.py` imports `capabilities`; `providers` imports `capabilities`; and `interfaces` imports `memory`.

### Requirement 3: Base package contents and ports

**User Story:** As a Nimbus maintainer, I want a real `base` package that holds the models, errors, config, and ports, so that every other component depends on one standard-library-only foundation.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define `base` as a real importable package at `nimbus/base/` containing an `__init__.py`.
2. THE Base_Package SHALL contain: the core models (messages, completion, capability schema), the error hierarchy, configuration loading, and the Ports. The Ports include the guard Port (`interfaces/safety.py`), the observe Port (`interfaces/observer.py`), the memory Port (`interfaces/memory.py`), the authorizer Port (Requirement 17.4), and the authentication Port (Requirement 18.4).
3. THE Base_Package SHALL define each Port as an interface that performs no I/O and contains no import of any other Component.
4. IF any `base` module imports a package outside the Python standard library, THEN THE Structure_Spec SHALL treat this as a violation and reject the Base_Package as non-compliant.
5. THE Structure_Spec SHALL NOT require pydantic as an import dependency of the Base_Package.
6. THE Structure_Spec SHALL record Assumption A1 as an open, unresolved tension whose scope is limited to this spec.

### Requirement 4: Models component and the DecisionModel port

**User Story:** As a Nimbus maintainer, I want `models` to hold adapters for every model API kind — LLMs, embeddings, and decision models — behind ports defined in base, so that the router, gateway, and guard can select models without vendor lock-in.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define `models` as the Component holding adapters for every model API kind: large language models, embedding models, and Decision_Models.
2. THE `models` Component SHALL contain one shared HTTP transport, retry policy, error mapping, and token counter, reused by every adapter; no adapter defines its own.
3. WHEN an adapter's request fails with a transient error, THE `models` Component SHALL retry up to a configurable maximum of 3 retries after the initial request (4 total attempts) before mapping the failure to a Nimbus error.
4. THE Base_Package SHALL define exactly one `DecisionModel` Port whose response returns one choice from a caller-supplied finite set of options together with a probability for each option, each in 0.0–1.0 and summing to 1.0.
5. IF a `DecisionModel` call receives an empty option set, THEN THE `models` Component SHALL reject it with a Nimbus error stating that at least one option is required and SHALL NOT return a choice.
6. THE Structure_Spec SHALL place the Decision_Model implementation (Jev) inside `models` as a third model kind.
7. THE Structure_Spec SHALL record that the `DecisionModel` Port is consumed by `gateway` for tool selection, by `router` for selecting the cheapest capable model, and by `guard` for pre-flight checks.
8. WHERE a provider offers a REST API reachable with the standard library, THE Structure_Spec SHALL prefer a thin standard-library adapter over the provider SDK.

### Requirement 5: Shared store component

**User Story:** As a Nimbus maintainer, I want all external state backends in one shared `store` package consumed through ports, so that durable state is not duplicated inside each service.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define `store` as exactly one shared Component containing the in-memory, file, DynamoDB, and Redis backends, each a distinct module.
2. WHERE a Port for a store backend exists in `base`, services SHALL consume the backend only through that Port and SHALL NOT import the implementation.
3. IF a service needs a store backend with no `base` Port, THEN a Port SHALL be defined in `base` before the backend is consumed.
4. THE Structure_Spec SHALL designate DynamoDB the first-choice durable backend; any durable-state requirement defaults to DynamoDB unless an alternative is explicitly declared.
5. THE Structure_Spec SHALL NOT place a copy of any storage backend inside a service Component; each backend appears exactly once, in `store`.
6. WHERE a backend offers a pure-Python and a compiled driver, THE Structure_Spec SHALL default to the pure-Python driver and permit the compiled one only when explicitly declared.

### Requirement 6: Optional-module packaging and lazy import

**User Story:** As a Nimbus maintainer, I want every optional component bounded by an extra and loaded lazily, so that the core install stays within budget and imports no optional library.

#### Acceptance Criteria

1. THE Structure_Spec SHALL classify each of the 15 Components as exactly one of always-present (core, no Extra) or optional (installed by an Extra), forming a complete partition. `auth` is optional with the `auth` Extra (Requirement 18.9).
2. WHERE a Component is optional, importing its package SHALL NOT import its optional library at module import time; the library SHALL be imported only through the LazyImporter at first use.
3. IF code uses an optional Component whose Extra is not installed, THEN Nimbus SHALL raise `MissingExtraError` wrapping the underlying ImportError and naming the missing Extra.
4. THE Structure_Spec SHALL keep one distribution with Extras (Assumption A2).
5. THE Structure_Spec SHALL limit the `nimbus/__init__.py` re-export set to exactly messages, completion, exceptions, and config, testable against `forbidden_at_import` in `budgets.toml`.
6. THE Structure_Spec SHALL remove from `nimbus/__init__.py` any re-export that would import an optional or provider library.
7. THE Structure_Spec SHALL retain the declared-but-minimal packages of Assumption A3.

### Requirement 7: Clean import of the top-level package

**User Story:** As a Nimbus user deploying to a serverless runtime, I want `import nimbus` to pull in no provider SDK or optional library, so that the deployed package stays small and imports fast.

#### Acceptance Criteria

1. WHEN a fresh interpreter runs `import nimbus` in a core-only install, THE package SHALL NOT import any library in `forbidden_at_import` of `budgets.toml`, even if present in the environment.
2. WHEN a fresh interpreter runs `import nimbus` in a core-only install, THE modules loaded SHALL NOT exceed `max_modules_loaded` (340) and the import time SHALL NOT exceed `max_import_ms` (250 ms), best of 5 runs.
3. THE Structure_Spec SHALL record that `nimbus/capabilities/remote_api.py` currently imports httpx and requests at module level (the `known_leaks` entries) and that both are to move behind the LazyImporter.
4. WHEN a known leak is resolved, its `known_leaks` entry SHALL be deleted; WHILE an entry remains, THE Budget_Tests SHALL emit a non-failing warning naming it.
5. IF `import nimbus` imports a `forbidden_at_import` library that is not an expected `known_leaks` entry, THEN THE Budget_Tests SHALL fail and identify the library.

### Requirement 8: Extras declare exactly the imported libraries

**User Story:** As a Nimbus maintainer, I want each extra to declare exactly the libraries its code imports, so that installs are correct and the budget stays honest.

#### Acceptance Criteria

1. THE Structure_Spec SHALL require that each Extra declare exactly the third-party libraries its Component's code imports: none missing, none unused.
2. THE Structure_Spec SHALL record that the `memory` Extra declares `psycopg2-binary`, which is unused and LGPL-licensed, and is to be removed.
3. THE Structure_Spec SHALL record that `memory` imports `redis.asyncio` and `asyncpg`, that `asyncpg` is undeclared, and that the `memory` Extra is to declare exactly those libraries.
4. THE Structure_Spec SHALL require that Extra declarations follow the dependency preference order in `budgets.toml`: standard library, then libraries in the target serverless runtime, then pure-Python packages, compiled packages last.
5. IF an Extra declares a library its Component does not import OR omits one it does, THEN THE Budget_Tests SHALL report the specific mismatch.

### Requirement 9: Codename watermark rules

**User Story:** As a Nimbus maintainer, I want each component to carry a quiet codename watermark that never leaks into code, so that the theme is present without ever being needed to understand the system.

#### Acceptance Criteria

1. THE Structure_Spec SHALL assign each Component exactly one Codename: base=stratus, auth=ozone, models=zephyr, store=lake, router=jet, tools=updraft, prompts=cirrus, memory=dew, guard=halo, policy=isobar, observe=radar, gateway=horizon, agents=cyclone, teams=front, flows=stream.
2. THE Structure_Spec SHALL require that each Codename match `^[a-z]{3,7}$`, that the mapping contain exactly 15 entries, and that all Codenames be unique.
3. THE Structure_Spec SHALL restrict Codename appearance to exactly four places: the `codename` front-matter field of the Component's spec and docs section; one italic line under each docs section index; the last line of the package `__init__.py` module docstring; and one glossary page in the documentation wiki.
4. THE Structure_Spec SHALL prohibit a Codename from appearing anywhere else, including any import path, folder name, file name, class name, function name, configuration key, log field, or spec folder name.
5. THE Structure_Spec SHALL require a deterministic test asserting pattern, uniqueness, exactly 15 entries, and no Codename in a package name, file name, or import; IF one appears there, THEN the test SHALL fail and identify the Codename and location.
6. THE Structure_Spec SHALL assign `vapor` to the `Runnable` Port and `nimbus` to the whole project as documentation-only watermarks: unique against the 15 Component Codenames, matching `^[a-z]{3,7}$`, not counted among the 15, and never appearing in any import path, folder, file, class, function, configuration key, or spec folder name. `vapor` appears only in documentation (glossary or wiki, and the Port's module docstring). `nimbus` becomes the umbrella watermark after the rename (Requirement 19.6); until then it is the project's name and no codename test applies to it.

### Requirement 10: Overlaps to be resolved by the structure

**User Story:** As a Nimbus maintainer, I want the known duplications recorded as resolution targets, so that the design unifies them.

#### Acceptance Criteria

1. THE Structure_Spec SHALL record the two registries (`interfaces/route_registry.py` and `providers/registry.py`) as one Overlap entry naming both sources and one target location.
2. THE Structure_Spec SHALL record the two storage concepts (`interfaces/storage.py` and `routes/storage_backends.py`) as one Overlap entry with `store` as the unification target.
3. THE Structure_Spec SHALL record the scattered cost, error, and token interfaces-and-implementations as an Overlap entry listing, per concept, its Port placement in `base` and its implementation placement in the responsible Component.
4. THE Structure_Spec SHALL list every Overlap entry with exactly one intended resolution location.
5. THE Structure_Spec SHALL record the planned spec renames as exactly eight mappings: nimbus → base, model-providers → models, capability-support → tools, prompts-support → prompts, policy-engine → policy, agent-runtime → agents, gateway unchanged, nimbus-consolidation folded into structure.

### Requirement 11: Composition abstraction for orchestrators

**User Story:** As a Nimbus maintainer, I want agents, teams, and flows to compose each other through a single abstraction, so that orchestration is uniform and no import cycle is introduced.

#### Acceptance Criteria

1. THE Base_Package SHALL define a single `Runnable` Port declaring one invocation operation that accepts exactly one input and returns exactly one output.
2. THE `agents`, `teams`, and `flows` implementation modules SHALL each declare a type conforming to `Runnable`.
3. THE `models` Component SHALL implement `Runnable` for its model adapters, so a model is usable anywhere a `Runnable` is accepted, including as a `flows` step or a `teams` member.
4. THE `teams` and `flows` modules SHALL reference composed units (models, agents, teams, flows) only as `Runnable` references, SHALL NOT import the `models`, `agents`, `teams`, or `flows` implementation modules, and SHALL NOT import `policy`, `guard`, `observe`, or `memory` (Requirement 17.3); any other import they hold must be a downward import allowed by the Allowed_Imports_Matrix.
5. IF a composition nests a unit within itself, directly or transitively, THEN THE composing unit SHALL detect the cycle with a visited-set of unit identities, SHALL also enforce a hard maximum nesting depth (default 100) as a safety net, SHALL stop traversal at the detection point, and SHALL raise a Nimbus error indicating the cyclic composition.
6. WHEN the AST import test runs, it SHALL report any direct import among the `agents`, `teams`, and `flows` modules as a violation and fail with a non-zero exit status.
7. THE role of a unit within a team (for example `supervisor`) SHALL be owned by `teams`, not defined in `base` or `agents`. `Runnable` SHALL remain a pure input-to-output contract with no notion of role; a `teams` unit associates a role with a member through membership metadata defined in `teams`. A role is distinct from the unit's identity, so the same `Runnable` may hold different roles in different teams. The concrete TeamMember shape, role set, and supervisor routing belong to the future `teams` spec.

### Requirement 12: Single extension point per integration kind

**User Story:** As a Nimbus maintainer, I want every external integration to enter through one extensible point, so that adding an integration never requires edits scattered across the core.

#### Acceptance Criteria

1. THE Structure_Spec SHALL require that each integration kind be added through exactly one extension point (a Port in `base` plus a registry) with the implementation in the owning Component: model provider → `models`; store backend → `store`; tool or capability → `tools`; observability exporter → `observe`; credential provider → `auth` (Requirement 18.10).
2. WHERE a new model provider is added, it SHALL be configuration or a thin dialect within `models`, with no change to any file outside `models`.
3. WHERE a new store backend is added, it SHALL be exactly one new module in `store` implementing the storage Port, with no change outside `store`.
4. WHERE a new tool, capability, or observability exporter is added, it SHALL be registered through the registry of its owning Component (`tools` or `observe`) without modifying any file outside that Component.
5. THE Structure_Spec SHALL require that adding any such integration introduce no import violating the Allowed_Imports_Matrix.
6. IF adding an integration requires modifying a file in `base` or any Component other than the owner, THEN a structural tooling check (CI or the AST import-matrix and boundary tooling) SHALL reject the change automatically with a message naming the out-of-scope Component, and a mandatory merge gate SHALL independently block it even if the primary check fails to flag it.

### Requirement 13: Extras for teams and flows

**User Story:** As a Nimbus maintainer, I want `teams` and `flows` to each have their own extra under the same rules as every other optional component, so that any library they later need is declared exactly and budgeted.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define exactly one Extra named `teams` and one named `flows`, each declared as an optional-dependencies group in `pyproject.toml`, recorded in `budgets.toml`, listed as a row in the design's extras table, listing standard-library imports before third-party ones, and declaring no compiled package.
2. THE Structure_Spec SHALL record that `teams` and `flows` each declare zero third-party libraries at creation, and list both in the `known_empty` set of `budgets.toml`.
3. WHERE `teams` or `flows` later needs a third-party library, the spec introducing it SHALL declare it as an exact match to the import in that Component's code, and the affected Extra SHALL leave `known_empty` in the same change.
4. Installing the `teams` Extra SHALL exclude every library unique to `flows`, and vice versa.
5. Core code SHALL work with neither Extra installed: `import nimbus` never imports `teams` or `flows`, and the clean-import and import-matrix tests pass with neither present.

### Requirement 14: Official SDKs are dev/test-only, used as differential-test oracles

**User Story:** As a Nimbus maintainer, I want the official vendor SDKs installed only in development and CI as validation oracles, never in production, so that I can prove the built-in standard-library implementations are equivalent without shipping any SDK.

#### Acceptance Criteria

1. THE Structure_Spec SHALL declare every official vendor SDK used for validation in a development/test dependency group (for example `[dependency-groups].dev`) and SHALL NOT declare any in `[project.optional-dependencies]` for that purpose, so no production install (`nimbus` or `nimbus[...]`) installs an SDK for validation.
2. THE Structure_Spec SHALL provide differential tests that, for each backend with both a built-in and an official SDK implementation, run the same input through both and assert 100% compatibility on the fields and behaviors Nimbus consumes (not the full SDK surface): structured fields match by field-subset comparison, numeric or timing values match within a declared epsilon, and error mapping matches at the error-category level.
3. THE differential tests SHALL run only where the SDKs are installed (development or CI); the core-only footprint and clean-import tests SHALL run in a separate core-only environment with no SDK, so SDKs present in dev/CI never cause `forbidden_at_import` or clean-import checks to fail.
4. THE Structure_Spec SHALL NOT ship, declare as a runtime dependency, or require any official vendor SDK in a production install. The SDK version validated in dev/test is used only as the differential-test oracle, never as a runtime fallback.
5. WHERE a differential test requires live credentials or network access that are unavailable, it MAY be skipped without failing the suite, while every test whose prerequisites are present still runs.

### Requirement 15: MCP client lives in tools, tri-faceted, built-in and fastmcp behind one Port

**User Story:** As a Nimbus maintainer, I want the MCP client in the `tools` Component returning Nimbus types, with the built-in client and fastmcp interchangeable behind one Port, so that MCP tools/prompts/resources are consumed uniformly and swapping implementations needs no user code change.

#### Acceptance Criteria

1. THE Structure_Spec SHALL place the MCP client inside the `tools` Component; it is not in `gateway`, MCP is not folded into the `gateway` Extra, and no separate MCP Component exists. MCP server-side behavior (Nimbus acting as an MCP server) is out of scope and belongs to `gateway`.
2. THE MCP client SHALL be tri-faceted: tools as Nimbus `Capability` objects (reusing the `tools` capability interfaces, defining no second tool abstraction), prompts as messages, and resources as `Resource` objects. The prompt facet SHALL NOT import the `prompts` Component: it returns the message types defined in `base` (`NimbusMessage`, `UserMessage`, `AssistantMessage` in `base/messages.py`, which `prompts/messages.py` merely re-exports) via the `MCPPrompt` descriptor defined in `tools`. "Reusing the prompt abstraction" means reusing the `PromptBuilderInterface` Port and the message types in `base`. The allowed imports of `tools` are therefore {base, auth}, and `tests/budget/test_import_matrix.py` SHALL report any `tools → prompts` import as a violation.
3. THE `Resource` type SHALL be internal to `tools`; no resource Port is defined in `base` and no Component is introduced for resources. This holds while no other same-Layer Component consumes MCP resources: WHEN `prompts` (as a context source) or `memory` (as a retrieval source) needs MCP resources, a resource Port SHALL be defined in `base` (list and read by URI, returning a MIME type and text or bytes), implemented by the `tools` MCP client and consumed through that Port, and that addition SHALL replace this clause.
4. THE built-in MCP client (a standard-library JSON-RPC-over-HTTP client) and the official `fastmcp` client SHALL implement the same Port and return identical Nimbus types for tools, prompts, and resources, so choosing one needs no change to user code (Requirement 16).
5. ANY official MCP/`fastmcp` protocol type (for example `mcp.types.Tool`, `mcp.types.Prompt`, `mcp.types.Resource`) SHALL be converted to the corresponding Nimbus type at exactly one boundary point within the `tools` MCP client, so no official protocol type is returned from or leaks outside `tools`.
6. THE conversion SHALL cover 100 percent of the fields and behaviors Nimbus consumes (Requirement 14.2), not the full SDK surface.
7. IF the conversion receives an official type whose required fields are absent or malformed, THEN THE boundary SHALL reject it with an error naming the failing type and field, and SHALL NOT return a partially populated Nimbus type.
8. THE implementation choice and the `mcp` Extra are governed by Requirement 21; `tools` SHALL carry no third-party library.

*(Design open question, no task: whether the MCP prompt facet should implement `PromptBuilderInterface` — `render(template_name, variables) -> list[NimbusMessage]` — so the agent has one prompt shape; today `get_prompt` returns the messages directly.)*

### Requirement 16: Built-in vs external-library adapter is a general boundary rule

**User Story:** As a Nimbus maintainer, I want one general rule for any component that offers a built-in implementation and an external-library implementation behind the same Port, so that external libraries are adapted at the boundary without changing user code or leaking their types.

#### Acceptance Criteria

1. WHERE a Component offers both a built-in standard-library implementation and an external-library implementation, both SHALL sit behind the same Port and return identical Nimbus types (same declared return type and Port method signatures), so user code needs zero changes whichever is selected. The property holds only when all sub-properties hold together: same Port, identical Nimbus return types, and no external-library type exposed.
2. THE external-library implementation SHALL convert every external input and output type into a Nimbus type at exactly one boundary point within the owning Component; no symbol, class, or instance from the external library appears in any Port return value, Port parameter, or public API of that Component.
3. IF an external-library type is exposed outside the owning Component, THEN THE Component SHALL be marked non-conformant and the leak SHALL be adapted to a Nimbus type before acceptance.
4. WHERE a Component has a single active implementation (model providers, Requirement 20) no selection occurs; WHERE an explicit choice exists (the MCP client, Requirement 21) it is an explicit code argument; any library used only for validation follows Requirement 14.
5. THE rule governs the `models` Component (standard-library REST adapters, no SDK on the runtime path) and the `tools` MCP client (built-in vs `fastmcp`), and SHALL apply to any future external-library backend for `observe`, `store`, `prompts`, or `agents` without a new Component or a new Port beyond the owner's existing Port.
6. THE `agents` Component SHALL expose its multiple agent types (for example a ReAct agent) through the `agents` registry behind the `Runnable`/agent Port, extensible per Requirement 12; concrete agent types belong to the future `agents` spec.

### Requirement 17: Policy is a service; runtime never imports optional services

**User Story:** As a Nimbus maintainer, I want `policy` treated as a decision service alongside `guard`, and the runtime components to receive optional services only through base Ports, so that no runtime component requires an optional service to be installed.

#### Acceptance Criteria

1. THE Structure_Spec SHALL place `policy` in the services Layer (Layer 2) alongside `guard`, with allowed imports exactly {base, models}; the full Layer assignment is Requirement 2.2.
2. THE runtime Components (`gateway`, `agents`, `teams`, `flows`) SHALL have allowed-import sets that exclude `policy`, `guard`, `observe`, and `memory`.
3. THE four optional services SHALL be supplied to runtime Components only through Ports defined in `base`, by injection or hooks. `base` provides the guard Port (`interfaces/safety.py`), the observe Port (`interfaces/observer.py`), the memory Port (`interfaces/memory.py`), and the authorizer Port.
4. THE Base_Package SHALL define an authorizer Port that accepts a principal identifier, an action identifier, and a resource identifier and returns exactly one of {permit, forbid}; `policy` implements it.
5. WHEN an authorizer Port is provided to the `gateway`, every capability listing and every capability call SHALL be checked by it; WHEN none is provided, the behavior is deferred to the `gateway` spec.
6. `tests/budget/test_import_matrix.py` SHALL have its `LAYER` and `ALLOWED` data place `policy` in the services Layer and remove `policy`, `guard`, `observe`, and `memory` from the `gateway`, `agents`, `teams`, and `flows` rows.
7. IF any runtime package imports `policy`, `guard`, `observe`, or `memory`, THEN the import-matrix test SHALL fail and report the offending runtime package and imported service.

### Requirement 18: Auth component (authentication and credentials)

**User Story:** As a Nimbus maintainer, I want a dedicated `auth` component in the foundation layer that provides authentication strategies and credential sources behind a base Port, so that every component authenticates outbound requests the same way without `base` doing I/O.

#### Acceptance Criteria

1. THE Structure_Spec SHALL define `auth` as the fifteenth Component, in Layer 0 next to `base`, separate from it.
2. THE allowed imports of `auth` SHALL be `base` only; `auth` serves `models`, `store`, `tools`, `gateway`, and `memory` (Requirement 2.5).
3. THE no-I/O and standard-library-only rules apply to `base`, not to `auth` (Requirement 2.4).
4. THE authentication Port SHALL be defined in `base`; the implementations are supplied by `auth`.
5. THE `auth` package, the spec folder `.kiro/specs/auth`, the documentation section, and the `budgets.toml` entry SHALL share the single name `auth` (Requirement 1.2); its Codename is `ozone` (Requirement 9.1).
6. THE `auth` Component SHALL contain: the authentication strategies (API key and bearer, SigV4, OAuth2); the credential sources (environment, files, container credentials, instance metadata, token exchange services, metadata server); and a token cache.
7. THE credential sources SHALL include native support for the principal cloud secret managers (AWS Secrets Manager, AWS SSM Parameter Store, Azure Key Vault, Google Secret Manager) as built-in sources; such a source calls over `base/http.py`, authenticated with the `auth` strategies.
8. THE SigV4 signer currently at `models/transport/sigv4.py` SHALL move into `auth`.
9. THE Structure_Spec SHALL declare an `auth` Extra whose only third-party library is `rsa` (own budget in `budgets.toml`), and the `google` Extra SHALL declare only the provider SDK, not `rsa`.
10. THE `auth` Component SHALL support only the documented, non-deprecated, non-interactive authentication modes of each provider at a stated date, SHALL never run an interactive login, and SHALL define an extensible credential-source Port through which user code registers its own credential provider (secret-manager or custom).
11. WHERE an authentication mode depends on an interactive login done earlier with a vendor command-line tool (for example AWS IAM Identity Center SSO, `az login`, `gcloud auth login`, application-default-credentials login), `auth` SHALL only read the cache the tool wrote, without prompting; IF the cache is missing or expired, THEN it SHALL raise a clear error telling the user to log in again with the tool.
12. THE design SHALL verify against each provider's current documentation at least these non-interactive modes: serverless execution role (environment variables, container-credentials endpoint, instance metadata IMDSv2); AWS assume-role including cross-account via signed STS; web identity (OIDC token from a file); Bedrock API keys; Google service-account files (RS256 with `rsa`), service-account impersonation, metadata server, authorized-user refresh token, Workload Identity Federation, and API key or access token from the environment; Microsoft Entra ID for Azure OpenAI through managed identity, client secret, certificate (RSA with `rsa`), federated token file, and API key; and API key or bearer for OpenAI-compatible providers, Anthropic, and Cohere.
13. OUT OF SCOPE for `auth`: on-premises Active Directory (Kerberos, NTLM, ADFS), SAML, hardware security modules (PKCS#11), and signing with non-RSA keys.
14. `tests/budget/test_import_matrix.py` and the codename test (15 entries) SHALL reflect `auth`. Implementing the strategies and sources belongs to the `auth` and `models` specs, not to this structure phase.

### Requirement 19: Planned project rename Nimbus to Skye (documented, executed last)

**User Story:** As the Nimbus owner, I want the planned rename of the project to Skye recorded in the spec and scheduled as the final step, so that the migration is agreed and documented before any code or spec text is renamed.

#### Acceptance Criteria

1. THE Structure_Spec SHALL record that the project is renamed from Nimbus to Skye: import package `skye`, PyPI distribution `skyeai` (`skye` belongs to an unrelated package and `skyai` is taken).
2. THE rename SHALL be executed last as its own task group, never implicitly before.
3. THE rename SHALL be a mechanical substitution covering: `src/nimbus` → `src/skye` and every import; the classes `NimbusMessage`, `NimbusError`, `NimbusConfig`, and any other `Nimbus*` name → `Skye*`; exactly the three environment variables of Requirement 23.3 → `SKYE_*`; `nimbus.yaml` → `skye.yaml`; the project name in `pyproject.toml` → `skyeai`; and the corresponding occurrences in `budgets.toml`, CI, CODEOWNERS, the Makefile, the specs, the steering, the wiki, the examples, and the README.
4. THE GitHub repository rename SHALL be performed by the owner (the platform redirects the old address) and is not part of the automated rename.
5. THE rename group's non-coding first task SHALL gate it: all previous task groups closed, the owner has checked the trademark of "Skye" in software, and the owner has reserved `skyeai` (and `skye-ai`) on PyPI.
6. THE definition of done SHALL be: `make budget-fast`, `make budget`, `make differential`, and the guardrail tests give the same results as before the rename, with the codename test adapted to the new names. After the rename, `nimbus` becomes the project-wide umbrella watermark (documentation-only, one of the two watermarks of Requirement 9.6).

### Requirement 20: One implementation per model provider (no selection machinery)

**User Story:** As a Nimbus maintainer, I want each model provider to have exactly one implementation at a time, so that there is no selection machinery, no version negotiation, and no SDK on the runtime path.

#### Acceptance Criteria

1. THE Structure_Spec SHALL require that each model provider have exactly one active implementation: Nimbus's built-in standard-library implementation. No vendor SDK is on the runtime path.
2. THERE SHALL be no selection environment variable (for example `NIMBUS_IMPL`, `NIMBUS_<BACKEND>_IMPL`), no `impl` block in the configuration file, no global default implementation, no SDK version table, no version warning, no fallback to an SDK when an import fails, and no automatic discovery of an installed SDK.
3. WHERE a provider's built-in standard-library adapter does not yet exist, the provider SHALL be implemented by the built-in implementation as it lands, never by a vendor SDK as the active runtime implementation.
4. ANY vendor SDK adapter SHALL be either deleted or kept only as a bring-your-own example in the documentation, and never registered as a provider's active runtime implementation.
5. VENDOR SDKs SHALL remain only as development/test dependencies and as the differential tests of Requirement 14, never on a runtime path.
6. THE selection machinery SHALL be removed in a later task: `base/backend_select.py`, `base/sdk_versions.py`, the `load_impl_config` function and the `impl` handling in `base/config.py`, the `impl_backend` handling and selection in `models/base.py` and the adapters, and `tests/unit/test_backend_select.py`.

### Requirement 21: MCP implementation chosen only by an explicit code argument

**User Story:** As a Nimbus user, I want the MCP client to default to the built-in implementation and to switch to fastmcp only through an explicit code argument, so that there is no environment or configuration machinery for it.

#### Acceptance Criteria

1. THE built-in MCP client SHALL be the default and `fastmcp` an optional substitute chosen only by an explicit code argument, through `create_mcp_client(target, impl="builtin")`.
2. WHEN `impl` is omitted, THE factory SHALL return the built-in client; WHEN `impl="fastmcp"` and `fastmcp` is installed, it SHALL return the `fastmcp` client.
3. IF `impl` is neither `"builtin"` nor `"fastmcp"`, THEN THE factory SHALL raise an error saying the value is not accepted and SHALL NOT return a client.
4. IF `impl="fastmcp"` and `fastmcp` is not installed, THEN THE factory SHALL raise `MissingExtraError` naming the extra `mcp` and SHALL NOT return a client.
5. SELECTION SHALL use no environment variable, no configuration entry, and no fallback; the reading of `NIMBUS_MCP_IMPL` in `tools/mcp_client.py` SHALL be removed in a later task. `import nimbus` imports neither `fastmcp` nor any optional MCP dependency unless explicitly selected.
6. THE `mcp` Extra (providing `fastmcp`, own budget in `budgets.toml`) SHALL be a separate Extra; `tools` carries no third-party library.
7. THE differential tests between the built-in MCP client and the `fastmcp` client SHALL stay as the contract that the two are interchangeable.
8. THE built-in MCP client SHALL be a consume-only client over HTTP transport with no stdio transport and no subprocess, and SHALL never start an MCP server (consistent with the serverless, no-subprocess product constraint). A stdio transport offered by the `fastmcp` substitute is a `fastmcp`-only capability, outside the built-in contract and the differential tests.

### Requirement 22: SDK compatibility is at the data level, with a bring-your-own escape hatch

**User Story:** As a Nimbus user, I want Nimbus to interoperate with vendor SDKs at the level of data shapes rather than classes, so that I can bring my own SDK-backed implementation without configuration.

#### Acceptance Criteria

1. WHEN Nimbus receives messages or tool definitions in the OpenAI data shape, it SHALL accept them and return results as Nimbus types.
2. NIMBUS data shapes SHALL NOT mirror, subclass, or re-export the classes of any vendor SDK client.
3. IF an input does not conform to the OpenAI data shape, THEN Nimbus SHALL reject it with an error indicating the invalid field or shape, retaining the original input unchanged.
4. WHERE a user brings a vendor SDK, they write an adapter satisfying `Runnable` and pass it where a model is expected, with zero configuration entries, zero environment variables, and zero registration steps. This is the only valid vendor-SDK path on the runtime path; any other SHALL NOT be exposed.

### Requirement 23: Environment-variable scope (provider-standard credentials; few Nimbus-prefixed variables)

**User Story:** As a Nimbus user, I want provider credentials to come from each provider's standard environment variables and only a few Nimbus-prefixed variables to remain, so that configuration is predictable and the planned rename has a bounded scope.

#### Acceptance Criteria

1. THE Structure_Spec SHALL require that provider credentials be read from each provider's standard variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and the `AWS_*`, `GOOGLE_*`, `AZURE_*` variables) exclusively through the credential sources of `auth`.
2. THE Structure_Spec SHALL prohibit reading provider credentials from any Nimbus-prefixed variable.
3. THE Nimbus-prefixed environment variables SHALL be exactly three: `NIMBUS_LOG_LEVEL`, `NIMBUS_CONFIG`, `NIMBUS_ENABLE_TELEMETRY`.
4. IF this spec references any other Nimbus-prefixed variable, THEN it SHALL be treated as non-compliant with this requirement.
5. THE bounded set fixes the scope of the rename (Requirement 19): exactly these three are renamed to `SKYE_*`.
6. THE rule of Requirement 16 (no vendor SDK or `mcp`/`fastmcp` type outside its owning Component) remains unchanged.

## Decision log

Decisions that replaced earlier ones (full text in git history before this consolidation):

- **MCP placement:** first in `gateway` and folded into the `gateway` Extra, then moved to `tools` (Requirement 15.1) with a separate `mcp` Extra (Requirement 21.6). The base resource Port was proposed and rejected for now (15.3).
- **Backend selection:** an auto-detect/environment/config mechanism for SDK vs built-in was replaced by one implementation per model provider (Requirement 20) and an explicit `impl` argument for MCP only (Requirement 21).
- **`tools` and `prompts`:** `tools → prompts` was allowed for a while; it is now forbidden (Requirement 15.2).
- **`policy` Layer:** moved from runtime to services (Requirement 17).
- **Component count:** 14 → 15 with `auth` (Requirement 18); codename `ozone`.
- **Runtime imports of optional services:** `teams`/`flows` formerly could import `memory`, `guard`, `observe`, `policy`; now excluded (Requirements 11.4, 17).
- **Scope guard of the first phase** (requirements-only, no design/tasks) was dropped: `design.md` and `tasks.md` now exist.

### Requirement renumbering (old → new)

1–10 unchanged; 11 dropped (scope guard, see above); 12 → 11; 13 → 12; 14 → 13; 15, 16, 17 dropped (superseded, folded into 15, 20, 21); 18 → 14; 19 and 28 → 15; 20 → 16; 21 → 17; 22 → 18; 23 → 19; 24 → 20; 25 → 21; 26 → 22; 27 → 23.
