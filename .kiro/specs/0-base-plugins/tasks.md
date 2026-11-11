# Implementation Plan: plugins

## Overview
Milestones in the order of decision D108: the example first (Requirement 61.1), then the Ports, the registrar and the provider profile
in `base`, discovery, the built-in providers on the registrar with their profiles and the removal of the scattered provider knowledge,
then the store, then the closed kinds, the conformance functions, the documentation and the final checkpoint. Status is judged from the
code and the tests. Each task cites the steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the
decision it honors. Task IDs cited from other documents are `plugins:N.k`. A task that depends on an open point of `design.md` (O59 to
O63) says so; the tasks follow the recommended option of each, and a different answer from the owner changes only the task named.

The token-counter work of `1-adapters-models` uses the field names of Requirement 59.2; task 6.2 takes over what is left of it.

## Tasks
- [ ] 1. The example, before any component changes
  - [ ] 1.1 Write `examples/plugins/` against the planned API: a provider registered with `OpenAICompatibleProvider` and a
    `ProviderProfile`, a store backend, `skye.use(plugin)`, and the `[project.entry-points."skye.plugins"]` declaration in a
    `pyproject.toml` of the example; a `README.md` with the reading order. No network and no key.
    - _Requirements: 61.1, 24.4, 24.8_
  - [ ] 1.2 Add the example to `tests/examples`, marked expected-to-fail until task 4 is done, then unmarked by the task that makes it pass
    - _Requirements: 61.1, 24.11_

- [ ] 2. Ports and registrar in `base`
  - [ ] 2.1 `PluginInterface` as a `Protocol` with `name` and `register(registrar)`; remove `initialize`, `shutdown` and `get_metadata`;
    keep the name exported by `skye.interfaces` (depends on O61, option A)
    - _Requirements: 56.1; D37_
  - [ ] 2.2 `RegistrarInterface` with the eleven methods of Requirement 56.2, each `(name, target, *, replace=False)`, and `profile=`
    on `model_provider` and `embedding_provider`; the docstring footer of a Port (error contract)
    - _Requirements: 56.2, 59.7, 16.8_
  - [ ] 2.3 `base/plugins.py`: `Registrar` with one in-memory table per kind, `get(kind, name)`, `names(kind)`, the default registrar;
    no file, no thread
    - _Requirements: 56.3; D27_
  - [ ] 2.4 Duplicate names and profiles: `ConfigurationError` naming the kind and the name, `replace=True` overrides; the same profile
    given twice is accepted
    - _Requirements: 56.4, 59.8_
  - [ ] 2.5 `"module:attribute"` targets imported at the first use of the name, never at registration; a text that does not import
    raises `ConfigurationError` with the cause
    - _Requirements: 56.5_
  - [ ] 2.6 Tests in `tests/unit/plugins/test_registrar.py`: each kind, duplicates, `replace`, lazy text targets, a private `Registrar()`
    that leaves the default untouched; the Port compliance test gains the pair `Registrar` / `RegistrarInterface`
    - _Requirements: 56.1 to 56.5, 16.7_

- [ ] 3. The provider profile in `base`
  - [ ] 3.1 `base/profile.py`: `ProviderProfile`, `ModelProfile`, `RegionRule` as frozen dataclasses with the fields of Requirements 59.1
    and 59.2; mappings frozen; prices and overhead validated (0 or more)
    - _Requirements: 59.1, 59.2_
  - [ ] 3.2 `find_model_profile`: exact name, then the longest registered name followed by a date or version suffix; tests that
    `gpt-4o` never matches `gpt-4` and that dated and Bedrock-versioned names find their family
    - _Requirements: 59.4_
  - [ ] 3.3 `resolve_region`: passed, authenticator, variables in order; `ConfigurationError` naming the variables when a required
    region is missing; no default region
    - _Requirements: 59.5, 59.6_
  - [ ] 3.4 Property tests: a lookup never raises for a missing profile or model (cost `None`, the estimate for tokens)
    - _Requirements: 59.10_

- [ ] 4. Discovery and control
  - [ ] 4.1 `utils/plugins.py` `discover(registrar)`: `importlib.metadata.entry_points(group="skye.plugins")`, each entry point loaded and
    passed to `use`; the report (`PluginReport`) kept for the command and the errors (depends on O60, option A)
    - _Requirements: 57.1_
  - [ ] 4.2 The registrar imports `"skye.utils.plugins:discover"` by text at the first miss, scans once per process and looks again
    once; `import skye` scans nothing (a fake entry point that raises on load proves it)
    - _Requirements: 57.1, 57.2, 57.3, 7.8, 7.9_
  - [ ] 4.3 The `plugins` key of the configuration file, read with `load_config` (D91): only the listed entry points load; without the
    key, all; the key returns to the configuration schema and its documentation (D106 removed it while no code read it)
    - _Requirements: 57.5; D91, D106_
  - [ ] 4.4 Failures: an entry point that fails to load or to register is logged once at WARNING with `extra` (entry point,
    distribution, error) and skipped; an unknown name after the scan raises `ConfigurationError` listing the names of the kind and the
    failures
    - _Requirements: 57.6, 57.7; D105_
  - [ ] 4.5 `skye.use(plugin)`: an object with `register` or a function of one parameter; a failing `register` raises
    `ConfigurationError` naming the plugin with the cause kept; `use` added to the lazy names of `skye/__init__.py`
    - _Requirements: 57.4, 57.8, 7.8_
  - [ ] 4.6 `skye plugins [--format json]` in `utils/cli.py`: built-in registrations and each entry point (name, distribution, version,
    loaded or failed with the error, names per kind)
    - _Requirements: 57.9_
  - [ ] 4.7 Tests in `tests/unit/plugins/test_discovery.py` with a fake `entry_points`: one scan per process, allowlist, failing entry
    point, error after the scan, `use` with an object and a function, the command in text and JSON
    - _Requirements: 57.1 to 57.9_

- [ ] 5. Built-in providers through the registrar, with their profiles
  - [ ] 5.1 `models/_plugin.py`: every built-in model and embedding provider registered by text with its `ProviderProfile` (key
    variables, region rule, default endpoint, client settings, model profiles with prices, tokenizer, overhead and `info`, `map_error`)
    - _Requirements: 56.6, 59.1, 59.7_
  - [ ] 5.2 `ProviderRegistry` becomes a view of the registrar: same methods and signatures, no table of its own; `skye.provider(name)`
    reaches third-party providers through the lookup
    - _Requirements: 56.7_
  - [ ] 5.3 An OpenAI-compatible endpoint registered with `OpenAICompatibleProvider` and a profile, and no class; a test that calls it
    offline through a fake transport
    - _Requirements: 59.9_
  - [ ] 5.4 The D109 list of Claude models that refuse a forced choice moves into the Anthropic and Bedrock model profiles
    (`info["supports_forced_capability_choice"]`); `refuses_forced_choice` reads `get_model_info()`; the two adapter tuples and their
    parity test go
    - _Requirements: 60.7; D109_

- [ ] 6. Provider knowledge in one place
  - [ ] 6.1 `CostCalculator` without `PRICING`: prices from the profiles, `add_custom_pricing` as a user layer that wins,
    `get_pricing`, `pricing_for`, `list_models` unchanged for the caller
    - _Requirements: 60.1, 59.3_
  - [ ] 6.2 `TokenCounter` without prefixes, tokenizers or overheads of its own: `tokenizer` and `message_overhead` from the
    `ModelProfile`; `register_tokenizer` registers a tokenizer by name through the registrar (coordinate with the token-counter work of
    `1-adapters-models`)
    - _Requirements: 60.2, 59.3_
  - [ ] 6.3 One home for API-key variables: remove `STANDARD_ENV_VARS` (`auth`), `API_KEY_VARIABLES` (`router/skye_file.py`) and the
    names written in the adapters; all read `api_key_variables` of the profile; the variable names stay the provider-standard ones
    - _Requirements: 60.3, 11.6_
  - [ ] 6.4 The router applies `client_settings` and `model_is_deployment` of the target's profile; the Azure branch of
    `router/model_router.py` goes; the router contains no provider name
    - _Requirements: 60.4_
  - [ ] 6.5 Error handlers into their adapter modules, referenced by `map_error`; `gemini_schema` into the Google adapter;
    `models/transport/error_mapping.py` keeps the HTTP-status mapping of D104 and calls `map_error`
    - _Requirements: 60.5; D104_
  - [ ] 6.6 The AWS region through `resolve_region` in `auth/aws.py`, `auth/sts.py`, `models/transport/credentials.py` and the store
    backends that need one; the `us-east-1` defaults go; DynamoDB passes the region found and leaves the boto3 chain last (depends on
    O63, part 2, option A)
    - _Requirements: 60.6, 59.6_
  - [ ] 6.7 Bedrock reads its native-JSON-output capability from `get_model_info()`; `_native_json_output` goes
    - _Requirements: 60.7_
  - [ ] 6.8 `tests/budget/test_provider_knowledge.py`: a built-in provider name, a key variable or a price as a literal outside the
    adapter and profile of that provider fails; an allowlist that only shrinks
    - _Requirements: 60.8_

- [ ] 7. The other registries as views
  - [ ] 7.1 `store/_plugin.py` and `register_backend` as a view (the `_BUILTIN` table becomes registrations by text)
    - _Requirements: 56.6, 56.7_
  - [ ] 7.2 `auth/_plugin.py` and `register_credential_source` as a view (`BUILTIN_SOURCES` becomes registrations by text)
    - _Requirements: 56.6, 56.7_
  - [ ] 7.3 `CapabilityRegistry`, `register_agent_type` and `TokenCounter.register_tokenizer` as views; the registrar holds the default
    set of capabilities and prompt filters, and a registration on a builder or registry instance stays local
    - _Requirements: 56.7, 56.8_
  - [ ] 7.4 A test that every call to a registry of today works as before (one case per registry)
    - _Requirements: 56.7_

- [ ] 8. Storage knowledge in one place
  - [ ] 8.1 `CounterStore.count(key)` on the Port and in all six backends; `check_backend` checks it
    - _Requirements: 60.9; D98_
  - [ ] 8.2 `ExpiryStore` (`is_alive`, `remaining`) beside the Protocols of D98, in every backend that stores an expiry; the
    conformance suite checks it with `FakeClock`
    - _Requirements: 60.10; D95, D98_
  - [ ] 8.3 The router: counters through `count`, cooldown as a key with a `ttl` read through `ExpiryStore`, no `time.time()`
    comparison, default store from `skye.store.backend("memory")`; router tests driven by `FakeClock`
    - _Requirements: 60.9, 60.10, 60.11; D97_
  - [ ] 8.4 `store.namespaced(store, prefix)` and the router on the namespace `router` (depends on O63, part 1, option A)
    - _Requirements: 60.10_
  - [ ] 8.5 `tests/budget/test_storage_knowledge.py`: the import of a concrete backend class outside `store` and its tests fails, and so
    does reading the key `"count"` of a stored value outside `store`
    - _Requirements: 60.12_

- [ ] 9. The closed kinds
  - [ ] 9.1 Routing strategies by name through the registrar; the eight built-ins registered in `router/_plugin.py`; every
    `RoutingStrategy` member still works; the `if`/`elif` chain goes; the `.skye` checker accepts a registered name in `strategy`
    - _Requirements: 58.1_
  - [ ] 9.2 MCP clients by `impl` name through the registrar; `"builtin"` the default; `"fastmcp"` registered by text and imported only
    when chosen
    - _Requirements: 58.2, 10.7; D16_
  - [ ] 9.3 Decision models by name through the registrar; Jev registered as a built-in
    - _Requirements: 58.3, 9.8_
  - [ ] 9.4 A test with a third-party strategy, MCP client and decision model registered through `skye.use`
    - _Requirements: 58.1, 58.2, 58.3_

- [ ] 10. Conformance per kind
  - [ ] 10.1 One public `check_<kind>` per kind, next to its owner, offline against fakes, returning the names of the checks passed and
    raising on the first failure: model and embedding provider, credential source, routing strategy, MCP client, decision model,
    tokenizer, capability, prompt filter, agent type (store: `check_backend` exists)
    - _Requirements: 58.4; D98_
  - [ ] 10.2 One parametrized test runs every built-in registration of every kind through its function
    - _Requirements: 58.5_

- [ ] 11. Documentation, skill and budgets
  - [ ] 11.1 The extension page (`docs/guides/extend/index.md`) lists the registrar method of each kind; a guide "Write a plugin" and a
    reference of `ProviderProfile` in the wiki, with snippets from `examples/plugins/`
    - _Requirements: 61.2, 15.10_
  - [ ] 11.2 The Claude skill that ships with the package: `skye plugins`, `skye.use`, the `plugins` key, the registrar and the profile;
    an eval for the rule that a provider is declared once, in its profile
    - _Requirements: 61.3_
  - [ ] 11.3 No third-party dependency and no extra added; size, import time and cold start of `budgets.toml` not higher
    - _Requirements: 61.4, 7.9; D27_

- [ ] 12. Final checkpoint
  - [ ] 12.0 Validate the code against every criterion this spec points to (`requirements.md`: Requirements 56 to 61 of
    `10-requirements.md`, and decisions D27, D97, D98, D104, D107 and D108). For each criterion, write one evidence line: the file or
    function that realizes it and the test that checks it. A criterion with no code or no test is a finding.
  - [ ] 12.1 Run `uv run pytest tests -q`, `make budget`, the doctests of the new modules and the strict docs build; record the numbers
  - [ ] 12.2 Close in steering what the work settled: O59 to O63 marked as taken with the options used, the "Extension points" table of
    `11-design.md` updated, and the scan note `docs/_notes/extension-points-scan.md` marked as done

## Notes
- Tasks are deliverables in build order (D108). Each cites the requirement numbers of `10-requirements.md` it satisfies, or the decision it honors.
- Task IDs cited from other documents are `plugins:N.k`.
- Task 6.2 coordinates with the token-counter work of `1-adapters-models`, which uses the field names of Requirement 59.2.
- Tasks 8.x are independent of 6.x, except that 6.6 also touches store backends, so it runs in a later wave than 8.1 and 8.2.
- Tasks that depend on an open point (O59 to O63) follow its recommended option; a different answer from the owner changes only the task named.
- Tasks 12.0 to 12.2 are the final checkpoint: evidence per criterion, the full test and budget run, and the closing of steering.
- The dependency graph below puts tasks that write the same file in different waves: `base/plugins.py` (2.3, 2.4, 2.5, 4.2),
  `base/profile.py` (3.1 to 3.3), `utils/plugins.py` (4.1, 4.3, 4.4, 4.5), the adapters (5.4, 6.3, 6.5, 6.7), the router (6.4, 8.3,
  8.4, 9.1) and the store package (7.1, 8.1, 8.2, 6.6, 8.4).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1"] },
    { "id": 1, "tasks": ["1.2", "2.2", "3.2"] },
    { "id": 2, "tasks": ["2.3", "3.3"] },
    { "id": 3, "tasks": ["2.4", "3.4"] },
    { "id": 4, "tasks": ["2.5"] },
    { "id": 5, "tasks": ["2.6", "4.1", "5.1"] },
    { "id": 6, "tasks": ["4.2", "6.1", "6.2", "7.1", "7.2", "9.2", "9.3"] },
    { "id": 7, "tasks": ["4.3", "5.2", "5.3", "5.4", "6.4", "7.3", "8.1"] },
    { "id": 8, "tasks": ["4.4", "6.3", "7.4", "8.2"] },
    { "id": 9, "tasks": ["4.5", "6.5", "8.3"] },
    { "id": 10, "tasks": ["4.6", "6.6", "6.7", "8.4"] },
    { "id": 11, "tasks": ["4.7", "6.8", "8.5", "9.1"] },
    { "id": 12, "tasks": ["9.4", "10.1"] },
    { "id": 13, "tasks": ["10.2", "11.1", "11.2"] },
    { "id": 14, "tasks": ["11.3"] },
    { "id": 15, "tasks": ["12.0"] },
    { "id": 16, "tasks": ["12.1"] },
    { "id": 17, "tasks": ["12.2"] }
  ]
}
```
