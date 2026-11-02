---
inclusion: manual
---

# Requirements Document

## Introduction

The only place where requirements are written. Component specs repeat the user stories they serve and cite the numbers
below as pointers (`THE spec SHALL realize Requirement 9.2 of #[[file:.kiro/steering/10-requirements.md]]`); they do not copy criteria. `Requirement 9.2` means criterion 2 of Requirement 9. A requirement
starts at the heading `### Requirement 9: <title>` (the Kiro syntax), so `grep -n -A25 "^### Requirement 9:" .kiro/steering/10-requirements.md`
returns it whole. Design is in `11-design.md`; decisions, taken and open, are in `12-decisions.md`. To change a requirement, edit it here
and add a line to the decision log. Where each criterion of the former specs went is in `.kiro/docs/requirements-trace.md`.
Written without the project name (it is being chosen); `<pkg>` is the import package. Terms: **Port** is an interface in `base`;
**Extra** is an optional dependency group; **Runnable** is the one-input, one-output Port.

## Requirements

### Requirement 1: Component names

**User Story:** As a maintainer, I want one short plain name per component used everywhere, so that a name tells me what a folder, spec or docs section holds.

#### Acceptance Criteria

1. THE library SHALL have exactly 15 components: base, auth, models, store, router, tools, prompts, memory, guard, policy, observe, gateway, agents, teams, flows.
2. EACH name SHALL match `^[a-z]{3,7}$` and SHALL be the same for the component's package, spec folder, docs section and `budgets.toml` entry.
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
8. THE top-level package SHALL re-export only messages, completion, exceptions and config, none of which imports an optional or provider library.

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

### Requirement 10: Tools and the MCP client

**User Story:** As a user, I want to consume MCP tools, prompts and resources with a built-in client and choose `fastmcp` only explicitly, so that MCP works without extra dependencies or hidden configuration.

#### Acceptance Criteria

1. THE MCP client SHALL live in `tools` (the `gateway` is the library acting as an MCP server) and SHALL expose tools as `Capability` objects reusing the `tools` interfaces, prompts as `base` messages (without importing `prompts`), and resources as `Resource` objects.
2. THE built-in client SHALL be a standard-library JSON-RPC client over HTTP, consume-only, with no stdio transport, no subprocess and no server of its own; a stdio transport offered by `fastmcp` SHALL be outside the built-in contract and the differential tests.
3. WHEN `create_mcp_client(target)` is called without `impl`, THE factory SHALL return the built-in client; WHEN `impl="fastmcp"` and it is installed, THE `fastmcp` client; OTHERWISE it SHALL raise an error and return no client, with `MissingExtraError` naming the extra `mcp` if `fastmcp` is missing.
4. THE selection SHALL use no environment variable, configuration entry or fallback; `import <pkg>` SHALL import neither `fastmcp` nor an optional MCP dependency unless it is selected; BOTH clients SHALL return identical types, kept equal by differential tests.
5. THE `Resource` type SHALL be internal to `tools` while no other component needs it; WHEN `prompts` or `memory` needs MCP resources, THE library SHALL define a resource Port in `base` (list and read by URI, MIME type, text or bytes) implemented by the MCP client (open decision O7).
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
2. EACH component SHALL have exactly one spec, named like the component (`.kiro/specs/<component>/`); the cross-cutting work SHALL live in the one spec `.kiro/specs/skye-structure/`. EACH spec has `requirements.md` (Kiro format: its user stories as `### Requirement N:` blocks, each criterion being a pointer `THE spec SHALL realize Requirement N.k of #[[file:.kiro/steering/10-requirements.md]]`, never a copied rule), `design.md` (detailed design, opening with a `Builds on:` line that cites the sections and components of `11-design.md`) and `tasks.md` (the only place for tasks, each citing the requirements it satisfies).
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
