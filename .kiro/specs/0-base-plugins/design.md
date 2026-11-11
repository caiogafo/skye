Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, Extension points, Plugins and provider profiles, Public API and lazy imports, Extras and budgets)

# Design Document: plugins

## Overview
`0-base-plugins` is the cross-cutting spec of decisions D107 and D108: one way for a third party to add any kind of integration to Skye
without changing it, and one place for the knowledge that belongs to a provider or to the store. It has no component of its own. The
Ports, the registrar and the profile live in `base`; the scan of installed plugins lives in `utils`; each kind keeps its owner
(`models`, `store`, `auth`, `router`, `tools`, `prompts`, `agents`), which registers its built-ins through the registrar and ships the
conformance function of the kind. The layer, the allowed imports, the Port rules and the extras policy are in the steering sections
named above and are not restated here.

The work has two halves on one mechanism (Requirements 56 to 61 of steering):
1. **The plugin door.** A plugin is an object with `register(registrar)`; the registrar has one method per kind; installed plugins are
   found through the entry-point group `skye.plugins`, lazily, at the first name a lookup does not know; `skye.use(plugin)` registers
   one explicitly; the configuration key `plugins` limits what the scan loads; `skye plugins` lists everything.
2. **One home per kind of knowledge.** A provider registers a `ProviderProfile` with its class, and cost, token counting, the router and
   `auth` read the profile instead of their own tables. The store gains the two reads the router needs (`count`, remaining lifetime),
   so the router no longer knows how a counter is stored or how expiry works.

Order of work (D108): the provider profile and its registrar methods (Requirements 59 and 60.1 to 60.8), then the store (60.9 to 60.12),
then the closed kinds (58). The example of Requirement 61.1 is written first, before any component changes.

## Current state
Scan of 2026-11-11 (`docs/_notes/extension-points-scan.md`, a working note, not part of the spec):
- `base/interfaces/plugin.py` defines `PluginInterface` (an ABC with `initialize`, `shutdown`, `get_metadata`); nothing loads or calls it.
- Six registries, each with its own shape: `ProviderRegistry` (`models/registry.py`, class attributes), `register_backend`
  (`store/factory.py`, with the `_BUILTIN` table of `"module:attribute"` texts), `register_credential_source` (`auth/registry.py`, with
  `BUILTIN_SOURCES`), `CapabilityRegistry` (`tools/registry.py`), `TokenCounter.register_tokenizer` (`models/transport/token_counter.py`),
  `register_agent_type` (`agents/registry.py`). Prompt filters are registered per builder instance (`prompts/messages.py`).
- Three kinds are closed: routing strategies (the `RoutingStrategy` enum and an `if`/`elif` chain in `router/routing_strategies.py`), MCP
  client implementations (`impl == "builtin" | "fastmcp"` in `tools/mcp_client.py`), decision models (Jev only, no registry).
- Provider knowledge outside the provider (P1 to P6 of the note): the `PRICING` table of `CostCalculator`; three tables of API-key
  variables (`STANDARD_ENV_VARS` in `auth`, `API_KEY_VARIABLES` in `router/skye_file.py`, names written in the adapters); the Azure branch
  of `router/model_router.py`; one error handler per provider in `models/transport/error_mapping.py`; `gemini_schema` in
  `models/transport/structured.py`; the AWS region decided in four places with two different defaults. Since D109 the list of Claude
  models that refuse a forced choice is written in the Anthropic and the Bedrock adapters (an adapter imports no other adapter).
- Storage knowledge outside the store (S1 to S3): the router reads `{"count": n}`, keeps a cooldown as `cooldown_until` compared with
  `time.time()`, and imports `InMemoryBackend` as its default.

## Architecture
```
base/interfaces/plugin.py   PluginInterface (Protocol: name, register), RegistrarInterface (Protocol: one method per kind)
base/plugins.py             Registrar: the in-memory tables, one per kind; lookup with one lazy scan; the default registrar
base/profile.py             ProviderProfile, ModelProfile, RegionRule (frozen dataclasses); find_model_profile; resolve_region
base/interfaces/storage.py  CounterStore.count; ExpiryStore (is_alive, remaining) next to KeyValueStore, CounterStore, ScanStore
utils/plugins.py            discover(registrar): scan of the entry-point group `skye.plugins`, the `plugins` allowlist, the report
utils/cli.py                `skye plugins [--format json]`
skye/__init__.py            `use` (lazy name, Requirement 7.8)
<owner>/_plugin.py          the built-in plugin of each owner: register(registrar) with "module:attribute" texts
<owner>/conformance.py      check_<kind> of the kinds it owns (store: check_backend exists, D98)
```
`base` holds data, Protocols and in-memory tables, and does no I/O (Requirement 3). The scan reads the metadata of installed
distributions, which is I/O, so it is in `utils`; the registrar holds the text `"skye.utils.plugins:discover"` and imports it at the
first miss, as `auth` and `store` already do with their built-in tables (O60, option A). Owners import `base` only, as the matrix
allows; no owner imports `utils`.

## Components and Interfaces

### The registrar (Requirement 56)
- `RegistrarInterface` has eleven methods: `model_provider`, `embedding_provider`, `store_backend`, `credential_source`,
  `routing_strategy`, `mcp_client`, `decision_model`, `tokenizer`, `capability`, `prompt_filter`, `agent_type`. Each takes
  `(name, target, *, replace=False)`; `model_provider` and `embedding_provider` also take `profile=` (Requirement 59.7).
- `target` is the object, a factory, or a `"module:attribute"` text that is imported at the first use of the name, never at
  registration (56.5). The built-ins register as texts, so registering them costs no import.
- A second registration of a name for the same kind raises `ConfigurationError` naming the kind and the name, unless `replace=True`
  (56.4). Two different profiles for one provider name raise the same way (59.8); the same profile given twice is accepted.
- One default `Registrar` per process, in memory only: no file, no thread, nothing that must survive an invocation (56.3, D27). Tests
  build their own `Registrar()` and pass it, so they do not touch the default.
- The registries of today become views (56.7): `ProviderRegistry.register_model_provider(name, cls)` calls
  `registrar.model_provider(name, cls)`, `ProviderRegistry.get_model_provider(name)` calls the registrar's lookup, and so on for
  `register_backend`, `register_credential_source`, `CapabilityRegistry`, `TokenCounter.register_tokenizer`, `register_agent_type`. Their
  signatures do not change; their tables are removed. `CapabilityRegistry` keeps its instances: the registrar holds the default set, as
  for prompt filters (56.8), and a registration on an instance stays local to it.
- Built-ins use the same door (56.6): each owner has `_plugin.py` with `register(registrar)`, and the default registrar calls the
  built-in plugins of the owners on the first lookup of any of their kinds. It knows them as a fixed tuple of texts, not by import.

### The plugin Port (Requirement 56.1; O61)
`PluginInterface` becomes a `Protocol` with `name: str` and `register(registrar) -> None`. The lifecycle methods go (O61, option A,
recommended: nothing calls them and serverless has no long-lived process). `skye.use` also accepts a plain function of one parameter.
`skye.interfaces` keeps exporting the name, so an import still works; a class written against the old ABC must change, which is accepted
while the version is 0.x.

### Discovery and control (Requirement 57)
- **Lookup.** `registrar.get(kind, name)` looks in the table; on a miss, and only the first time in the process, it imports
  `skye.utils.plugins:discover`, calls it with itself, and looks once more (57.1, 57.2). `import skye` scans nothing and loads no plugin
  (57.3); the lazy names of `skye/__init__.py` do not change.
- **Scan.** `discover` reads `importlib.metadata.entry_points(group="skye.plugins")`. Each entry point is loaded and its object passed to
  `use`. A failure (load or `register`) is logged once at WARNING with `extra={"entry_point", "distribution", "error"}` and the scan
  goes on (57.6, D105). The scan keeps a report (name, distribution, version, loaded or the error, the names registered per kind) for
  `skye plugins` and for the error of 57.7.
- **Allowlist.** When the configuration file has `plugins = [...]`, only those entry-point names are loaded; without the key, all are
  (57.5). The key is read with `skye.utils.config_files.load_config`, the reader of D91; the key goes back into the configuration
  schema that D106 cleaned (it was removed only because no code read it).
- **Explicit.** `skye.use(plugin)` calls `plugin.register(registrar)` at once; a function of one parameter is called directly. An
  exception in `register` becomes a `ConfigurationError` naming the plugin, with the cause kept (57.4, 57.8).
- **Unknown name.** After the scan, a miss raises `ConfigurationError` listing the names of that kind and the failures of the scan (57.7).
- **Command.** `skye plugins` prints the built-in registrations and each entry point with its distribution, version, status and names
  per kind; `--format json` prints the same as one JSON object (57.9). It runs the scan, so it also shows what a lookup would load.

### The provider profile (Requirement 59)
```python
@dataclass(frozen=True)
class ModelProfile:
    prompt_price: float | None = None        # USD per 1M tokens
    completion_price: float | None = None
    tokenizer: str | None = None             # a name registered with registrar.tokenizer
    message_overhead: int = 0                # tokens added per message
    info: Mapping[str, Any] = {}             # merged into get_model_info(), e.g. supports_structured_output

@dataclass(frozen=True)
class RegionRule:
    variables: tuple[str, ...]               # e.g. ("AWS_REGION", "AWS_DEFAULT_REGION")
    required: bool = True

@dataclass(frozen=True)
class ProviderProfile:
    name: str
    api_key_variables: tuple[str, ...] = ()  # read in order; the provider-standard names (Requirement 11.6)
    region: RegionRule | None = None
    default_api_base: str | None = None
    client_settings: Mapping[str, str] = {}  # generic setting -> provider name, e.g. {"api_base": "azure_endpoint"}
    model_is_deployment: bool = False        # Azure: the model name is the deployment
    models: Mapping[str, ModelProfile] = {}
    map_error: Callable[..., ProviderError] | str | None = None  # or "module:attribute"
```
(Mappings are given with `field(default_factory=...)` and frozen as `MappingProxyType`.)
- `find_model_profile(profile, model)`: the exact name first, then the longest registered name followed by a date or version suffix
  (`-2024-08-06`, `-20240620`, `-v1:0`, `@001`); `gpt-4o` never matches `gpt-4` (59.4). One function, in `base/profile.py`.
- `resolve_region(rule, passed=None, authenticator=None)`: the region passed, then the authenticator's, then the variables in order; a
  required rule with no region raises `ConfigurationError` naming the variables; there is no default region (59.5, 59.6).
- A provider with no profile, or a model missing from it, is not an error: the cost is unknown (`None`), the token count is the
  standard-library estimate, and `get_model_info()` returns what the adapter knows (59.10).
- An OpenAI-compatible endpoint is a plugin with no class: `registrar.model_provider("acme", OpenAICompatibleProvider,
  profile=ProviderProfile("acme", ("ACME_API_KEY",), default_api_base="https://api.acme.example/v1"))` (59.9).
- The model facts of D109 (which Claude models refuse a forced choice) become `ModelProfile.info["supports_forced_capability_choice"]`
  in the Anthropic and Bedrock profiles, and `refuses_forced_choice` reads `get_model_info()`; the two adapter tuples go.

### Provider knowledge in one place (Requirement 60.1 to 60.8)
| Today | After |
|---|---|
| `CostCalculator.PRICING` | prices in each built-in `ModelProfile`; `add_custom_pricing` writes a user layer that wins; `get_pricing`, `pricing_for`, `list_models` read profiles then the layer (60.1) |
| prefixes, tokenizers and overheads in `TokenCounter` | `tokenizer` and `message_overhead` of the `ModelProfile`; `register_tokenizer` registers a tokenizer by name (60.2, 59.3) |
| `STANDARD_ENV_VARS`, `API_KEY_VARIABLES`, names in adapters | `ProviderProfile.api_key_variables`, read by `auth`, the router's `.skye` reader and the adapters (60.3) |
| `if target.provider == "azure"` in the router | `client_settings` and `model_is_deployment` of the target's profile; the router names no provider (60.4) |
| handlers per provider in `error_mapping.py`; `gemini_schema` in `structured.py` | each in its adapter module, referenced by `map_error`; `error_mapping.py` keeps the HTTP-status mapping of D104 and calls `map_error` (60.5) |
| region in `auth/aws.py`, `auth/sts.py`, `models/transport/credentials.py`, the boto3 chain | `resolve_region` everywhere (60.6); the store passes the region it finds and leaves boto3's chain as the last step (O63.2, option A) |
| `_native_json_output` in Bedrock | `get_model_info()["supports_structured_output"]` from the profile (60.7) |

`tests/budget/test_provider_knowledge.py` fails on a built-in provider name, a key variable or a price used as a literal outside the
adapter and profile of that provider, with an allowlist that only shrinks, in the style of `test_provider_agnostic_core.py` (60.8).

### Storage knowledge in one place (Requirement 60.9 to 60.12)
- `CounterStore.count(key) -> int`: the count, 0 when absent or expired. Every backend implements it; `check_backend` checks it (60.9).
- `ExpiryStore` (a capability Protocol beside those of D98): `is_alive(key) -> bool` and `remaining(key) -> float | None` (seconds, `None`
  for no expiry or absent). Each backend computes it from the expiry it already stores and its clock (60.10).
- The router keeps a cooldown as `set(key, {}, ttl=seconds)` and asks `is_alive`; it never compares a stored time with `time.time()`,
  so `FakeClock` drives its tests (closes S2). It reads counters with `count` (closes S1) and creates its default store with
  `skye.store.backend("memory")` (60.11, closes S3).
- Namespaces (O63.1, option A, recommended): `store.namespaced(store, "router")` prefixes every key, and each component uses its own.
- `tests/budget/test_storage_knowledge.py` fails on the import of a concrete backend class outside `store` and its tests, and on reading
  the key `"count"` of a stored value outside `store` (60.12).

### The closed kinds (Requirement 58)
- **Routing strategies.** `RoutingStrategySelector` asks the registrar for the strategy by name; the eight built-ins register in
  `router/_plugin.py`; every `RoutingStrategy` member stays valid as a name; the `if`/`elif` chain goes (58.1). The `.skye` checker
  accepts a registered name in `strategy` (its enum check becomes a registry check, with the built-in names in the schema).
- **MCP clients.** `impl` is a registrar name; `"builtin"` stays the default (D16); `"fastmcp"` registers as text and imports `fastmcp`
  only when chosen (58.2, Requirement 10.7).
- **Decision models.** `models` creates one by name through the registrar; Jev registers as a built-in (58.3).
- A Port of a planned component (content reader, observer, safety filter, authorizer, memory) gets its registrar method in the change that
  gives it a registry (58.6).

### Conformance (Requirement 58.4, 58.5)
Each owner ships `check_<kind>` next to the kind: offline, against fakes, returning the names of the checks passed and raising an error
that names the first that fails. `skye.store.check_backend` is the model. Kinds and owners: `check_model_provider` and
`check_embedding_provider` (`models`; a fake transport, the Port shape, the profile valid), `check_credential_source` (`auth`),
`check_routing_strategy` (`router`), `check_mcp_client` (`tools`), `check_decision_model` (`models`, the D-rule of Requirement 9.8),
`check_tokenizer` (`models`), `check_capability` (`tools`), `check_prompt_filter` (`prompts`), `check_agent_type` (`agents`). One
parametrized test runs every built-in registration of every kind through its function.

## Data Models
`ProviderProfile`, `ModelProfile`, `RegionRule` above; the scan report is a list of dataclasses `PluginReport(name, distribution,
version, loaded, error, registered: dict[kind, list[name]])`, printed by `skye plugins`. Nothing is persisted.

## Error Handling
All registration and lookup errors are `ConfigurationError` with `details` (kind, name, the names known, the scan failures). A plugin that
fails to load is logged once and skipped (57.6); a plugin passed to `use` that fails is raised (57.8). `resolve_region` raises
`ConfigurationError` naming the variables. A `map_error` given as text that does not import raises `ConfigurationError` at the first
error it should map, with the cause kept.

## Testing Strategy
- `tests/unit/plugins/`: the registrar (each kind, duplicate names, `replace`, lazy text targets, views of the old registries), `use`
  (object, function, failing `register`), discovery with a fake `entry_points` (one scan per process, the allowlist, a failing entry
  point, the error after the scan), `skye plugins` text and JSON, `find_model_profile` and `resolve_region`.
- `tests/unit/store/`: `count` and `ExpiryStore` in the conformance suite, for all six backends.
- `tests/unit/router/`: cooldown and counters with `FakeClock`, no `time.time()`; strategies by name; a registered custom strategy.
- `tests/budget/`: `test_provider_knowledge.py`, `test_storage_knowledge.py`; import time and cold start unchanged; `import skye` loads no
  entry point (a fake entry point that raises on load proves it).
- `tests/examples`: `examples/plugins/` runs offline (61.1).

## Correctness Properties

### Property 1: One door
Every kind is registered through `RegistrarInterface`; built-ins and third-party plugins make the same calls.

**Validates: Requirements 1.2, 1.6**

### Property 2: Lazy
`import skye` scans nothing and imports no plugin or built-in target; a text target is imported only at its first use.

**Validates: Requirements 1.5, 2.3**

### Property 3: One scan
The entry-point group is read at most once per process, whatever the number of misses.

**Validates: Requirements 2.2**

### Property 4: No silent override
A second registration of a name, or a second different profile for a provider, fails unless `replace=True`.

**Validates: Requirements 1.4, 4.8**

### Property 5: One home
No provider name, key variable or price appears as a literal outside its adapter and profile; no backend class or stored shape is read outside `store` (the two budget tests).

**Validates: Requirements 5.8, 5.12**

### Property 6: Profile lookup is total
For any provider and model, the cost is a number or `None`, the token count is a number, and neither raises for a missing profile.

**Validates: Requirements 4.10**

### Property 7: Time is the store's
No router behaviour depends on `time.time()`; every time-dependent path is driven by the store's clock.

**Validates: Requirements 5.10**

### Property 8: Compatible
Every call to the registries of today, and every `RoutingStrategy` name, works as before.

**Validates: Requirements 1.7, 3.1**

## Open points (not decided here)
- O59 sub-questions the owner has not taken (the spec follows the recommended options; a different answer changes the section named):
  discovery (lazy entry points and `use`, both), control (`plugins` allowlist), the plugin object (`register(registrar)`).
- O60: where the scan lives. The design uses option A (`utils/plugins.py`, imported by text from `base`).
- O61: `PluginInterface` without its lifecycle. The design uses option A.
- O62: `base/openai_shape.py` stays in `base` (option A); no change in this spec.
- O63: namespaces with `store.namespaced` (1, option A) and the store region through `resolve_region` with boto3's chain last (2, option A).
