# Implementation Plan: base

## Overview

Milestones in build order for the `base` component (codename stratus): the standard contracts first, then the Port catalogue,
the error hierarchy, configuration and the lazy-import helper, the one sanctioned transport, and the budget guards. Status is
judged from the code in `src/skye/base` and the tests in `tests/`. Each task cites the steering requirement numbers it
satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it honors.

## Tasks

- [x] 1. Standard contracts (stdlib shapes across every Port)
  - [x] 1.1 Message types: `SkyeMessage` and the role variants, `ContentChunk`
    - Evidence: `src/skye/base/messages.py` (`SkyeMessage`, `UserMessage`, `AssistantMessage`, `SystemMessage`, `CapabilityMessage`).
    - _Requirements: 16.1_
  - [x] 1.2 Completion contracts: `CompleteRequest`, `CompleteResponse`, `StreamChunk`, `TokenUsage`
    - Evidence: `src/skye/base/completion.py` (content, role, metadata, token usage, model id, provider; stream yields `StreamChunk`).
    - _Requirements: 16.4, 16.5, 19.1_
  - [x] 1.3 Capability contract and the OpenAI-shape boundary
    - Evidence: `src/skye/base/capability_schema.py` (name, description, parameters), `src/skye/base/completion.py` (`CapabilityCall`, with `execute()` after D45), `src/skye/base/openai_shape.py`.
    - _Requirements: 16.1_

- [x] 2. Port catalogue (one module per Port, no I/O, no component import)
  - [x] 2.1 Define every Port under `interfaces/` and re-export them
    - Evidence: `src/skye/base/interfaces/` (model, decision, runnable, storage, registry, cost_calculator, error_handler, token_counter, memory, vector_encoder, router, safety, observer, event_handler, content_reader, multimodal_handler, prompt, config_loader, plugin, capability, authorizer, authentication), `src/skye/base/interfaces/__init__.py`.
    - _Requirements: 16.1_
  - [x]* 2.2 Test: Port compliance validated at initialization and at runtime, plugins registered and discovered
    - Evidence: `tests/unit/test_port_compliance.py` (an incomplete implementation of a Port cannot be built; `validate_interface_compliance` checks at runtime; a plugin runs its lifecycle through `PluginInterface`; a provider plugin registers and is found by name through the registry Port; an incomplete one fails when the registry builds it).
    - _Requirements: 16.2, 16.3_

- [x] 3. Errors and logging
  - [x] 3.1 `SkyeError` hierarchy with context and structured logging
    - Evidence: `src/skye/base/exceptions.py` (`SkyeError`, `ProviderError`, `ConfigurationError`, `ValidationError`, `CapabilityExecutionError`, `MissingExtraError`; logs with `extra={...}`, keeps the cause).
    - _Requirements: 18.1, 18.2_
  - [x] 3.2 Structured log events and telemetry hooks for model invocations
    - Evidence: `src/skye/base/log_event.py` (`ModelInvocationEvent`: phase, model, provider, correlation id, request and response details, no message text; `model_invocation_start`, `_end`, `_error`; `log_extra()` for `logging`'s `extra`; `event_type` maps to the `EventType` of the `observer` Port), `src/skye/base/config.py` (`SkyeConfig.component_log_levels`, `level_for`, `apply_log_levels`), the hook Ports `src/skye/base/interfaces/observer.py` and `event_handler.py`; `tests/unit/test_log_event.py`, `tests/unit/config/test_component_log_levels.py`. The emission stays in `models` and `observe`.
    - _Requirements: 18.3, 18.4_

- [x] 4. Token usage and cost contracts
  - [x] 4.1 `TokenUsage` on the response and pricing fields on `ModelConfig`
    - Evidence: `src/skye/base/completion.py` (`TokenUsage`), `src/skye/base/config.py` (`cost_per_1k_prompt_tokens`, `cost_per_1k_completion_tokens`); `cost_calculator` / `token_counter` Ports in `interfaces/`.
    - _Requirements: 19.1, 19.2_
  - [x]* 4.2 Test: usage aggregates across requests through the response metadata
    - Evidence: `tests/unit/test_usage_aggregation.py` (usage and cost in the metadata add up across responses; usage round-trips through a dict).
    - _Requirements: 19.3_

- [x] 5. Configuration
  - [x] 5.1 `ConfigLoader` with precedence, `${VAR}` substitution and the three prefixed variables
    - Evidence: `src/skye/base/config.py` (`ConfigLoader.load` applies file -> env -> code; `substitute_env_vars` expands `${VAR}` and raises `ConfigurationError` when missing; invalid values raise `ConfigurationError`; `ALL_ENV_VARS` = `SKYE_LOG_LEVEL`, `SKYE_CONFIG`, `SKYE_ENABLE_TELEMETRY`).
    - _Requirements: 20.1, 20.2, 20.3, 20.4_
  - [x] 5.2 YAML needs the extra `yaml`, JSON needs nothing
    - Evidence: `src/skye/base/config.py` (`_yaml()` -> `missing_extra("yaml", extra="yaml")`), `src/skye/base/lazy_import.py` (`missing_extra`).
    - _Requirements: 20.1; honors D29_
  - [x] 5.3 Honor D18: exactly three prefixed variables, credentials from provider-standard names
    - Evidence: `src/skye/base/config.py` (`ENV_CONFIG_VARS`, `ALL_ENV_VARS`; `_load_from_env` reads only the prefixed config vars, never provider credentials).
    - _Requirements: 20.1; honors D18_

- [x] 6. The one sanctioned transport
  - [x] 6.1 `base/http.py`: stdlib HTTP shared by `auth` and the adapters
    - Evidence: `src/skye/base/http.py` (`request_json`, `stream_lines`, `send_bytes`, `open_stream`, `request`; urllib + json only; maps failures to `ProviderError`).
    - _Requirements: 18.1_
  - [x] 6.2 Resolve O6: where `http.py` lives given "base does no I/O"
    - Evidence: decision D32 in `.kiro/steering/12-decisions.md` (`http.py` stays in `base` as the one I/O exception; cloud secret managers are in scope of `auth` over `base/http.py`), which confirms what `11-design.md` and Requirement 3.2 already state; the import-matrix exception for `http.py` is unchanged (`tests/budget/test_import_matrix.py`). Taken by the assistant on the instruction to implement every task: change it if you decide otherwise.
    - _Requirements: 16.1; O6_

- [x] 7. Type safety and the pydantic migration
  - [x] 7.1 Full type hints (3.10 syntax) and field-level `ValidationError`
    - Evidence: `src/skye/base/*.py` fully hinted with `list[...]` / `X | None`; `src/skye/base/exceptions.py` (`ValidationError(field, value)`).
    - _Requirements: 21.1, 21.3_
  - [x] 7.2 Move the core models off pydantic to dataclasses (D24 / O4)
    - Evidence: `src/skye/base/validated.py` (the `@validated` keyword-only dataclass, `Validated` mixin, `field()` with `ge`/`gt`/`le`/`lt`/`min_length`/`max_length`, conversions and `ValidationError` naming the field, `from_dict`, `to_dict`, `to_json`, `from_json`, `json_schema`; standard library only); `messages.py`, `completion.py`, `config.py`, `interfaces/capability.py` and `interfaces/safety.py` now use it, and nothing under `src/skye/base` imports pydantic (`tests/unit/test_validated.py` imports every base model in a clean interpreter and checks `pydantic` is not loaded). `ValidationError` is also a `ValueError`. `response_schema` and `structured_output` accept any class and instance (a user's pydantic model still works). Pydantic stays a core dependency until the other components migrate (tasks 14.1 to 14.3 of `0-base-structure`): `tools`, `memory`, `utils` and `router` still import it, `[imports.max_files] pydantic` in `budgets.toml` went from 10 to 5.
    - Note: pydantic used to ignore arguments a model does not have, so `UserMessage(images=[...])` ran and dropped the images; a dataclass rejects them with a `ValidationError`. That exposed the example `examples/advanced/multimodal.py`, rewritten on `ImageHandler`; the real gap is task 5.2 of `1-adapters-models`.
    - _Requirements: 21.2; honors D24_

- [x] 8. Budget and structure guards
  - [x] 8.1 `base` imports only the standard library; clean top-level import
    - Evidence: `tests/budget/test_import_matrix.py` (base -> stdlib only, `http.py` the one I/O module), `tests/budget/test_clean_import.py` (`import skye` imports no optional/provider library).
    - _Requirements: 21.1_
  - [x] 8.2 Codename stratus only in the sanctioned places
    - Evidence: `src/skye/base/__init__.py` (docstring ends "Codename: stratus."), `tests/budget/test_codenames.py`.
    - _Requirements: 16.1_

- [x] 9. Checkpoint
  - Evidence: `uv run pytest tests/` passes (1453 passed, 7 skipped, 1 xfailed, 0 failures) and the CI gate `uv run pytest tests/budget/` passes (102 passed, 1 xfailed, 0 failures) on 2026-11-03; no `src/skye/base` module imports pydantic (`tests/budget/test_clean_import.py`) and `budgets.toml` holds `pydantic = 5`.

## Notes

- Tasks marked with `*` are optional (tests) and can be skipped for a faster path.
- Status reflects the code in `src/skye/base` and `tests/` at writing time.
- The top-level public surface (`skye/__init__.py` re-exporting `messages`, `completion`, `exceptions`, `config`,
  Requirement 7.8) is owned by the cross-cutting spec `0-base-structure`, not this one.
- Done on 2026-11-03: every task, including the final checkpoint (9), verified by running the full suite and the budget
  gate. 3.2 and 6.2 add the log-event shape, the per-component log levels and decision D32; 7.2 moves the base contracts to
  validated dataclasses. The project-wide pydantic removal stays open (O4): `tools`, `memory`, `utils` and `router` still
  import it, tracked in `0-base-structure` tasks 14.1 to 14.3.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "2.1", "3.1", "6.1"] },
    { "id": 1, "tasks": ["2.2", "3.2", "4.1", "5.1", "5.2", "5.3", "7.1", "8.1", "8.2"] },
    { "id": 2, "tasks": ["4.2", "6.2", "7.2"] },
    { "id": 3, "tasks": ["9"] }
  ]
}
```
