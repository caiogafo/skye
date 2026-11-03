# Implementation Plan: base

## Overview

Milestones in build order for the `base` component (codename stratus): the standard contracts first, then the Port catalogue,
the error hierarchy, configuration and the lazy-import helper, the one sanctioned transport, and the budget guards. Status is
judged from the code in `src/skye/base` and the tests in `tests/`. Each task cites the steering requirement numbers it
satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it honors.

## Tasks

- [ ] 1. Standard contracts (stdlib shapes across every Port)
  - [x] 1.1 Message types: `SkyeMessage` and the role variants, `ContentChunk`
    - Evidence: `src/skye/base/messages.py` (`SkyeMessage`, `UserMessage`, `AssistantMessage`, `SystemMessage`, `CapabilityMessage`).
    - _Requirements: 16.1_
  - [x] 1.2 Completion contracts: `CompletionRequest`, `CompletionResponse`, `StreamChunk`, `TokenUsage`
    - Evidence: `src/skye/base/completion.py` (content, role, metadata, token usage, model id, provider; stream yields `StreamChunk`).
    - _Requirements: 16.4, 16.5, 19.1_
  - [x] 1.3 Capability contract and the OpenAI-shape boundary
    - Evidence: `src/skye/base/capability_schema.py` (name, description, parameters), `src/skye/base/completion.py` (`CapabilityCall`, `ExecutableCapabilityCall`), `src/skye/base/openai_shape.py`.
    - _Requirements: 16.1_

- [ ] 2. Port catalogue (one module per Port, no I/O, no component import)
  - [x] 2.1 Define every Port under `interfaces/` and re-export them
    - Evidence: `src/skye/base/interfaces/` (model, decision, runnable, storage, registry, cost_calculator, error_handler, token_counter, memory, vector_encoder, router, safety, observer, event_handler, content_reader, multimodal_handler, prompt, config_loader, plugin, capability, authorizer, authentication), `src/skye/base/interfaces/__init__.py`.
    - _Requirements: 16.1_
  - [ ]* 2.2 Test: Port compliance validated at initialization and at runtime, plugins registered and discovered
    - Note: add tests asserting that a component implementing a Port is validated at init and at runtime, and that plugins register and resolve through the `plugin` / `registry` Ports.
    - _Requirements: 16.2, 16.3_

- [ ] 3. Errors and logging
  - [x] 3.1 `SkyeError` hierarchy with context and structured logging
    - Evidence: `src/skye/base/exceptions.py` (`SkyeError`, `ProviderError`, `ConfigurationError`, `ValidationError`, `CapabilityExecutionError`, `MissingExtraError`; logs with `extra={...}`, keeps the cause).
    - _Requirements: 18.1, 18.2_
  - [ ] 3.2 Structured log events and telemetry hooks for model invocations
    - Note: define in `base` the shape of a structured log event for a model invocation (request/response details, correlation id) and the telemetry-hook Ports (`observer`, `event_handler`) that `observe` consumes; wire a per-component log level through `SkyeConfig`. The emission lives in `observe`/`models`; `base` owns the contract and the config fields.
    - _Requirements: 18.3, 18.4_

- [ ] 4. Token usage and cost contracts
  - [x] 4.1 `TokenUsage` on the response and pricing fields on `ModelConfig`
    - Evidence: `src/skye/base/completion.py` (`TokenUsage`), `src/skye/base/config.py` (`cost_per_1k_prompt_tokens`, `cost_per_1k_completion_tokens`); `cost_calculator` / `token_counter` Ports in `interfaces/`.
    - _Requirements: 19.1, 19.2_
  - [ ]* 4.2 Test: usage aggregates across requests through the response metadata
    - Note: assert that token usage can be summed across several `CompletionResponse` objects via the metadata contract.
    - _Requirements: 19.3_

- [ ] 5. Configuration
  - [x] 5.1 `ConfigLoader` with precedence, `${VAR}` substitution and the three prefixed variables
    - Evidence: `src/skye/base/config.py` (`ConfigLoader.load` applies file -> env -> code; `substitute_env_vars` expands `${VAR}` and raises `ConfigurationError` when missing; invalid values raise `ConfigurationError`; `ALL_ENV_VARS` = `SKYE_LOG_LEVEL`, `SKYE_CONFIG`, `SKYE_ENABLE_TELEMETRY`).
    - _Requirements: 20.1, 20.2, 20.3, 20.4_
  - [x] 5.2 YAML needs the extra `yaml`, JSON needs nothing
    - Evidence: `src/skye/base/config.py` (`_yaml()` -> `missing_extra("yaml", extra="yaml")`), `src/skye/base/lazy_import.py` (`missing_extra`).
    - _Requirements: 20.1; honors D29_
  - [x] 5.3 Honor D18: exactly three prefixed variables, credentials from provider-standard names
    - Evidence: `src/skye/base/config.py` (`ENV_CONFIG_VARS`, `ALL_ENV_VARS`; `_load_from_env` reads only the prefixed config vars, never provider credentials).
    - _Requirements: 20.1; honors D18_

- [ ] 6. The one sanctioned transport
  - [x] 6.1 `base/http.py`: stdlib HTTP shared by `auth` and the adapters
    - Evidence: `src/skye/base/http.py` (`request_json`, `stream_lines`, `send_bytes`, `open_stream`, `request`; urllib + json only; maps failures to `ProviderError`).
    - _Requirements: 18.1_
  - [ ] 6.2 Resolve O6: where `http.py` lives given "base does no I/O"
    - Note: `base` must do no file/network/process I/O except `http.py` (Requirement 3.2). O6 is open on where this module belongs and whether cloud secret managers are in scope of `auth`. Record the decision in `12-decisions.md`, then adjust the import-matrix exception for `http.py` and this spec; no code change until the decision is taken.
    - _Requirements: 16.1; O6_

- [ ] 7. Type safety and the pydantic migration
  - [x] 7.1 Full type hints (3.10 syntax) and field-level `ValidationError`
    - Evidence: `src/skye/base/*.py` fully hinted with `list[...]` / `X | None`; `src/skye/base/exceptions.py` (`ValidationError(field, value)`).
    - _Requirements: 21.1, 21.3_
  - [ ] 7.2 Move the core models off pydantic to dataclasses (D24 / O4)
    - Note: `messages.py`, `completion.py` and `config.py` still subclass `pydantic.BaseModel`; new structures must be dataclasses (D24) and `base` must not need pydantic to import (Requirement 3.3). Migrate the shared contracts to `dataclasses`, keep field-level `ValidationError`, and remove pydantic from the core once nothing in `base` imports it. Blocked on open decision O4 (when and how); coordinate with `1-adapters-models` task 8.1 (structured-output schemas) and the router, which consume these models.
    - _Requirements: 21.2; honors D24_

- [ ] 8. Budget and structure guards
  - [x] 8.1 `base` imports only the standard library; clean top-level import
    - Evidence: `tests/budget/test_import_matrix.py` (base -> stdlib only, `http.py` the one I/O module), `tests/budget/test_clean_import.py` (`import skye` imports no optional/provider library).
    - _Requirements: 21.1_
  - [x] 8.2 Codename stratus only in the sanctioned places
    - Evidence: `src/skye/base/__init__.py` (docstring ends "Codename: stratus."), `tests/budget/test_codenames.py`.
    - _Requirements: 16.1_

- [ ] 9. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional (tests) and can be skipped for a faster path.
- Status reflects the code in `src/skye/base` and `tests/` at writing time.
- The top-level public surface (`skye/__init__.py` re-exporting `messages`, `completion`, `exceptions`, `config`,
  Requirement 7.8) is owned by the cross-cutting spec `0-base-structure`, not this one.
- Open items: 3.2 (structured log-event and telemetry-hook contracts), 6.2 (O6, where `http.py` lives), 7.2 (O4/D24,
  pydantic -> dataclasses).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "2.1", "3.1", "6.1"] },
    { "id": 1, "tasks": ["2.2", "3.2", "4.1", "5.1", "5.2", "5.3", "7.1", "8.1", "8.2"] },
    { "id": 2, "tasks": ["4.2", "6.2", "7.2"] }
  ]
}
```
