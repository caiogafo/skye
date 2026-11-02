# Requirements trace

Every acceptance criterion of the former specs (`structure`, `skye`, `skye-consolidation`, `wiki`) and where it is now: a criterion of
`.kiro/steering/10-requirements.md` ("Now" is `Requirement N.k` written as `N.k`), a decision (`D`, `O` in `12-decisions.md`), or `history`
(a migration step already done in code, kept only as a record). Source ids are `S<requirement>.<criterion>` for `structure`,
`B...` for `skye` (the base spec) and `C...` for `skye-consolidation`. `tests/budget/test_steering.py` checks that every target exists.

## structure

| Source | Text (start) | Now |
|---|---|---|
| S1.1 | THE Structure_Spec SHALL define each Component with a single name matching `^[a-z]{3,7}$`  | 1.1 |
| S1.2 | THE Structure_Spec SHALL use one identical name string for a Component's package folder, s | 1.2 |
| S1.3 | THE Structure_Spec SHALL define the Component set as exactly these 15 names and no others: | 1.1 |
| S1.4 | THE Structure_Spec SHALL define the cross-cutting spec set as exactly these 3 names and no | history: spec set replaced (R15.2) |
| S1.5 | WHERE a name is used at class or function level, THE Structure_Spec SHALL allow descriptiv | 1.4 |
| S1.6 | IF a proposed Component name exceeds 7 letters, has fewer than 3 letters, contains a chara | 1.3 |
| S2.1 | THE Structure_Spec SHALL define exactly four Layers with ordinals: base=0, adapters=1, ser | 2.1 |
| S2.2 | THE Structure_Spec SHALL assign Components to Layers as: Layer 0 = {base, auth}; Layer 1 = | 2.1 |
| S2.3 | THE Structure_Spec SHALL require that a Component in Layer N import only from Components i | 2.2 |
| S2.4 | THE Base_Package SHALL import only the Python standard library and SHALL perform no file-s | 3.2 |
| S2.5 | THE Structure_Spec SHALL set these Component-level allowed imports (the Allowed_Imports_Ma | 2.2, 2.3 |
| S2.6 | IF a Component imports from a Component of a higher Layer, or violates the Component-level | 2.4 |
| S2.7 | THE Structure_Spec SHALL require a deterministic test, using static analysis of the abstra | 2.4 |
| S2.8 | THE Structure_Spec SHALL record these known import violations to be removed: `completion.p | history: violations removed in code |
| S3.1 | THE Structure_Spec SHALL define `base` as a real importable package at `skye/base/` contai | 3.1 |
| S3.2 | THE Base_Package SHALL contain: the core models (messages, completion, capability schema), | 3.1 |
| S3.3 | THE Base_Package SHALL define each Port as an interface that performs no I/O and contains  | 3.4 |
| S3.4 | IF any `base` module imports a package outside the Python standard library, THEN THE Struc | 3.5 |
| S3.5 | THE Structure_Spec SHALL NOT require pydantic as an import dependency of the Base_Package. | 3.3 |
| S3.6 | THE Structure_Spec SHALL record Assumption A1 as an open, unresolved tension whose scope i | O4 |
| S4.1 | THE Structure_Spec SHALL define `models` as the Component holding adapters for every model | 9.1 |
| S4.2 | THE `models` Component SHALL contain one shared HTTP transport, retry policy, error mappin | 9.1 |
| S4.3 | WHEN an adapter's request fails with a transient error, THE `models` Component SHALL retry | 9.2 |
| S4.4 | THE Base_Package SHALL define exactly one `DecisionModel` Port whose response returns one  | 9.8 |
| S4.5 | IF a `DecisionModel` call receives an empty option set, THEN THE `models` Component SHALL  | 9.8 |
| S4.6 | THE Structure_Spec SHALL place the Decision_Model implementation (Jev) inside `models` as  | 9.1 |
| S4.7 | THE Structure_Spec SHALL record that the `DecisionModel` Port is consumed by `gateway` for | 9.8 |
| S4.8 | WHERE a provider offers a REST API reachable with the standard library, THE Structure_Spec | 9.3 |
| S5.1 | THE Structure_Spec SHALL define `store` as exactly one shared Component containing the in- | 12.1 |
| S5.2 | WHERE a Port for a store backend exists in `base`, services SHALL consume the backend only | 12.1 |
| S5.3 | IF a service needs a store backend with no `base` Port, THEN a Port SHALL be defined in `b | 12.3 |
| S5.4 | THE Structure_Spec SHALL designate DynamoDB the first-choice durable backend; any durable- | 12.2 |
| S5.5 | THE Structure_Spec SHALL NOT place a copy of any storage backend inside a service Componen | 12.1 |
| S5.6 | WHERE a backend offers a pure-Python and a compiled driver, THE Structure_Spec SHALL defau | 12.2 |
| S6.1 | THE Structure_Spec SHALL classify each of the 15 Components as exactly one of always-prese | 7.1 |
| S6.2 | WHERE a Component is optional, importing its package SHALL NOT import its optional library | 7.3 |
| S6.3 | IF code uses an optional Component whose Extra is not installed, THEN Skye SHALL raise `Mi | 7.3 |
| S6.4 | THE Structure_Spec SHALL keep one distribution with Extras (Assumption A2). | 7.1 |
| S6.5 | THE Structure_Spec SHALL limit the `skye/__init__.py` re-export set to exactly messages, c | 7.8 |
| S6.6 | THE Structure_Spec SHALL remove from `skye/__init__.py` any re-export that would import an | 7.8 |
| S6.7 | THE Structure_Spec SHALL retain the declared-but-minimal packages of Assumption A3. | history: all 15 packages exist |
| S7.1 | WHEN a fresh interpreter runs `import skye` in a core-only install, THE package SHALL NOT  | 7.4 |
| S7.2 | WHEN a fresh interpreter runs `import skye` in a core-only install, THE modules loaded SHA | 7.4 |
| S7.3 | THE Structure_Spec SHALL record that `skye/capabilities/remote_api.py` currently imports h | history: leak removed (7.7) |
| S7.4 | WHEN a known leak is resolved, its `known_leaks` entry SHALL be deleted; WHILE an entry re | 7.7 |
| S7.5 | IF `import skye` imports a `forbidden_at_import` library that is not an expected `known_le | 7.4 |
| S8.1 | THE Structure_Spec SHALL require that each Extra declare exactly the third-party libraries | 7.1 |
| S8.2 | THE Structure_Spec SHALL record that the `memory` Extra declares `psycopg2-binary`, which  | history: done, psycopg2-binary removed |
| S8.3 | THE Structure_Spec SHALL record that `memory` imports `redis.asyncio` and `asyncpg`, that  | history: done, memory extra is redis + asyncpg |
| S8.4 | THE Structure_Spec SHALL require that Extra declarations follow the dependency preference  | 7.2 |
| S8.5 | IF an Extra declares a library its Component does not import OR omits one it does, THEN TH | 7.1 |
| S9.1 | THE Structure_Spec SHALL assign each Component exactly one Codename: base=stratus, auth=oz | 8.1 |
| S9.2 | THE Structure_Spec SHALL require that each Codename match `^[a-z]{3,7}$`, that the mapping | 8.1 |
| S9.3 | THE Structure_Spec SHALL restrict Codename appearance to exactly four places: the `codenam | 8.2 |
| S9.4 | THE Structure_Spec SHALL prohibit a Codename from appearing anywhere else, including any i | 8.3 |
| S9.5 | THE Structure_Spec SHALL require a deterministic test asserting pattern, uniqueness, exact | 8.3 |
| S9.6 | THE Structure_Spec SHALL assign `vapor` to the `Runnable` Port and `nimbus` to the whole p | 8.4 |
| S10.1 | THE Structure_Spec SHALL record the two registries (`interfaces/route_registry.py` and `pr | history: overlap resolved in code |
| S10.2 | THE Structure_Spec SHALL record the two storage concepts (`interfaces/storage.py` and `rou | history: overlap resolved in code |
| S10.3 | THE Structure_Spec SHALL record the scattered cost, error, and token interfaces-and-implem | history: overlap resolved in code |
| S10.4 | THE Structure_Spec SHALL list every Overlap entry with exactly one intended resolution loc | history: overlap resolved in code |
| S10.5 | THE Structure_Spec SHALL record the planned spec renames as exactly eight mappings: skye → | history: spec renames, see spec-migration.md |
| S11.1 | THE Base_Package SHALL define a single `Runnable` Port declaring one invocation operation  | 5.1 |
| S11.2 | THE `agents`, `teams`, and `flows` implementation modules SHALL each declare a type confor | 5.1 |
| S11.3 | THE `models` Component SHALL implement `Runnable` for its model adapters, so a model is us | 5.1 |
| S11.4 | THE `teams` and `flows` modules SHALL reference composed units (models, agents, teams, flo | 5.1, 4.1 |
| S11.5 | IF a composition nests a unit within itself, directly or transitively, THEN THE composing  | 5.3 |
| S11.6 | WHEN the AST import test runs, it SHALL report any direct import among the `agents`, `team | 5.4 |
| S11.7 | THE role of a unit within a team (for example `supervisor`) SHALL be owned by `teams`, not | 5.2 |
| S12.1 | THE Structure_Spec SHALL require that each integration kind be added through exactly one e | 6.1 |
| S12.2 | WHERE a new model provider is added, it SHALL be configuration or a thin dialect within `m | 6.2 |
| S12.3 | WHERE a new store backend is added, it SHALL be exactly one new module in `store` implemen | 6.2 |
| S12.4 | WHERE a new tool, capability, or observability exporter is added, it SHALL be registered t | 6.2 |
| S12.5 | THE Structure_Spec SHALL require that adding any such integration introduce no import viol | 6.2 |
| S12.6 | IF adding an integration requires modifying a file in `base` or any Component other than t | 6.3 |
| S13.1 | THE Structure_Spec SHALL define exactly one Extra named `teams` and one named `flows`, eac | 7.6 |
| S13.2 | THE Structure_Spec SHALL record that `teams` and `flows` each declare zero third-party lib | 7.6 |
| S13.3 | WHERE `teams` or `flows` later needs a third-party library, the spec introducing it SHALL  | 7.6 |
| S13.4 | Installing the `teams` Extra SHALL exclude every library unique to `flows`, and vice versa | 7.6 |
| S13.5 | Core code SHALL work with neither Extra installed: `import skye` never imports `teams` or  | 7.6 |
| S14.1 | THE Structure_Spec SHALL declare every official vendor SDK used for validation in a develo | 9.4 |
| S14.2 | THE Structure_Spec SHALL provide differential tests that, for each backend with both a bui | 9.4 |
| S14.3 | THE differential tests SHALL run only where the SDKs are installed (development or CI); th | 9.4 |
| S14.4 | THE Structure_Spec SHALL NOT ship, declare as a runtime dependency, or require any officia | 9.3 |
| S14.5 | WHERE a differential test requires live credentials or network access that are unavailable | 9.4 |
| S15.1 | THE Structure_Spec SHALL place the MCP client inside the `tools` Component; it is not in ` | 10.1 |
| S15.2 | THE MCP client SHALL be tri-faceted: tools as Skye `Capability` objects (reusing the `tool | 10.1 |
| S15.3 | THE `Resource` type SHALL be internal to `tools`; no resource Port is defined in `base` an | 10.5 |
| S15.4 | THE built-in MCP client (a standard-library JSON-RPC-over-HTTP client) and the official `f | 10.4 |
| S15.5 | ANY official MCP/`fastmcp` protocol type (for example `mcp.types.Tool`, `mcp.types.Prompt` | 10.6 |
| S15.6 | THE conversion SHALL cover 100 percent of the fields and behaviors Skye consumes (Requirem | 10.6 |
| S15.7 | IF the conversion receives an official type whose required fields are absent or malformed, | 10.6 |
| S15.8 | THE implementation choice and the `mcp` Extra are governed by Requirement 21; `tools` SHAL | 10.7 |
| S16.1 | WHERE a Component offers both a built-in standard-library implementation and an external-l | 9.5 |
| S16.2 | THE external-library implementation SHALL convert every external input and output type int | 9.5 |
| S16.3 | IF an external-library type is exposed outside the owning Component, THEN THE Component SH | 9.5 |
| S16.4 | WHERE a Component has a single active implementation (model providers, Requirement 20) no  | 9.3 |
| S16.5 | THE rule governs the `models` Component (standard-library REST adapters, no SDK on the run | 9.5 |
| S16.6 | THE `agents` Component SHALL expose its multiple agent types (for example a ReAct agent) t | 6.1 |
| S17.1 | THE Structure_Spec SHALL place `policy` in the services Layer (Layer 2) alongside `guard`, | 2.3 |
| S17.2 | THE runtime Components (`gateway`, `agents`, `teams`, `flows`) SHALL have allowed-import s | 4.1 |
| S17.3 | THE four optional services SHALL be supplied to runtime Components only through Ports defi | 4.1 |
| S17.4 | THE Base_Package SHALL define an authorizer Port that accepts a principal identifier, an a | 4.2 |
| S17.5 | WHEN an authorizer Port is provided to the `gateway`, every capability listing and every c | 4.3 |
| S17.6 | `tests/budget/test_import_matrix.py` SHALL have its `LAYER` and `ALLOWED` data place `poli | 2.4 |
| S17.7 | IF any runtime package imports `policy`, `guard`, `observe`, or `memory`, THEN the import- | 4.4 |
| S18.1 | THE Structure_Spec SHALL define `auth` as the fifteenth Component, in Layer 0 next to `bas | 1.1, 2.1 |
| S18.2 | THE allowed imports of `auth` SHALL be `base` only; `auth` serves `models`, `store`, `tool | 11.1 |
| S18.3 | THE no-I/O and standard-library-only rules apply to `base`, not to `auth` (Requirement 2.4 | 3.2 |
| S18.4 | THE authentication Port SHALL be defined in `base`; the implementations are supplied by `a | 11.1 |
| S18.5 | THE `auth` package, the spec folder `.kiro/specs/auth`, the documentation section, and the | 1.2, 8.1 |
| S18.6 | THE `auth` Component SHALL contain: the authentication strategies (API key and bearer, Sig | 11.1 |
| S18.7 | THE credential sources SHALL include native support for the principal cloud secret manager | 11.1 |
| S18.8 | THE SigV4 signer currently at `models/transport/sigv4.py` SHALL move into `auth`. | 11.1 |
| S18.9 | THE Structure_Spec SHALL declare an `auth` Extra whose only third-party library is `rsa` ( | 11.4 |
| S18.10 | THE `auth` Component SHALL support only the documented, non-deprecated, non-interactive au | 11.7, 11.3, 11.5 |
| S18.11 | WHERE an authentication mode depends on an interactive login done earlier with a vendor co | 11.3 |
| S18.12 | THE design SHALL verify against each provider's current documentation at least these non-i | 11.9 |
| S18.13 | OUT OF SCOPE for `auth`: on-premises Active Directory (Kerberos, NTLM, ADFS), SAML, hardwa | 11.8 |
| S18.14 | `tests/budget/test_import_matrix.py` and the codename test (15 entries) SHALL reflect `aut | 2.4, 8.3 |
| S19.1 | THE Structure_Spec SHALL record that the project is renamed from Nimbus to Skye: import pa | D23, O1 |
| S19.2 | THE rename SHALL be executed last as its own task group, never implicitly before. | history: one-off migration, see skye-structure tasks group 10 |
| S19.3 | THE rename SHALL be a mechanical substitution covering: `src/nimbus` → `src/skye` and ever | history: one-off migration, see skye-structure tasks group 10 |
| S19.4 | THE GitHub repository rename SHALL be performed by the owner (the platform redirects the o | history: one-off migration, see skye-structure tasks group 10 |
| S19.5 | THE rename group's non-coding first task SHALL gate it: all previous task groups closed, t | history: one-off migration, see skye-structure tasks group 10 |
| S19.6 | THE definition of done SHALL be: `make budget-fast`, `make budget`, `make differential`, a | history: one-off migration, see skye-structure tasks group 10 |
| S20.1 | THE Structure_Spec SHALL require that each model provider have exactly one active implemen | 9.3 |
| S20.2 | THERE SHALL be no selection environment variable (for example `SKYE_IMPL`, `SKYE_<BACKEND> | 9.3 |
| S20.3 | WHERE a provider's built-in standard-library adapter does not yet exist, the provider SHAL | 9.3 |
| S20.4 | ANY vendor SDK adapter SHALL be either deleted or kept only as a bring-your-own example in | 9.3 |
| S20.5 | VENDOR SDKs SHALL remain only as development/test dependencies and as the differential tes | 9.4 |
| S20.6 | THE selection machinery SHALL be removed in a later task: `base/backend_select.py`, `base/ | history: machinery removed in code |
| S21.1 | THE built-in MCP client SHALL be the default and `fastmcp` an optional substitute chosen o | 10.3 |
| S21.2 | WHEN `impl` is omitted, THE factory SHALL return the built-in client; WHEN `impl="fastmcp" | 10.3 |
| S21.3 | IF `impl` is neither `"builtin"` nor `"fastmcp"`, THEN THE factory SHALL raise an error sa | 10.3 |
| S21.4 | IF `impl="fastmcp"` and `fastmcp` is not installed, THEN THE factory SHALL raise `MissingE | 10.3 |
| S21.5 | SELECTION SHALL use no environment variable, no configuration entry, and no fallback; the  | 10.4 |
| S21.6 | THE `mcp` Extra (providing `fastmcp`, own budget in `budgets.toml`) SHALL be a separate Ex | 10.7 |
| S21.7 | THE differential tests between the built-in MCP client and the `fastmcp` client SHALL stay | 10.4 |
| S21.8 | THE built-in MCP client SHALL be a consume-only client over HTTP transport with no stdio t | 10.2 |
| S22.1 | WHEN Skye receives messages or tool definitions in the OpenAI data shape, it SHALL accept  | 9.6 |
| S22.2 | SKYE data shapes SHALL NOT mirror, subclass, or re-export the classes of any vendor SDK cl | 9.6 |
| S22.3 | IF an input does not conform to the OpenAI data shape, THEN Skye SHALL reject it with an e | 9.6 |
| S22.4 | WHERE a user brings a vendor SDK, they write an adapter satisfying `Runnable` and pass it  | 9.7 |
| S23.1 | THE Structure_Spec SHALL require that provider credentials be read from each provider's st | 11.6 |
| S23.2 | THE Structure_Spec SHALL prohibit reading provider credentials from any Skye-prefixed vari | 11.6 |
| S23.3 | THE Skye-prefixed environment variables SHALL be exactly three: `SKYE_LOG_LEVEL`, `SKYE_CO | 11.6 |
| S23.4 | IF this spec references any other Skye-prefixed variable, THEN it SHALL be treated as non- | 11.6 |
| S23.5 | THE bounded set fixes the scope of the rename (Requirement 19): exactly these three are re | history: scope of the rename, one-off |
| S23.6 | THE rule of Requirement 16 (no vendor SDK or `mcp`/`fastmcp` type outside its owning Compo | 9.5 |
| S24.1 | THE project SHALL be MIT-licensed, with a `LICENSE` file at the repository root stating th | 14.1 |
| S24.2 | THE project SHALL NOT contain code or documentation text copied from another project witho | 14.1 |
| S24.3 | WHERE the `prompts` Component reuses the design of liteprompt or anything taken from promp | 14.2 |
| S24.4 | THE project SHALL NOT copy from a source under a licence incompatible with MIT (for exampl | 14.2 |
| S24.5 | PROMPT templates shipped in the project SHALL be written for Skye or carry the licence of  | 14.3 |
| S25.1 | THE repository SHALL contain a continuous-integration workflow (`.github/workflows/budgets | 7.5 |
| S25.2 | THE budget CI gate SHALL fail the pull request when any limit in `budgets.toml` is exceede | 7.5 |
| S25.3 | THE budget limits SHALL live in `budgets.toml` as the single source of truth, consumed ide | 7.5 |
| S25.4 | THE Structure_Spec SHALL NOT weaken a budget limit to make a failing change pass; a limit  | 7.5 |
| S26.1 | THE `known_leaks` list in `budgets.toml` SHALL be empty, the `httpx`/`requests` leak havin | 7.7 |
| S26.2 | THE `known_import_failures` list in `budgets.toml` SHALL be empty, the former `skye.capabi | 7.7 |
| S26.3 | WHILE a `known_leaks` or `known_import_failures` entry is tracked, THE Budget_Tests SHALL  | 7.7 |
| S26.4 | IF a listed entry starts working again (a leak reappears or a tracked failure is fixed but | 7.7 |
| S27.1 | THE target `prompts` Component SHALL reuse the liteprompt design — loaders, role-based mes | 13.1 |
| S27.2 | THE target `prompts` Component SHALL NOT depend on a compiled template engine; where templ | 13.1 |
| S27.3 | THE Structure_Spec SHALL record that `jinja2` is currently still a core dependency and tha | 13.2 (done, D20) |
| S27.4 | WHEN the Jinja2 removal is executed, THE `jinja2` dependency SHALL be removed from the cor | 13.2 |

## skye (base)

| Source | Text (start) | Now |
|---|---|---|
| B1.1 | THE skye library SHALL provide a ModelInterface that defines methods for model invocation, | 16.1 |
| B1.2 | THE skye library SHALL provide a PromptBuilderInterface that defines methods for template  | 16.1 |
| B1.3 | THE skye library SHALL provide a CapabilityInterface that defines methods for capability r | 16.1 |
| B1.4 | THE skye library SHALL provide a MemoryInterface that defines methods for storing and retr | 16.1 |
| B1.5 | THE skye library SHALL provide a SafetyFilterInterface that defines methods for input and  | 16.1 |
| B2.1 | THE skye library SHALL provide a unified interface for accessing multiple LLM providers in | 9.9 |
| B2.2 | WHEN a developer specifies a model identifier, THE skye library SHALL route the request to | 9.9 |
| B2.3 | THE skye library SHALL support synchronous completion requests across all supported provid | 9.9 |
| B2.4 | THE skye library SHALL support streaming completion requests across all supported provider | 9.9 |
| B2.5 | WHEN a provider call fails, THE skye library SHALL return standardized error information i | 9.9 |
| B3.1 | THE skye library SHALL accept model configuration including provider, model identifier, te | 17.1 |
| B3.2 | THE skye library SHALL support multiple model configurations for the same logical model na | 17.1 |
| B3.3 | WHEN a primary model configuration fails, THE skye library SHALL attempt fallback configur | 17.2 |
| B3.4 | THE skye library SHALL track which model configuration was used for each request | 17.2 |
| B3.5 | THE skye library SHALL expose model configuration metadata for observability purposes | 17.2 |
| B4.1 | THE skye library SHALL return completion responses in a standardized format with message c | 16.4 |
| B4.2 | THE skye library SHALL include token usage information in all completion responses | 16.4 |
| B4.3 | THE skye library SHALL include model identifier and provider information in all completion | 16.4 |
| B4.4 | WHEN streaming is enabled, THE skye library SHALL yield response chunks in a standardized  | 16.5 |
| B4.5 | THE skye library SHALL normalize provider-specific response fields to a common schema | 16.4 |
| B5.1 | THE skye library SHALL provide a PluginInterface that defines lifecycle hooks for initiali | 16.1 |
| B5.2 | THE skye library SHALL provide an ObserverInterface that defines methods for logging event | 16.1 |
| B5.3 | THE skye library SHALL provide a StorageAdapterInterface that defines methods for data per | 16.1 |
| B5.4 | WHEN a plugin implements a core interface, THE skye library SHALL validate interface compl | 16.2 |
| B5.5 | THE skye library SHALL allow plugins to be registered and discovered dynamically | 16.3 |
| B6.1 | THE skye library SHALL define a SkyeError base class for all Skye-specific exceptions | 18.1 |
| B6.2 | THE skye library SHALL define specific exception types for provider errors, configuration  | 18.1 |
| B6.3 | WHEN an LLM provider returns an error, THE skye library SHALL wrap it in a ProviderError w | 18.1 |
| B6.4 | THE skye library SHALL include the original error message and stack trace in all wrapped e | 18.2 |
| B6.5 | THE skye library SHALL log all exceptions with appropriate severity levels | 18.2 |
| B7.1 | THE skye library SHALL calculate token usage for all completion requests including prompt  | 19.1 |
| B7.2 | THE skye library SHALL estimate costs based on provider pricing when pricing data is avail | 19.2 |
| B7.3 | THE skye library SHALL include token usage and cost estimates in completion response metad | 19.1 |
| B7.4 | THE skye library SHALL support custom pricing configurations for private or custom models | 19.2 |
| B7.5 | THE skye library SHALL aggregate token usage across multiple requests when requested | 19.3 |
| B8.1 | THE skye library SHALL load configuration from environment variables with a SKYE_ prefix | 11.6 (superseded: three variables only, D18) |
| B8.2 | THE skye library SHALL support configuration through Python dictionaries passed at initial | 20.1 |
| B8.3 | THE skye library SHALL support configuration through YAML or JSON configuration files | 20.1 |
| B8.4 | WHEN multiple configuration sources are present, THE skye library SHALL apply them in orde | 20.2 |
| B8.5 | THE skye library SHALL validate all configuration values and raise ConfigurationError for  | 20.3 |
| B9.1 | THE skye library SHALL emit structured log events for all model invocations with request a | 18.3 |
| B9.2 | THE skye library SHALL provide hooks for custom telemetry implementations to capture event | 18.4 |
| B9.3 | THE skye library SHALL include correlation IDs in all log events to trace requests across  | 18.3 |
| B9.4 | THE skye library SHALL support log level configuration per component | 18.3 |
| B9.5 | WHEN a telemetry plugin is registered, THE skye library SHALL invoke telemetry hooks for a | 18.4 |
| B10.1 | THE skye library SHALL provide complete type hints for all public APIs using Python typing | 21.1 |
| B10.2 | THE skye library SHALL use Pydantic models for all configuration and data structures | 21.2 (superseded: dataclasses, D24) |
| B10.3 | WHEN invalid data is provided to a Pydantic model, THE skye library SHALL raise a Validati | 21.3 |
| B10.4 | THE skye library SHALL validate all interface implementations at runtime to ensure contrac | 16.2 |
| B10.5 | THE skye library SHALL support Python 3.10 and higher versions | 21.1 |

## skye-consolidation

| Source | Text (start) | Now |
|---|---|---|
| C1.1 | WHEN the system references tool-related functionality THEN it SHALL use "Capability" termi | 22.1 |
| C1.2 | WHEN class names are defined for tool functionality THEN they SHALL use the "Capability" p | 22.1 |
| C1.3 | WHEN documentation references tools THEN it SHALL use "capability" terminology exclusively | 22.1 |
| C1.4 | WHEN variable names reference tools THEN they SHALL use "capability" naming conventions ex | 22.1 |
| C1.5 | WHEN the codebase is scanned THEN there SHALL be zero occurrences of "Tool" terminology in | 22.2 |
| C2.1 | WHEN a YAML configuration file is provided THEN the Router SHALL load route configurations | 17.3 |
| C2.2 | WHEN environment variables are referenced in YAML using ${VAR_NAME} syntax THEN the Router | 20.4 |
| C2.3 | WHEN a YAML file contains model targets with API keys THEN the Router SHALL support enviro | 17.4 |
| C2.4 | WHEN a YAML file is invalid THEN the Router SHALL raise a clear ConfigurationError with de | 17.3 |
| C2.5 | WHEN no YAML file is provided THEN the Router SHALL continue to work with programmatic con | 17.3 |
| C3.1 | WHEN tests are organized THEN they SHALL follow a clear structure separating unit, integra | 23.1 |
| C3.2 | WHEN capability functionality is tested THEN tests SHALL cover all major code paths | 23.2 |
| C3.3 | WHEN router functionality is tested THEN tests SHALL cover all routing strategies | 23.2 |
| C3.4 | WHEN provider functionality is tested THEN tests SHALL cover all supported providers | 23.2 |
| C3.5 | WHEN tests are run THEN they SHALL achieve at least 80% code coverage on core functionalit | 23.2 |
| C4.1 | WHEN examples are provided THEN they SHALL be organized by feature category | 24.1 |
| C4.2 | WHEN capability examples are provided THEN they SHALL demonstrate all capability types | 24.2 |
| C4.3 | WHEN router examples are provided THEN they SHALL demonstrate YAML configuration | 24.2 |
| C4.4 | WHEN provider examples are provided THEN they SHALL demonstrate all supported providers | 24.2 |
| C4.5 | WHEN examples are accessed THEN they SHALL include clear README documentation | 24.1 |
| C5.1 | WHEN steering documents are read THEN they SHALL accurately reflect the current codebase s | 15.8 |
| C5.2 | WHEN naming conventions are documented THEN they SHALL match actual implementation | 15.8 |
| C5.3 | WHEN configuration patterns are documented THEN they SHALL include YAML examples | 15.8 |
| C5.4 | WHEN the package structure is documented THEN it SHALL match the actual src/ directory lay | 15.8 |
| C5.5 | WHEN examples are referenced THEN they SHALL point to existing example files | 15.8 |
| C6.1 | WHEN a ModelTarget is created with api_key="${ENV_VAR}" THEN the Router SHALL substitute t | 17.4 |
| C6.2 | WHEN environment variable substitution is used THEN it SHALL support the ${VAR_NAME} synta | 17.4 |
| C6.3 | WHEN an environment variable is not found THEN the Router SHALL raise a clear Configuratio | 17.4 |
| C6.4 | WHEN environment variable substitution is used THEN it SHALL work for all string fields in | 17.4 |
| C6.5 | WHEN environment variables are substituted THEN the Router SHALL log the substitution at D | 17.4 |
| C7.1 | WHEN stress tests are run THEN they SHALL test concurrent request handling | 23.3 |
| C7.2 | WHEN stress tests are run THEN they SHALL test rate limiting under load | 23.3 |
| C7.3 | WHEN stress tests are run THEN they SHALL test router failover scenarios | 23.3 |
| C7.4 | WHEN stress tests are run THEN they SHALL test capability execution under concurrent load | 23.3 |
| C7.5 | WHEN stress tests complete THEN they SHALL report performance metrics | 23.3 |
| C8.1 | WHEN tests are organized THEN unit tests SHALL be in tests/unit/ organized by module | 23.1 |
| C8.2 | WHEN tests are organized THEN integration tests SHALL be in tests/integration/ organized b | 23.1 |
| C8.3 | WHEN tests are organized THEN stress tests SHALL be in tests/stress/ with clear naming | 23.1 |
| C8.4 | WHEN tests are organized THEN fixtures SHALL be in tests/fixtures/ and reusable | 23.1 |
| C8.5 | WHEN tests are organized THEN each test file SHALL have a clear docstring explaining its p | 23.1 |
| C9.1 | WHEN a provider client transforms requests THEN all provider-specific logic SHALL be conta | 9.10 |
| C9.2 | WHEN capability transformations occur THEN the CapabilityTransformer SHALL delegate to pro | 9.10 |
| C9.3 | WHEN message transformations occur THEN the MessageTransformer SHALL delegate to provider- | 9.10 |
| C9.4 | WHEN core library code processes requests THEN it SHALL use only provider-agnostic Skye mo | 9.10 |
| C9.5 | WHEN a new provider is added THEN no changes SHALL be required to core library code outsid | 9.10 |
| C9.6 | WHEN router code handles requests THEN it SHALL remain completely provider-agnostic | 9.10 |
| C9.7 | WHEN capability code handles tool calls THEN it SHALL remain completely provider-agnostic | 9.10 |
| C9.8 | WHEN completion models are used THEN they SHALL remain completely provider-agnostic | 9.10 |

## wiki (original criteria, summarized)

| Source | Text (start) | Now |
|---|---|---|
| W1.1 | one docs section per component | 15.5, 1.2 |
| W1.2 | migrate each existing flat page into its section | task: skye-structure group 11 |
| W1.3 | codename line under each section index | 8.2 |
| W1.4 | no codename outside the four places | 8.2 |
| W2.1 | one glossary with the 15 codenames | 8.1, 15.7 |
| W2.2 | two watermarks listed apart | 15.7, 8.4 |
| W2.3 | auth versus policy contrast | 15.7 |
| W3.1 | wiki governs documentation only | 15.1 |
| W3.2 | component and codename rules owned elsewhere, referenced | 15.1 |
