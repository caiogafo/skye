---
inclusion: manual
---

# Requirements Document

## Introduction

The only place where requirements are written. Component specs repeat the user stories they serve and cite the numbers
below as pointers (`THE spec SHALL realize Requirement 9.2 of #[[file:.kiro/steering/10-requirements.md]]`); they do not copy criteria. `Requirement 9.2` means criterion 2 of Requirement 9. A requirement
starts at the heading `### Requirement 9: <title>` (the Kiro syntax), so `grep -n -A25 "^### Requirement 9:" .kiro/steering/10-requirements.md`
returns it whole. Design is in `11-design.md`; decisions, taken and open, are in `12-decisions.md`. To change a requirement, edit it here
and add a line to the decision log.
Written without the project name (it is being chosen); `<pkg>` is the import package. Terms: **Port** is an interface in `base`;
**Extra** is an optional dependency group; **Runnable** is the one-input, one-output Port.

## Requirements

### Requirement 1: Component names

**User Story:** As a maintainer, I want one short plain name per component used everywhere, so that a name tells me what a folder, spec or docs section holds.

#### Acceptance Criteria

1. THE library SHALL have exactly 15 components: base, auth, models, store, router, tools, prompts, memory, guard, policy, observe, gateway, agents, teams, flows.
2. EACH name SHALL match `^[a-z]{3,7}$` and SHALL be the same for the component's package, docs section and `budgets.toml` entry; THE spec folder SHALL carry the layer number of the component in front of the name (`<layer>-<name>`, for example `1-adapters-models`).
3. IF a proposed name breaks the pattern or equals an existing one, THEN THE library SHALL reject it and keep the existing set.
4. WHERE a name is used for a class or a function, THE library SHALL allow a descriptive identifier (for example `ModelRouter`).

### Requirement 2: Layers and imports

**User Story:** As a maintainer, I want one-directional dependencies, so that the architecture stays testable and nothing low-level depends on something high-level.

#### Acceptance Criteria

1. THE layers SHALL be: base (0) = {base, auth}; adapters (1) = {models, store}; services (2) = {router, tools, prompts, memory, guard, observe, policy}; runtime (3) = {gateway, agents, teams, flows}.
2. A component SHALL import only from a strictly lower layer plus `base`, and only the components in its allowed set (`11-design.md`); THE only same-layer import SHALL be `auth` importing `base`, and a same-layer need SHALL be met by a Port in `base`.
3. `tools` SHALL NOT import `prompts`; `policy` SHALL import only `base` and `models`.
4. IF an import breaks these rules, THEN `tests/budget/test_import_matrix.py` SHALL fail and name both components with their layers; THE test SHALL be deterministic (static analysis of the syntax tree) and SHALL exit non-zero on a violation.

### Requirement 3: `base`

**User Story:** As a maintainer, I want `base` to be a small standard-library foundation, so that everything depends on something that installs nothing and does no I/O.

#### Acceptance Criteria

1. THE `base` component SHALL hold the core models, the errors, the configuration loader and every Port, and SHALL import only the standard library.
2. THE `base` component SHALL do no file, network or process I/O, except `base/http.py`, the one standard-library HTTP transport shared by `auth` and the adapters.
3. THE `base` component SHALL NOT need pydantic to import.
4. EACH Port SHALL perform no I/O and SHALL import no other component.
5. IF a `base` module imports a package outside the standard library, THEN THE budget tests SHALL fail.

### Requirement 4: Optional services reach the runtime only through Ports

**User Story:** As a user, I want to run an agent without installing policy, guard, observe or memory, so that the runtime never forces a service on me.

#### Acceptance Criteria

1. THE runtime components SHALL NOT import `policy`, `guard`, `observe` or `memory`; they SHALL receive them through the Ports in `base` (authorizer, safety, observer, memory), by injection or hooks.
2. THE authorizer Port SHALL take a principal, an action and a resource and return exactly `permit` or `forbid`.
3. WHEN an authorizer is provided, THE gateway SHALL check every capability listing and call with it; WHEN none is provided, THE behavior SHALL be the one defined by the gateway spec.
4. IF a runtime package imports `policy`, `guard`, `observe` or `memory`, THEN THE import-matrix test SHALL fail and name the package and the service.

### Requirement 5: Composition

**User Story:** As a maintainer, I want agents, teams and flows to compose through one abstraction, so that orchestration is uniform and no import cycle appears.

#### Acceptance Criteria

1. THE model adapters, `agents`, `teams` and `flows` SHALL implement the `Runnable` Port (one input, one output); `teams` and `flows` SHALL hold what they compose as `Runnable` references and SHALL NOT import `models`, `agents`, `teams` or `flows`.
2. THE role of a unit in a team SHALL be a free string owned by `teams`, distinct from the unit's identity (the same `Runnable` may hold different roles in different teams), and SHALL NOT be defined in `base` or `agents`.
3. IF a composition nests a unit within itself, THEN THE composing unit SHALL detect it with a visited set and a depth bound (default 100), stop at the detection point, and raise an error naming the cycle.
4. IF a module of `agents`, `teams` or `flows` imports another of the three, THEN THE import-matrix test SHALL fail.

### Requirement 6: Extension points

**User Story:** As a maintainer, I want every integration to enter through one extension point, so that adding one never means editing files across the library.

#### Acceptance Criteria

1. EACH integration kind SHALL have a Port in `base`, a registry and one owner: model provider in `models`, store backend in `store`, tool in `tools`, observability exporter in `observe`, credential provider in `auth`, agent type in `agents`.
2. WHERE an integration is added, THE change SHALL touch only the owning component: a provider is configuration or a thin dialect in `models`, a store backend is one new module in `store`, a tool or exporter is registered in its owner's registry, and no import SHALL break Requirement 2.
3. IF a change adds an integration and edits a file outside its owner, THEN THE structural check SHALL reject it and name the component, and a mandatory merge gate SHALL block it independently of that check.

### Requirement 7: Packaging, load and budgets

**User Story:** As a user deploying to a serverless runtime, I want a small install and an import that pulls nothing optional, so that the package is light and fast to load.

#### Acceptance Criteria

1. THE library SHALL be one distribution with extras, each component being always present or installed by an extra; EACH extra SHALL declare exactly the third-party libraries its component imports, and IF it declares one that is unused or omits one that is used, THEN THE budget tests SHALL report the mismatch.
2. THE library SHALL prefer the standard library, then libraries in the serverless runtime, then pure-Python packages; THE core SHALL NOT contain a compiled package.
3. THE library SHALL import optional libraries lazily; IF an extra is missing, THEN THE library SHALL raise `MissingExtraError` wrapping the original error and naming the extra.
4. WHEN `import <pkg>` runs in a core-only install, THE library SHALL import no `forbidden_at_import` library even if it is present, no more than `max_modules_loaded` modules, within `max_import_ms` (best of five runs); IF it imports a forbidden library, THEN THE budget tests SHALL fail and name it.
5. THE limits SHALL live in `budgets.toml`, read identically by `make budget-fast`, `make budget` and the workflow `.github/workflows/budgets.yml`; THE workflow SHALL run `tests/budget` on every pull request and fail on a breach; THE budgets SHALL only go down, and a change to a limit SHALL be an explicit, reviewed edit.
6. THE extras `teams` and `flows` SHALL exist as optional-dependency groups recorded in `budgets.toml`, SHALL be independent of each other (installing one excludes every library unique to the other), SHALL declare no third-party library and no compiled package until one is needed and be listed in `known_empty`; WHEN one is added, THE declaration SHALL equal the import and THE extra SHALL leave `known_empty` in the same change; THE core SHALL work with neither installed.
7. THE lists `known_leaks` and `known_import_failures` SHALL be empty; WHILE an entry exists, THE tests SHALL warn naming it, and IF a listed entry starts working again, THEN THE tests SHALL fail.
8. THE top-level package SHALL re-export only messages, completion, exceptions, config and the function `provider` (Requirement 9.11), none of which imports an optional or provider library when `import <pkg>` runs.
9. THE cold start of the library, measured in a fresh interpreter as `import <pkg>`, importing the router, building a router with one target and building one request, without network, SHALL stay within `max_cold_start_ms` of `budgets.toml` (best of five runs), a limit compatible with serverless (a thin Python function starts in 100 to 300 ms and an init of 500 to 2000 ms is usually acceptable for an LLM application); IF it is exceeded, THEN `tests/budget/test_cold_start.py` SHALL fail.

### Requirement 8: Codenames

**User Story:** As a maintainer, I want a quiet codename per component that never leaks into code, so that the theme is present without being needed.

#### Acceptance Criteria

1. EACH component SHALL have one codename matching `^[a-z]{3,7}$`; THE 15 codenames SHALL be unique and listed in `docs/glossary.md`.
2. A codename SHALL appear only in the front matter of the spec and docs section, one italic line under the section index title, the last line of the package docstring, and the glossary.
3. IF a codename appears in an import, a folder or file name, an identifier, a configuration key, a log field or a spec folder name, THEN THE codename test SHALL fail naming the codename and the place; THE test SHALL also check pattern, uniqueness and the count of 15.
4. THE documentation SHALL carry two more watermarks outside the 15, `vapor` (the `Runnable` Port) and the project umbrella watermark; each SHALL be unique against the 15, match `^[a-z]{3,7}$`, and never appear in code, imports, file or folder names, identifiers or configuration keys.

### Requirement 9: Models and providers

**User Story:** As a user, I want one lightweight implementation of every provider and no SDK to install, so that packages are small, behavior is predictable and I can switch providers without changing my code.

#### Acceptance Criteria

1. THE `models` component SHALL hold the adapters for language, embedding and decision models (Jev is the decision model), with one shared transport, retry policy, error mapping and token counter reused by every adapter.
2. WHEN a request fails with a transient error, THE `models` component SHALL retry up to 3 times after the first attempt before it maps the failure to a library error.
3. EACH provider SHALL have exactly one implementation, a thin standard-library REST adapter, with no vendor SDK shipped or on the runtime path and no SDK adapter registered as a provider; THE library SHALL NOT provide a selector, a selection variable, an `impl` setting, an SDK version table, an SDK fallback or SDK discovery.
4. THE vendor SDKs SHALL be development dependencies (a dev group, never an optional extra) and the oracle of the differential tests, which compare the fields and behaviors the library consumes (structured fields by subset, numbers within a stated epsilon, errors by category), run only where the SDK is installed in an environment apart from the core-only tests, and MAY skip when credentials or network are missing.
5. WHERE a component has a built-in and an external-library implementation, BOTH SHALL sit behind the same Port and return identical library types, THE external types SHALL be converted at one boundary inside the owner, and IF one appears in a Port return value, parameter or public API, THEN THE component SHALL be non-conformant until it is adapted; THE rule SHALL apply to `models`, the `tools` MCP client and any future backend of `observe`, `store`, `prompts` or `agents`.
6. WHEN messages or tools arrive in the OpenAI shape, THE library SHALL accept them and return library types without mirroring, subclassing or re-exporting any SDK class; IF an input does not conform, THEN THE library SHALL reject it naming the field and keep the input unchanged.
7. WHERE a user brings a vendor SDK, THE user SHALL wrap it in a `Runnable` adapter with no configuration, no environment variable and no registration; THE library SHALL expose no other SDK path.
8. THE `DecisionModel` Port SHALL return one option from a finite set with a probability per option, each in 0 to 1 and summing to 1, SHALL reject an empty set with an error and return no choice, and SHALL be consumed by `gateway`, `router` and `guard`.
9. WHEN a model identifier is given, THE library SHALL route the request to the provider implementation, and SHALL support synchronous and streaming completions for every provider; WHEN a provider call fails, THE library SHALL return a standardized error with the error type and provider details.
10. ALL provider-specific transformation of requests, messages and capabilities SHALL live inside the provider adapter; THE router, the tools and the completion models SHALL stay provider-agnostic, and adding a provider SHALL need no change outside its adapter.
11. THE library SHALL create the client of a provider with one call, `<pkg>.provider(name, **config)`, in the style of `boto3.client`, and the function SHALL import the models registry only when it is called, so that `import <pkg>` stays light.
12. THE client returned by `<pkg>.provider` SHALL support `complete`, `acomplete` and `stream` for a language model, and `encode`, `encode_batch`, `aencode` and `aencode_batch` for an embedding model (chosen with `provider_type="embedding"`); THE documentation and the examples SHALL use `<pkg>.provider` as the default way to create a client, naming the variable `client` (`embedder` for embeddings), and SHALL NOT use an alias such as `create_provider`.

### Requirement 10: Tools and the MCP client

**User Story:** As a user, I want to consume MCP tools, prompts and resources with a built-in client and choose `fastmcp` only explicitly, so that MCP works without extra dependencies or hidden configuration.

#### Acceptance Criteria

1. THE MCP client SHALL live in `tools` (the `gateway` is the library acting as an MCP server) and SHALL expose tools as `Capability` objects reusing the `tools` interfaces, prompts as `base` messages (without importing `prompts`), and resources as `Resource` objects.
2. THE built-in client SHALL be a standard-library JSON-RPC client over HTTP, consume-only, with no stdio transport, no subprocess and no server of its own; a stdio transport offered by `fastmcp` SHALL be outside the built-in contract and the differential tests.
3. WHEN `create_mcp_client(target)` is called without `impl`, THE factory SHALL return the built-in client; WHEN `impl="fastmcp"` and it is installed, THE `fastmcp` client; OTHERWISE it SHALL raise an error and return no client, with `MissingExtraError` naming the extra `mcp` if `fastmcp` is missing.
4. THE selection SHALL use no environment variable, configuration entry or fallback; `import <pkg>` SHALL import neither `fastmcp` nor an optional MCP dependency unless it is selected; BOTH clients SHALL return identical types, kept equal by differential tests.
5. THE library SHALL define a resource Port in `base` (list and read by URI, MIME type, text or bytes) implemented by the MCP client in `tools` (decision D26), so that `prompts` and `memory` can consume MCP resources through `base`; THE MCP prompt facet SHALL return `base` messages and SHALL NOT implement `PromptBuilderInterface`.
6. THE MCP client SHALL convert official MCP types to library types at one boundary point, covering all the fields and behaviors the library consumes, and IF a required field is absent or malformed, THEN THE boundary SHALL reject it naming the type and field and return no partial object.
7. THE `mcp` extra (providing `fastmcp`) SHALL be separate with its own budget, and `tools` SHALL carry no third-party library.

### Requirement 11: Authentication and credentials

**User Story:** As a user, I want every outbound request authenticated by one component that covers each provider's documented non-interactive modes, so that I write no authentication code per provider.

#### Acceptance Criteria

1. THE `auth` component SHALL import only `base`, implement the authentication Port (adds headers or signs a request), and provide strategies (API key and bearer, SigV4, OAuth2), credential sources (environment, files, container, instance metadata, token exchange, metadata server) and native secret-manager sources (AWS Secrets Manager, AWS SSM Parameter Store, Azure Key Vault, Google Secret Manager) that call over `base/http.py` authenticated with the `auth` strategies, and a lazy token cache with an expiry margin.
2. WHEN a request returns 401, THE `auth` component SHALL refresh the credential and retry once.
3. THE `auth` component SHALL start no background thread, SHALL NOT put a secret in a log, repr or error, and SHALL NOT run an interactive login; WHERE a mode needs an earlier vendor-tool login (AWS IAM Identity Center SSO, `az login`, `gcloud auth login`, application-default-credentials login), it SHALL read that tool's cache and, IF it is missing or expired, raise an error saying to log in again.
4. THE only third-party library SHALL be `rsa` (extra `auth`), used only to mint tokens; THE `google` extra SHALL declare only the provider SDK; `google-auth` and `cryptography` SHALL NOT be used.
5. WHERE user code needs another credential provider, THE `auth` component SHALL let it register one.
6. THE library SHALL read provider credentials only from each provider's standard variables (through `auth`), SHALL NOT read them from a prefixed variable, and SHALL define exactly three prefixed variables: `<PREFIX>_LOG_LEVEL`, `<PREFIX>_CONFIG`, `<PREFIX>_ENABLE_TELEMETRY`.
7. THE `auth` component SHALL support only documented, non-deprecated, non-interactive modes at a stated date.
8. THE `auth` component SHALL treat on-premises Active Directory (Kerberos, NTLM, ADFS), SAML, hardware security modules (PKCS#11) and non-RSA signing as out of scope.
9. THE design of `auth` SHALL verify against each provider's current documentation at least: the serverless execution role (environment variables, container-credentials endpoint, IMDSv2); AWS assume-role including cross-account through signed STS; web identity (OIDC token from a file); Bedrock API keys; Google service-account files (RS256 with `rsa`), impersonation, metadata server, authorized-user refresh token, Workload Identity Federation, and API key or access token from the environment; Microsoft Entra ID for Azure OpenAI (managed identity, client secret, certificate with `rsa`, federated token file, API key); and API key or bearer for OpenAI-compatible providers, Anthropic and Cohere.

### Requirement 12: State

**User Story:** As a maintainer, I want all state backends in one component behind one Port, so that durable state is not duplicated in each service.

#### Acceptance Criteria

1. THE `store` component SHALL hold the in-memory, file, DynamoDB and Redis backends, each in its own module, reached only through the storage Port in `base`; no other component SHALL keep a copy of a backend.
2. WHERE a durable backend is needed and none is declared, THE library SHALL default to DynamoDB, and WHERE a backend has a pure-Python and a compiled driver, to the pure-Python one.
3. IF a service needs a backend that has no Port in `base`, THEN THE Port SHALL be defined first.

### Requirement 13: Prompts

**User Story:** As a maintainer, I want prompts to reuse the liteprompt design without a compiled template engine, so that the footprint stays light.

#### Acceptance Criteria

1. THE `prompts` component SHALL reuse the liteprompt design (loaders, role-based messages, registry, truncation) and SHALL NOT depend on Jinja2 or any compiled template engine.
2. THE `jinja2` dependency SHALL NOT appear in `pyproject.toml` or `budgets.toml`; THE engine SHALL be the standard-library `prompts/engine.py`.

### Requirement 14: Licence

**User Story:** As the owner, I want an MIT project free of unattributed third-party code, so that the codebase is legally clean.

#### Acceptance Criteria

1. THE project SHALL be MIT-licensed with a `LICENSE` file, and SHALL NOT contain code or text copied from another project without its licence and attribution (a notice file and a comment at the copied code); ideas and public API shapes are exempt.
2. THE project SHALL NOT copy from an incompatible source such as the `enterprise/` directory of LiteLLM, and SHALL carry the prompt-poet MIT notice for anything taken from it.
3. THE prompt templates shipped SHALL be written for the project or carry the licence of their source.

### Requirement 15: Specs, steering and documentation

**User Story:** As a reader, I want one place for requirements and design, one spec per component and one wiki, so that I know where a thing is written and where to change it.

#### Acceptance Criteria

1. THE requirements, the high-level design and the decisions SHALL live only in `10-requirements.md`, `11-design.md` and `12-decisions.md`.
2. EACH component SHALL have exactly one spec, named `<n>-<layer>-<scope>` (`.kiro/specs/<n>-<layer>-<scope>/`, the layer from Requirement 2.1 and the component as the scope); the cross-cutting work SHALL live in the one spec `.kiro/specs/0-base-structure/`, at layer 0 with `0-base-base` and `0-base-auth`. EACH spec has `requirements.md` (Kiro format: its user stories as `### Requirement N:` blocks, each criterion being a pointer `THE spec SHALL realize Requirement N.k of #[[file:.kiro/steering/10-requirements.md]]`, never a copied rule), `design.md` (detailed design, opening with a `Builds on:` line that cites the sections and components of `11-design.md`) and `tasks.md` (the only place for tasks, each citing the requirements it satisfies).
3. WHEN a new spec needs a requirement that no existing one covers, THE requirement SHALL be added here, in Kiro format with the next number, and the spec SHALL cite it; existing numbers SHALL NOT be renumbered.
4. WHEN a requirement changes, THE change SHALL be made here with a decision-log line, and a milestone SHALL be added to each component that cites it.
5. THE documentation SHALL be a wiki with one section per component, a glossary and `docs/index.md`; IF a page lacks front matter, has a broken link or is unreachable from the index, THEN THE docs test SHALL fail.
6. THE `README.md` SHALL be a short entry (what the library is, install, quick start, links into the wiki), and every other explanation SHALL live in the wiki.
7. THE glossary page SHALL map each codename to its plain component name and role, list the two documentation-only watermarks apart from the 15, and state the contrast between `auth` (authentication) and `policy` (authorization).
8. THE steering files SHALL reflect the current code (package structure, naming conventions, configuration patterns with YAML examples, and examples that exist).

### Requirement 16: Interfaces and the standard response

**User Story:** As a component developer, I want well-defined interfaces and one response format whatever the provider, so that I can build compatible components and write provider-agnostic code.

#### Acceptance Criteria

1. THE `base` component SHALL provide the Ports for model invocation, streaming and configuration; prompt rendering and parameter injection; capability registration, validation and execution; memory store and retrieve; safety validation of input and output; observability of events, metrics and traces; storage persistence; and plugin lifecycle (initialization and cleanup).
2. WHEN a component implements a Port, THE library SHALL validate its compliance at initialization and at runtime.
3. THE library SHALL let plugins be registered and discovered dynamically.
4. THE library SHALL return every completion in one standard format with message content, role, metadata, token usage, model identifier and provider, and SHALL normalize provider-specific response fields to that schema.
5. WHEN streaming is enabled, THE library SHALL yield response chunks in one standard format.

### Requirement 17: Router and model configuration

**User Story:** As a platform engineer, I want to configure model routing with fallbacks in code or in YAML, so that my applications stay available when a provider has issues and I do not hardcode secrets.

#### Acceptance Criteria

1. THE router SHALL accept a model configuration with provider, model identifier, temperature and maximum tokens, and SHALL support several configurations for one logical model name.
2. WHEN a primary configuration fails, THE router SHALL try the fallback configurations if provided, SHALL record which configuration served each request, and SHALL expose the configuration metadata for observability.
3. WHEN a YAML file is provided, THE router SHALL load its routes from it; WHEN no file is provided, THE router SHALL work with programmatic configuration; IF the file is invalid, THEN THE router SHALL raise a `ConfigurationError` with details.
4. WHEN a `ModelTarget` field or a YAML value uses `${VAR}`, THE router SHALL substitute the environment variable for every string field, including API keys, and SHALL log the substitution at DEBUG level; IF the variable is missing, THEN THE router SHALL raise a `ConfigurationError`.

### Requirement 18: Errors and logging

**User Story:** As a developer, I want clear, actionable errors and structured logs, so that I can diagnose problems and plug the library into my observability stack.

#### Acceptance Criteria

1. THE library SHALL define a base error (`SkyeError` today, renamed with the project) and specific types for provider, configuration and validation errors; WHEN a provider returns an error, THE library SHALL wrap it in a `ProviderError` with provider context.
2. THE wrapped errors SHALL keep the original message and stack trace, and THE library SHALL log every exception at an appropriate level.
3. THE library SHALL emit structured log events for every model invocation with request and response details and a correlation ID, and SHALL support a log level per component.
4. THE library SHALL provide hooks for custom telemetry; WHEN a telemetry plugin is registered, THE library SHALL invoke the hooks for all significant events.

### Requirement 19: Token usage and cost

**User Story:** As a product manager, I want token usage and estimated cost for every call, so that I can monitor and control spending.

#### Acceptance Criteria

1. THE library SHALL compute prompt and completion tokens for every completion request and include them with the cost estimate in the response metadata.
2. WHERE pricing data is available, THE library SHALL estimate the cost from it, and SHALL accept custom pricing for private or custom models.
3. WHEN asked, THE library SHALL aggregate token usage across requests.

### Requirement 20: Configuration

**User Story:** As a DevOps engineer, I want to configure the library from code or files with predictable precedence, so that I can manage environments without code changes.

#### Acceptance Criteria

1. THE library SHALL accept configuration as a dictionary at initialization and from a YAML or JSON file (named by `<PREFIX>_CONFIG`).
2. WHEN several sources are present, THE library SHALL apply them in the order code, then environment, then file.
3. IF a configuration value is invalid, THEN THE library SHALL raise `ConfigurationError`.
4. THE configuration SHALL support `${VAR}` substitution of environment variables.

### Requirement 21: Type safety

**User Story:** As a Python developer, I want complete type hints and field-level validation errors, so that I catch mistakes early and get IDE support.

#### Acceptance Criteria

1. THE library SHALL type-hint every public API and SHALL support Python 3.10 and higher.
2. THE library SHALL define new data structures as dataclasses and SHALL NOT add pydantic models; moving the existing models is open decision O4.
3. WHEN invalid data reaches a data model, THE library SHALL raise a `ValidationError` with field-specific errors.

### Requirement 22: Terminology

**User Story:** As a developer, I want consistent terminology, so that I understand the library without confusion.

#### Acceptance Criteria

1. THE library SHALL use "Capability" in type names, variable names, documentation and prompts for what an LLM can invoke, and not "Tool".
2. WHEN the capability-related code is scanned, THE result SHALL show no "Tool" terminology, except the MCP wire terms and the folder `tools`.

### Requirement 23: Tests

**User Story:** As a developer, I want an organized and sufficient test suite, so that I can trust the library and find the tests I need.

#### Acceptance Criteria

1. THE tests SHALL be organized as `tests/unit` by module, `tests/integration` by feature, `tests/stress`, `tests/differential` and `tests/fixtures` (reusable), with property-based tests where they fit, and every test file SHALL have a docstring stating its purpose.
2. THE tests SHALL cover the major code paths of the capabilities, all routing strategies and all supported providers, with at least 80 percent coverage of the core.
3. THE stress tests SHALL cover concurrent requests, rate limiting under load, router failover and concurrent capability execution, and SHALL report performance metrics.

### Requirement 24: Examples

**User Story:** As a developer, I want well-organized examples, so that I learn each feature quickly.

#### Acceptance Criteria

1. THE examples SHALL be organized by feature category, each with a README.
2. THE examples SHALL demonstrate every capability type, YAML router configuration and every supported provider.
3. THE examples SHALL create a client with `<pkg>.provider(name, **config)` (Requirement 9.11), and WHEN the examples change or the library changes, a test SHALL run every example offline against a fake network and fail on an uncaught exception or on a failure that an example prints.
### Requirement 25: Embeddings

**User Story:** As a developer building retrieval, I want embedding adapters behind one Port, so that I can switch embedding models without changing my code.

#### Acceptance Criteria

1. THE `models` component SHALL provide embedding adapters for OpenAI, Bedrock (Titan), Cohere and Google, each a thin standard-library REST adapter behind the `VectorEncoder` Port in `base`, with no vendor SDK on the runtime path.
2. THE embedding adapters SHALL support single and batch encoding and SHALL provide sync and async forms, the async methods prefixed with `a` (`aencode`, `aencode_batch`).
3. EACH embedding adapter SHALL report its vector dimension.
4. WHERE a provider offers multimodal embeddings (for example Google `multimodalembedding`), THE adapter SHALL accept image inputs and return vectors in the same shape as text embeddings; IF a provider does not support multimodal embeddings, THEN THE adapter SHALL reject the input naming the limitation.

### Requirement 26: Multimodal inputs

**User Story:** As a developer building vision applications, I want to send images and other media to multimodal models, so that I can build richer experiences through the same interface.

#### Acceptance Criteria

1. THE `models` component SHALL accept image inputs in a user message as a URL, a base64 data URL, a file path or raw bytes, and SHALL convert them to each provider's documented shape at the provider boundary.
2. WHERE a model accepts audio or video, THE adapter SHALL carry those inputs through the same boundary conversion.
3. IF a provider does not support a submitted modality, THEN THE adapter SHALL raise a `ProviderError` naming the unsupported modality and SHALL leave the input unchanged.

### Requirement 27: Structured output

**User Story:** As a developer, I want models to return data validated against a declared shape, so that I can parse outputs reliably.

#### Acceptance Criteria

1. WHEN a completion request declares an output schema, THE `models` component SHALL use the provider's native structured-output mechanism where available and otherwise function calling, and SHALL validate the result against the declared shape.
2. THE declared output shape SHALL be a dataclass, not a pydantic model (decision D24); IF the result does not conform, THEN THE library SHALL raise a `ValidationError` naming the field.

### Requirement 28: Token counting

**User Story:** As a product manager, I want token counts without shipping a tokenizer in the core, so that the serverless footprint stays light while exact counts remain available.

#### Acceptance Criteria

1. THE `models` component SHALL provide an approximate token counter using only the standard library, present in the core install.
2. WHERE exact counts are needed, THE library SHALL use `tiktoken` through the optional `tiktoken` extra, imported lazily and never on the core runtime path; IF the extra is not installed, THEN THE library SHALL fall back to the approximate counter.
3. THE core install SHALL NOT import a tokenizer library at import time, and `import skye` SHALL NOT import `tiktoken`.

### Requirement 29: Prompt template registry

**User Story:** As a developer, I want to register and inspect versioned prompt templates, so that I can organize reusable prompts and debug them.

#### Acceptance Criteria

1. WHEN a template is registered from a string or from a file path, THE `prompts` registry SHALL store it under the given name and version; IF the file cannot be loaded, THEN THE registry SHALL raise `FileNotFoundError` with the attempted path.
2. WHEN a template is retrieved by name without a version, THE registry SHALL return the latest version, and WHEN with a version, the exact version; IF the template does not exist, THEN THE registry SHALL raise `KeyError`.
3. IF a template has invalid syntax at registration, THEN THE registry SHALL raise a validation error that carries the engine's error details.
4. WHEN templates are listed, THE registry SHALL return every registered name and version.
5. WHEN metadata is requested, THE registry SHALL return the variables (distinguishing required from optional), the examples, the content types, the roles, and the current settings for examples, roles and content types.
6. WHEN a template is validated, THE registry SHALL check the syntax and the variable references and return detailed results, without raising an exception for a validation failure.

### Requirement 30: Prompt rendering and variables

**User Story:** As a developer, I want to render templates with runtime data, defaults and conditional logic, so that I can generate dynamic prompts.

#### Acceptance Criteria

1. WHEN a template is rendered with all its required variables, THE builder SHALL return a list of `SkyeMessage` objects.
2. IF a required variable is missing, THEN THE builder SHALL raise `ValueError` naming the variables, unless the variable is in the allowed-missing list set by the developer.
3. WHEN variables that the template does not use are provided, THE builder SHALL ignore them without error.
4. THE builder SHALL use the default values for variables that are not provided, merge provided variables over the defaults with the provided ones winning, and call callable defaults to get their current values.
5. WHEN the variables of a template are extracted, THE builder SHALL return every variable name found in it.
6. WHEN a partial builder is created with bound variables, THE builder SHALL return a new instance with those variables pre-filled.
7. WHEN a template is composed from several parts, THE builder SHALL create a new template by joining the parts with the given separator.
8. THE template engine SHALL evaluate conditionals, loops and filters, SHALL let the developer register custom filters available in every rendering, and SHALL support whitespace control.
9. THE template engine SHALL NOT support macros, template inheritance, include directives or variable assignment (decision D20).

### Requirement 31: Few-shot examples

**User Story:** As a developer, I want to attach examples to templates and select them dynamically, so that I can implement few-shot prompting.

#### Acceptance Criteria

1. WHEN examples are added to a template, THE builder SHALL store them and, at rendering, format and inject them with the configured example template.
2. WHERE a semantic example selector is configured, THE builder SHALL select the examples most relevant to the input by similarity.
3. WHERE a random selector is configured, THE builder SHALL select random examples up to the maximum; WHERE a fixed selector is configured, it SHALL always use the same set.
4. WHEN no example selector is configured, THE builder SHALL use all available examples up to a reasonable default limit.

### Requirement 32: Prompt message roles and multimodal content

**User Story:** As a developer, I want to control message roles and include images and other media, so that I can build proper conversations for text, vision and audio models.

#### Acceptance Criteria

1. WHEN roles are set for template sections, THE builder SHALL create a separate `SystemMessage`, `UserMessage` or `AssistantMessage` for each, and WHEN no role mapping is given, a `UserMessage`.
2. WHEN message placeholders are added, THE builder SHALL allow dynamic insertion of conversation history.
3. IF a role name is invalid, THEN THE builder SHALL raise a validation error.
4. WHEN content is configured for a variable, THE builder SHALL process image URLs, base64 data and file paths, validate the content format, and create messages with the proper multimodal content structure.
5. WHEN multimodal content is rendered, THE builder SHALL preserve the content type metadata in the resulting messages.
6. IF the image format or a content type is invalid, THEN THE builder SHALL raise a validation error with a descriptive message that lists the supported formats.

### Requirement 33: Prompt output schema

**User Story:** As a developer, I want to declare the expected output schema in a prompt, so that I can generate structured outputs and validate responses.

#### Acceptance Criteria

1. WHEN an output schema is set with a dataclass, THE builder SHALL generate the JSON-schema instructions for it (decision D24: a Pydantic model is not used).
2. WHEN an output schema is set with a JSON-schema dictionary, THE builder SHALL format it for the model.
3. WHEN output instructions are requested, THE builder SHALL return them formatted from the configured schema, and an empty text when no schema is configured.
4. IF a schema is invalid, THEN THE builder SHALL raise a validation error.

### Requirement 34: Prompts integration and performance

**User Story:** As a developer, I want prompts to fit the rest of the library and render fast, so that I can use them with other components under load.

#### Acceptance Criteria

1. THE `prompts` component SHALL need no third-party dependency (decisions D20 and Requirement 13: the template engine is the standard-library one).
2. THE builder SHALL create standard `SkyeMessage` objects that every provider accepts, and SHALL create and format `CapabilityMessage` objects when used with capabilities.
3. THE builder SHALL follow the library's configuration patterns with `${VAR}` substitution (Requirement 20.4), and SHALL use the library's exception hierarchy and logging.
4. WHEN a template is registered, THE builder SHALL compile and cache it, and SHALL reuse the compiled template for later renderings without recompiling.
5. THE builder SHALL cache the variable list of a template and the formatted examples for reuse.
6. WHEN many templates are registered, THE builder SHALL keep memory use reasonable through efficient storage.

### Requirement 35: Policy model and evaluation

**User Story:** As a security owner, I want rules expressed as permit and forbid with predictable evaluation, so that access is explicit, reviewable and repeatable.

#### Acceptance Criteria

1. THE `policy` component SHALL represent a policy as an effect (permit or forbid), a scope over principal, action and resource, and optional when and unless conditions over context and attributes.
2. THE `policy` component SHALL allow a scope element to be any, an exact entity, a set of entities, or a membership test (in a group or collection).
3. THE `policy` component SHALL give every policy an identifier and optional annotations (description, owner).
4. THE `policy` component SHALL deny a request unless at least one permit policy matches, and WHEN any forbid policy matches, SHALL deny whatever the permits.
5. THE `policy` component SHALL return the decision with the identifiers of the policies that determined it.
6. THE `policy` component SHALL evaluate without side effects and give the same decision for the same inputs.
7. WHEN a condition cannot be evaluated (a missing attribute, a type error), THE `policy` component SHALL treat that policy as not matching and record the error.
8. THE conditions SHALL support comparisons, boolean operators, set membership, attribute presence tests, string prefix and suffix tests, and membership in an entity hierarchy.
9. THE conditions SHALL NOT support loops, user-defined functions, I/O or regular expressions.
10. THE `policy` component SHALL bound evaluation time by the size of the policy set, with no unbounded recursion.

### Requirement 36: Policy entities, representation and validation

**User Story:** As a platform engineer, I want to describe who and what exists, write policies in a reviewable format, and have mistakes found at load time, so that policies are correct before any request is denied.

#### Acceptance Criteria

1. THE `policy` component SHALL take entities from an entity provider supplied by the caller, as identifier, attributes and parents.
2. THE `policy` component SHALL support principals from IAM identities and from JWT claims, mapped by a configurable function.
3. THE `policy` component SHALL treat an unknown entity as having no attributes and no parents.
4. THE `policy` component SHALL load policies from JSON and TOML with the standard library.
5. THE `policy` component SHALL define a text syntax close to Cedar for the same policies (open decision O9).
6. IF a policy has an error, THEN THE `policy` component SHALL report it with the policy identifier and the position of the problem.
7. THE `policy` component SHALL export a policy set to the representation it was loaded from without changing its meaning.
8. THE `policy` component SHALL validate policies against a schema of entity types, actions and attributes, built from the gateway registry so that every tool is an action.
9. IF a policy names an unknown action or attribute, THEN THE `policy` component SHALL reject the policy set at load time.

### Requirement 37: Policy integration, enforcement and observability

**User Story:** As a security owner, I want one engine for every place that needs a decision, a way to try policies before enforcing them, and a record of every decision, so that access is enforced and auditable.

#### Acceptance Criteria

1. THE `policy` component SHALL implement the authorizer Port (Requirement 4.2): one interface that takes principal, action, resource and context and returns a decision.
2. THE gateway SHALL use the engine for tool listing, tool discovery and tool calls; the router MAY use it to restrict the models and regions a principal may use; the agent loop MAY use it through a hook provider at the policy check operation; the memory systems MAY use it for read and write access.
3. THE `policy` component SHALL support enforce and log-only modes, set per policy set, and in log-only mode SHALL return allow and record the decision it would have made.
4. THE `policy` component SHALL load a policy set from a file, an environment variable or an external store (DynamoDB through boto3 in Lambda).
5. THE `policy` component SHALL cache a loaded policy set with a time to live and refresh it inside the request that notices the expiry, not in a background thread.
6. THE `policy` component SHALL give each policy set a version and a content hash and include both in every decision log.
7. THE `policy` component SHALL write one structured JSON log line per decision (principal, action, resource, decision, determining policies, policy set version, latency) and SHALL NOT log context values unless a setting enables it.
8. THE `policy` component SHALL publish counters for allow, deny and error through the observability module.

### Requirement 38: Policy dependencies and Cedar alignment

**User Story:** As a maintainer and security owner, I want the policy engine to stay light and move to Cedar later without rewriting policies, so that it fits a Lambda package and has a clear upgrade path.

#### Acceptance Criteria

1. THE `policy` component SHALL use only the standard library, with no compiled dependency and no third-party import at module level.
2. THE `policy` component SHALL have an entry in `budgets.toml` for import time and a limit on evaluation time for a typical policy set (values open, O10), and SHALL pass the budget tests.
3. THE `policy` component SHALL document which parts of Cedar it implements and which it leaves out.
4. THE `policy` component SHALL keep the permit, forbid, scope and condition semantics identical to Cedar for the parts it implements.
5. THE `policy` component SHALL be tested with policies and requests whose expected decisions come from the Cedar documentation (availability and licence of an official conformance suite is open, O9).

### Requirement 39: Agent loop and hook points

**User Story:** As a developer, I want the agent loop in one reusable class with a hook point before and after each operation, so that I can build my own agent without rewriting the loop.

#### Acceptance Criteria

1. THE `agents` component SHALL provide a `BaseAgent` class that implements the agent loop for synchronous and asynchronous use.
2. THE `BaseAgent` SHALL take as inputs the model (or the router), a `ToolProvider`, optional memory and optional hook providers.
3. THE `BaseAgent` SHALL stop when the model returns a final answer, when the maximum number of steps is reached, when a hook stops the run, or when the run is suspended, and SHALL return a result that states why the run ended.
4. THE default `Agent` SHALL be a `BaseAgent` subclass and SHALL NOT duplicate the loop.
5. THE `BaseAgent` SHALL define these operations, each with a pre hook point and a post hook point: run, step, toolset selection, model call, tool call, memory read, memory write, safety check, policy check.
6. WHEN an operation fails, THE `BaseAgent` SHALL call the error hooks of that operation.
7. THE `BaseAgent` SHALL pass each hook a context with the `AgentState`, the operation name and the operation payload (the request before, the result after).
8. THE `agents` component SHALL list the operations in one enumeration so that hooks can be registered by name.

### Requirement 40: Hook semantics and customization

**User Story:** As a developer, I want hooks that can change what happens, in several ways to customize, so that a small change does not need a new class and observers cannot alter a run.

#### Acceptance Criteria

1. THE pre hook of an operation SHALL be able to return one of: continue unchanged, continue with a modified payload, skip the operation and supply its result, or deny the operation with a reason.
2. THE post hook of an operation SHALL be able to return one of: keep the result, replace the result, retry the operation with a modified payload within a retry limit, or stop the run.
3. THE `BaseAgent` SHALL run pre hooks in registration order and post hooks in reverse order.
4. THE `BaseAgent` SHALL accept hooks written as synchronous or asynchronous functions.
5. WHEN a hook raises an error, THE `BaseAgent` SHALL apply a per-hook setting, fail closed (stop the operation) or fail open (log and continue), the default being fail closed for hooks that protect (safety, policy, limits) and fail open for observers.
6. THE `BaseAgent` SHALL provide a retry limit and a per-hook time limit (default values open, O11).
7. THE `BaseAgent` SHALL let a subclass override a method for each hook point, let a caller register and remove hooks on an instance by operation name, and accept hook providers that register several hooks together.
8. THE `BaseAgent` SHALL let hooks be restricted to a subset of tools or models, by name or tag.
9. THE `BaseAgent` SHALL document the order in which subclass overrides, instance hooks and hook providers run.
10. THE `BaseAgent` SHALL call the existing event-handler methods for model calls, tool calls, steps and completion.
11. THE `BaseAgent` SHALL treat event-handler implementations as observers: their errors SHALL NOT stop the run, and they SHALL NOT modify a payload or a result.

### Requirement 41: Default agent behaviour

**User Story:** As a developer, I want the default agent's own rules to be visible and removable, so that nothing is hidden in the loop.

#### Acceptance Criteria

1. THE default `Agent` SHALL provide these optional, replaceable hook providers: limits (steps, tokens, cost, time), safety (the safety Port), policy (the authorizer Port), observability (the event-handler and observer Ports), and checkpointing.
2. THE default `Agent` SHALL enable the limits provider by default.
3. WHEN a safety filter or an authorizer is configured, THE default `Agent` SHALL enable the matching provider automatically.
4. THE default `Agent` SHALL expose the list of active hooks, in execution order, for inspection.

### Requirement 42: Agent toolset, state and resumability

**User Story:** As a platform engineer, I want the agent to ask for the tools its operation needs and a run to survive the end of a Lambda invocation, so that the loop behaves correctly in serverless.

#### Acceptance Criteria

1. THE `BaseAgent` SHALL obtain tools only through a `ToolProvider`, at the toolset selection operation, at the start of a run and again when a hook or the model asks for different tools.
2. THE `BaseAgent` SHALL work with the local capability registry as `ToolProvider` without any gateway.
3. WHEN the `ToolProvider` is the gateway client, THE `BaseAgent` SHALL carry the scope token in the `AgentState` and send it with every tool call, and SHALL pass the operation description to the `ToolProvider` (who writes it is open, O12).
4. THE `BaseAgent` SHALL keep the whole run in an `AgentState` that serializes to JSON with the standard library.
5. THE `BaseAgent` SHALL save a checkpoint through the storage Port at configurable points (after each step by default).
6. WHEN the remaining time, read from a configurable function (the Lambda context, or a deadline elsewhere), is below a configurable margin, THE `BaseAgent` SHALL stop before the next step and return a `Suspended` result with the checkpoint identifier.
7. WHEN given a checkpoint identifier, THE `BaseAgent` SHALL resume the run from the saved state.
8. THE `BaseAgent` SHALL NOT use multiprocessing and SHALL NOT start work that continues after the run returns.
9. WHEN a model asks for several tools in one step, THE `BaseAgent` SHALL run them concurrently, with asyncio or threads, up to a configurable limit, and return the results in the order the model asked for them.
10. WHEN a model call fails, THE `BaseAgent` SHALL use the fallbacks and retries of the router before failing the operation.
11. WHEN a tool call fails, THE `BaseAgent` SHALL return the error to the model as a tool result, unless a hook stops the run (the default per error type is open, O13).
12. THE `BaseAgent` SHALL stop after a configurable number of consecutive failed steps.
13. THE `BaseAgent` SHALL count tokens and cost per run from the model responses and expose them in the result.

### Requirement 43: Agent runtime packaging and tests

**User Story:** As a maintainer, I want the runtime light and testable without a real model, so that it stays in budget and its loop and hooks are verified.

#### Acceptance Criteria

1. THE `agents` component SHALL use the standard library for the models of state, hooks and results (dataclasses, enums, json) and SHALL NOT add a third-party import at module level.
2. THE `agents` component SHALL be part of the core, with no extra of its own.
3. THE `agents` component SHALL have an entry in `budgets.toml` for import time and module count (values open, O11) and SHALL pass the budget tests.
4. THE library SHALL provide a scripted model for tests that returns prepared responses and tool calls.
5. THE test suite SHALL cover each hook outcome (continue, modify, skip, deny, retry, replace, stop), the hook order, fail open and fail closed, suspension and resumption, and concurrent tool calls.

### Requirement 44: Gateway endpoint, targets, registry and local mode

**User Story:** As an agent developer and platform engineer, I want one standard MCP endpoint over targets I attach, backed by an external registry, that also runs locally, so that any MCP client can use my tools and I can test without AWS.

#### Acceptance Criteria

1. THE `gateway` SHALL serve MCP over stateless HTTP, handling initialize, ping, tools/list and tools/call, and SHALL NOT require a session held in the memory of one process between requests.
2. THE `gateway` SHALL return protocol errors in the JSON-RPC format defined by MCP.
3. THE `gateway` SHALL be implemented with the Python standard library, without the `mcp` package and without a web framework.
4. THE `gateway` SHALL state the MCP specification version it implements (the version, and whether responses stream, are open, O14).
5. THE `gateway` SHALL support four target types: Lambda function, OpenAPI document, upstream MCP server, local capability.
6. WHEN a target is registered, THE `gateway` SHALL convert its operations into tools with a stable identifier made of the target and the tool name.
7. THE `gateway` SHALL read OpenAPI documents in JSON, and in YAML only when the optional YAML parser is installed.
8. WHEN one target fails, THE `gateway` SHALL keep serving the tools of the other targets.
9. THE `gateway` SHALL reuse the existing capability registry for local capabilities.
10. THE `gateway` SHALL keep the registry in an external store: DynamoDB through boto3 in Lambda, files or memory for local use and tests (whether S3 or Parameter Store are also supported is open, O15).
11. THE `gateway` SHALL load the registry lazily and cache it in the warm container with a time to live, and WHEN the time to live expires SHALL refresh it inside the request that notices it, not in a background thread.
12. THE `gateway` SHALL store for each tool its name, description, argument schema, tags, target and version.
13. THE `gateway` SHALL run as a local HTTP server built on the standard library, using the same request handler as in Lambda.

### Requirement 45: Gateway toolset per operation, discovery and scope token

**User Story:** As an agent developer, I want the agent to see only the tools its current operation needs, find more when it needs them, and have that bound by a stateless token, so that prompts stay small and the agent cannot reach tools it should not use.

#### Acceptance Criteria

1. WHEN a client lists tools for an operation, THE `gateway` SHALL return only the toolset selected for that operation, taking the operation description, tags and principal from the caller in each request.
2. THE `gateway` SHALL limit the size of a toolset to a configurable maximum (the default is open, O16).
3. THE `gateway` SHALL reject a tool call for a tool outside the toolset named by the scope token.
4. WHEN no operation is given, THE `gateway` SHALL return only the discovery tool.
5. THE `gateway` SHALL always expose a discovery tool (`<prefix>_find_tools`) that takes a query and returns matching tools.
6. WHEN the discovery tool returns tools, THE `gateway` SHALL return an extended scope token that includes them.
7. THE `gateway` SHALL apply the authorizer to the discovery results, so that a caller never learns about tools it may not use.
8. THE `gateway` SHALL issue a scope token that carries the operation identifier, the tool identifiers, the principal and an expiry time.
9. THE `gateway` SHALL sign the scope token with HMAC-SHA256 from the standard library.
10. WHEN a tools/call arrives, THE `gateway` SHALL verify the signature and the expiry before executing.
11. THE `gateway` SHALL read the signing key from the environment or from a secrets store (key rotation is open, O17).

### Requirement 46: Gateway selection strategies

**User Story:** As an agent developer, I want to choose tools with hybrid search or with a decision model, so that the agent gets the right few tools fast, with every choice a setting of mine and not a hidden default.

#### Acceptance Criteria

1. THE `gateway` SHALL define a selector interface that takes an operation and the registry and returns ranked tools with a reason for each, so that other selectors can be added later.
2. THE `gateway` SHALL ship two selectors: hybrid search and Jev.
3. THE hybrid selector SHALL combine a lexical ranking (BM25-style, standard library) with a semantic ranking (embeddings from a model of the `models` component) and fuse the two rankings.
4. THE `gateway` SHALL support more than one fusion method (reciprocal rank fusion and weighted scores), chosen by a setting.
5. THE `gateway` SHALL compute the embedding of a tool when the tool is registered and store it through a vector storage interface, with an implementation that keeps vectors with the tool in the registry and room for others, and SHALL NOT require a vector database.
6. THE `gateway` SHALL support ranking all tools and ranking only the best N lexical candidates, chosen by a setting.
7. WHEN the embedding service is unavailable, THE hybrid selector SHALL use the lexical ranking alone and record that it did.
8. THE Jev selector SHALL ask a decision model (Jev, or any model that implements the decision Port of `models`) to choose the tools for an operation from a shortlist, and SHALL record the probabilities it returns.
9. THE `gateway` SHALL reach a decision model through an endpoint and credentials given in settings, and SHALL work with any endpoint that speaks the Jev wire format, local-jev included.
10. WHEN there are more candidates than the maximum number of labels set for the decision model, THE selector SHALL choose in two steps, domain first and then tool.
11. WHEN the probability of the best choice is below the configured threshold, THE selector SHALL return the hybrid shortlist instead; WHEN the decision model is unavailable, THE `gateway` SHALL fall back to the hybrid selector and record the fallback.
12. THE `gateway` SHALL support three modes, chosen per operation type by a setting: hybrid alone, Jev alone, and hybrid then Jev (hybrid builds the shortlist, Jev chooses from it).
13. THE `gateway` SHALL record which selector and which mode exposed each tool, for audit.
14. THE `gateway` SHALL NOT choose the mode, the decision model, the embedding model, the vector storage or any threshold on its own; each is a setting provided by the owner, and WHEN the chosen mode needs a setting that is not set, THE `gateway` SHALL fail with a clear error naming it.
15. THE `gateway` SHALL define one configuration object for these settings: the selection mode per operation type; the decision model endpoint and credentials, maximum labels and probability threshold; the embedding model and the vector storage; the hybrid fusion method, the number of lexical candidates (all or the best N) and the weights; and the toolset size per operation.

### Requirement 47: Gateway authorization

**User Story:** As a platform engineer and security owner, I want to know who is calling, call each target with its own credentials, and have every listing and call authorized in one place, so that callers never hold credentials and access is enforced.

#### Acceptance Criteria

1. THE `gateway` SHALL support AWS IAM (SigV4) authentication and a JWT authorizer in front of it, taking the principal from the verified identity.
2. THE `gateway` SHALL NOT verify JWT signatures itself unless this is approved in design (it needs RSA verification without a compiled library, O18).
3. WHEN no identity is available, THE `gateway` SHALL deny the request unless an explicit local-development setting allows it.
4. THE `gateway` SHALL support these outbound modes per target, through the `auth` component: the function execution role, API key, OAuth client credentials, SigV4 signing.
5. THE `gateway` SHALL cache an OAuth access token in the warm container until shortly before it expires.
6. THE `gateway` SHALL NOT include credentials in tool results, logs or error messages.
7. THE `gateway` SHALL ask the authorizer for a decision on every tools/list, every discovery query and every tools/call (Requirement 4.3).
8. WHEN the decision is deny, THE `gateway` SHALL omit the tool from listings and reject the call.
9. THE `gateway` SHALL support an enforcement mode and a log-only mode.

### Requirement 48: Gateway operation: Lambda, observability and budgets

**User Story:** As a platform engineer and maintainer, I want the gateway to behave correctly in Lambda, leave a record of what each agent could see and do, and stay small, so that it deploys in one function within budget.

#### Acceptance Criteria

1. THE `gateway` SHALL NOT use multiprocessing and SHALL NOT depend on work that continues after the response is returned, because the environment is frozen between invocations.
2. THE `gateway` SHALL run concurrent I/O, such as calls to several targets, with asyncio or threads inside one invocation only.
3. THE `gateway` SHALL finish every request within a configurable time limit and return a partial result with an error note when a target is late.
4. THE `gateway` SHALL keep all state that must survive between invocations in the external store.
5. THE `gateway` SHALL write one structured JSON log line per decision (principal, operation identifier, selector, tools exposed or called, policy decision, latency) and SHALL NOT log tool arguments or results unless explicitly enabled.
6. THE `gateway` SHALL publish its counters through the observability module.
7. THE `gateway` SHALL depend only on the standard library and libraries preinstalled in the serverless runtime.
8. THE `gateway` SHALL have its own entry in `budgets.toml` for size over the core and import time (values open, O16) and SHALL be covered by the budget tests in the pull request workflow.

### Requirement 49: Teams

**User Story:** As a developer, I want to coordinate several units (models, agents, flows or other teams) toward a shared objective, so that I can build multi-unit behavior from one abstraction.

#### Acceptance Criteria

1. THE `teams` component SHALL define a `TeamMember` that holds a `Runnable`, a role, a name and metadata.
2. THE roles SHALL be free strings defined by the team type and not a closed enumeration in `base` (Requirement 5.2).
3. THE `teams` component SHALL provide a supervisor that decides which member works next and how work is routed to members, and the supervisor MAY use a decision model received as a `Runnable`.
4. THE `teams` component SHALL provide coordination strategies: parallel, hand-off and vote.
5. THE `teams` component SHALL detect a team that contains itself, directly or transitively (Requirement 5.3).

### Requirement 50: Flows

**User Story:** As a developer, I want to sequence units into steps with conditions and error handling, so that I can express a workflow as data.

#### Acceptance Criteria

1. THE `flows` component SHALL define a step with a name (`step_name`), an error handler (`on_error`), conditions and branching, and each step SHALL hold a `Runnable`.
2. THE `flows` component SHALL run steps in sequence, SHALL run in parallel the steps declared as parallel, and SHALL apply the step's error handler when it fails.
3. THE `flows` component SHALL detect a flow that contains itself, directly or transitively (Requirement 5.3).

### Requirement 51: Guard

**User Story:** As a security owner, I want safety filters and pre-flight checks that the runtime can use without depending on them, so that unsafe inputs and outputs are caught and no optional service is forced on a user.

#### Acceptance Criteria

1. THE `guard` component SHALL provide safety filters that validate the input and the output of a model call through the safety Port in `base`.
2. THE `guard` component SHALL provide pre-flight checks that MAY ask a decision model (Requirement 9.8).
3. THE runtime components SHALL reach `guard` only through the safety Port, never by import (Requirement 4.1).

### Requirement 52: Memory

**User Story:** As a developer, I want conversation and state memory behind one Port, so that agents can remember without depending on a particular store.

#### Acceptance Criteria

1. THE `memory` component SHALL provide conversation and state memory through the memory Port in `base`, persisting through the storage Port (Requirement 12.1).
2. THE `memory` extra SHALL declare exactly the libraries the component imports, `redis` and `asyncpg`, and no compiled driver (Requirement 7.1).
3. THE runtime components SHALL reach `memory` only through the memory Port, never by import (Requirement 4.1).

### Requirement 53: Observe

**User Story:** As a platform engineer, I want events, logs, metrics and traces behind Ports, so that I can plug the library into my observability stack without the runtime depending on it.

#### Acceptance Criteria

1. THE `observe` component SHALL provide events, logs, metrics and traces through the observer and event-handler Ports in `base`.
2. THE `observe` component SHALL accept new exporters through its registry (Requirement 6.1).
3. WHERE an exporter has no standard-library path, THE `observe` extra SHALL declare only that library (Requirement 7.1).
4. THE runtime components SHALL reach `observe` only through the observer Port, never by import (Requirement 4.1).
