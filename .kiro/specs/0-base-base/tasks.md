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

- [x] 10. The `.skye` parser (decisions D50 to D61; Requirement 54 of `10-requirements.md`)
  - Note: the parser takes text and returns a syntax tree and the validated block models; it reads no file (Requirement 3.2: `base` does no file I/O). The
    code that reads a file lives in the component that loads it (`router`, `flows`, `prompts`) and in the `skye check` entry point. Everything is
    standard library. The syntax, the errors and the examples are in `.kiro/specs/0-base-uxui/dsl-examples.md`; the grammar becomes a wiki page in
    task 8.2 of `0-base-uxui`. Module: `src/skye/base/dsl/`.
  - [x] 10.1 Lexer and syntax tree: tokens with line and column; blocks (`KIND "label" { ... }`), attributes, `#` comments, strings, `"""` multi-line strings, numbers, booleans, lists, maps, durations as strings, references (`registry.x`, `context.x`, `step.X.output`, `env.X`, `item`) and expressions kept as text with their position.
    - Evidence: `src/skye/base/dsl/lexer.py`, `tree.py`, `parser.py`; `tests/unit/dsl/test_lexer_parser.py` (positions, comments, `"""` strings, values, shorthand route, random-text robustness).
    - _Requirements: 54.1, 54.2; D50; D57_
  - [x] 10.2 Errors that help: `SkyeSyntaxError` (a `SkyeError`) carrying file name, line, column, reason and fix; the parser and the validators collect every error they can find in the file and raise them together; the "did you mean" suggestion for a name that is close to a known one.
    - Evidence: `src/skye/base/dsl/errors.py` (`Diagnostic`, `SkyeSyntaxError`, difflib `did_you_mean`); `tests/unit/dsl/test_conformance.py::test_all_errors_are_reported_together`, `test_syntax_errors_are_collected_and_raised_together`.
    - _Requirements: 54.3_
  - [x] 10.3 The expression checker and evaluator: `ast.parse(..., mode="eval")` with a whitelist of nodes (comparison, `and`/`or`/`not`, arithmetic, `in`, names, attribute access, subscripts, constants, lists, dicts, conditional) and of functions (`len`, `min`, `max`, `abs`, `round`, `str`, `int`, `float`); no `eval`, no `exec`, no call to anything else.
    - Evidence: `src/skye/base/dsl/expressions.py` (`check_expression`, `evaluate`, no `eval`/`exec`); `tests/unit/dsl/test_expressions.py`.
    - _Requirements: 54.5; D55_
  - [x] 10.4 The block models, as `@validated` dataclasses: `RouterSpec`, `RouteSpec`, `TargetSpec`, the retry and allowed-fails policies (field names 1:1 with today's configuration, durations as strings), `FlowSpec`, `StepSpec`, `ParallelSpec`, `ChoiceSpec`, `ContextSpec`, `PromptSpec` (the reduced block); built from the tree, with the shorthand `route "x" = [...]`.
    - Evidence: `src/skye/base/dsl/specs.py` (`@validated` models), `build.py` (`build`); `tests/unit/dsl/test_skeletons_cli_schema.py` (model content, field names against `ModelTarget`, strategies against `RoutingStrategy`).
    - _Requirements: 54.1, 54.6, 54.7; D56 to D60_
  - [x] 10.5 The load-time checks of Requirement 54.4: every `next`, `on_error`, `on_timeout` and `fallback` names a block that exists; every step has a `next`; a `choice` has an `else`; a step that can be re-entered has `max_visits`; every reference has a known prefix and resolves; every context field is declared and a `set` has the declared type; every duration is a string with a unit; unreachable steps; `wait` and `on_event` are rejected with the "not available in this version" message.
    - Evidence: `src/skye/base/dsl/build.py` (`check_text`, graph, reference, type, duration and version 2 checks); `tests/unit/dsl/test_conformance.py::test_error_table_row`.
    - _Requirements: 54.4, 54.10; D54 to D58_
  - [x] 10.6 The JSON Schema of the `router`, `flow` and `prompt` blocks, generated from the block dataclasses with `skye.base.validated.json_schema`.
    - Evidence: `src/skye/base/dsl/schema.py` (`block_schema`, from `skye.base.validated.json_schema`); `tests/unit/dsl/test_skeletons_cli_schema.py::test_block_schema_matches_the_models`.
    - _Requirements: 54.8; D61_
  - [x] 10.7 Tests of the parser: a parametrized suite over the fixtures (each example of the reference set parses, each row of the error table gives its message with file, line and column), property-style tests for the lexer, tests that the expression checker rejects `open(...)`, `__import__`, attribute access to dunder names and any call outside the list, and that `import skye` still imports nothing outside the standard library.
    - Evidence: `tests/unit/dsl/` (`test_conformance.py` over `tests/fixtures/skye/`, `test_lexer_parser.py`, `test_expressions.py`, `test_imports.py`: `import skye` does not load the dsl and the dsl adds only standard library modules, no file I/O).
    - _Requirements: 54.3, 54.4, 54.5, 54.11_

  - [x] 10.8 Skeleton generators: `new_router`, `new_flow`, `new_prompt` and `skeleton(kind, name, template)` return `.skye` text (no file I/O) derived from the reference examples, with `# CHANGE ME` marks and example references; no version 2 syntax; `skye new router|flow|prompt NAME [--template T] [-o file] [--force]` and `skye new --list` in the command line (outside `base`).
    - Evidence: `src/skye/base/dsl/skeletons.py`, `src/skye/utils/cli.py`; `tests/unit/dsl/test_skeletons_cli_schema.py` (every kind and template passes `check_text`, none contains `wait` or `on_event`, `skye new` refuses to overwrite without `--force`).
    - _Requirements: 54.1, 54.8; D61_

- [x] 11. Do not parse the same text twice (decision D63; Requirement 54.13)
  - [x] 11.1 `skye.base.dsl.cache`: `build_cached(text, filename=, registry_names=)`, `cache_info()`, `clear_cache()`; a bounded (64) least-recently-used cache keyed by the SHA-256 of the text, the file name and the registry names; the cached document is read-only.
    - Evidence: `src/skye/base/dsl/cache.py`; `tests/unit/dsl/test_cache.py`.
    - _Requirements: 54.13; D63_
  - [x] 11.2 `skye.utils.skye_files.load_document(path, registry_names=, use_cache=)`: returns the document from memory without reading the file when its modification time and size are the same, reads and hashes it when they differ and keeps the document if the hash is the same; the router file loader uses it.
    - Evidence: `src/skye/utils/skye_files.py`, `src/skye/router/skye_file.py`; `tests/unit/dsl/test_cache.py`.
    - _Requirements: 54.13; D63_
  - [x] 11.3 Measure the parse time of a real router file and flow file (cold and from the cache) and write it in `docs/budgets.md`; the number decides open decision O37 (a parse result kept on disk).
    - Evidence: `docs/budgets.md`, section "Parse time of a `.skye` file": best of 5 fresh interpreters on a clean install; the real router file (292 lines) builds cold in 4.6 ms and flows in 2.3 to 5.6 ms, from the memory cache in 8 to 40 microseconds; importing the parser costs about 27 ms. Conclusion: a parse result on disk would save about 5 ms of roughly 70 ms per cold container and adds a file to keep consistent, so it is not worth it; the owner can close O37 as "no" (not edited here: `12-decisions.md` is the owner's).
    - _Requirements: 54.13; O37_

- [ ] 12. Final verification (to be run with Kiro)
  - [ ] 12.1 Run `uv run pytest tests -q` and `uv run pytest tests/budget -q`; confirm that `src/skye/base` imports only the standard library and does no file I/O except `http.py` (the parser takes text); fix what fails, one failure at a time.
    - _Requirements: 54.2, 54.11; Requirement 3_
  - [x] 12.2 Report which tasks of this spec are still unticked and anything left open.
    - Evidence (2026-11-07): the only unticked tasks of this spec are 12 and 12.1. Open: `src/skye/base/config.py` (`ConfigLoader._load_from_file`) calls `Path.exists()` and `open()` to read a
      JSON file, which Requirement 3.2 does not allow (`base` does no file I/O except `http.py`); no test guards that rule today. Everything else in `base` imports the standard library
      only (`typing_extensions` appears under `TYPE_CHECKING` only and is not installed in a clean environment). Moving the read to the caller needs a decision of the owner.
    - _Requirements: 15.1_

- [ ] 13. The language grows: comments, front matter, the formatter, prompt inputs and outputs (decisions D69 to D73; Requirements 54.16 to 54.20)
  - [x] 13.1 Comments `/* */` and `/** **/` in the lexer; a comment in an expression is a space; `//` stays floor division
    - Evidence (2026-11-08): `src/skye/base/dsl/lexer.py`, `parser.py` (`_expression_text`); `tests/unit/dsl/test_comments.py`.
    - _Requirements: 54.16; D71_
  - [x] 13.2 Front matter in TOML: `split_metadata`, `format_metadata`, `Document.metadata`, line numbers unchanged, YAML lines rejected with the fix
    - Evidence (2026-11-08): `src/skye/base/dsl/metadata.py`, `parser.py`, `tree.py`, `build.py`, `emit.py`; `tests/unit/dsl/test_metadata.py`.
    - _Requirements: 54.17; D71_
  - [x] 13.3 `format_text` and `FormatError`: idempotent, keeps comments and strings, refuses mistakes and a different model
    - Evidence (2026-11-08): `src/skye/base/dsl/fmt.py`, `skeletons.py`; `tests/unit/dsl/test_fmt.py` (also checks that every bundled `.skye` file is formatted).
    - _Requirements: 54.18; D71_
  - [x] 13.4 Descriptions and structured types of prompt variables; `conform` with the path of each mistake
    - Evidence (2026-11-08): `src/skye/base/dsl/parser.py` (`TypeCall.second`), `build.py`, `specs.py` (`VariableSpec.description`, `item_type`, `fields`), `emit.py`, `shapes.py`; `tests/unit/dsl/test_variable_descriptions.py`, `tests/unit/dsl/test_structured_variables.py`. The default form is open decision O46.
    - _Requirements: 54.20, 30.10; D73_
  - [x] 13.5 The `output` block in the parser, the checker and `to_text` (descriptions, format from a variable, conditional variants); `loop` inside `each`
    - Evidence (2026-11-08): `src/skye/base/dsl/build.py`, `specs.py` (`OutputSpec`, `OutputFieldSpec`, `output_variants`), `emit.py`; `tests/unit/dsl/test_output_block.py`, `tests/unit/dsl/test_conditional_output.py`; `tests/unit/prompts/test_prompt_loops.py`.
    - _Requirements: 33.5 to 33.8, 30.11; D69, D70_
  - [x] 13.6 `describe_prompt`, `prompt_help` and `PromptInfo` in `base/dsl/info.py`
    - Evidence (2026-11-08): `src/skye/base/dsl/info.py`; `tests/unit/prompts/test_prompt_help.py`. Its place is open decision O46.
    - _Requirements: 34.7; D73_
  - [x] 13.7 The resource Port: `ResourceProviderInterface` and `Resource` in `base/interfaces/resource.py`, exported by `skye.interfaces`
    - Evidence (2026-11-08): `src/skye/base/interfaces/resource.py`, `src/skye/base/interfaces/__init__.py`, `src/skye/interfaces.py`; `tests/unit/tools/test_mcp_conformance.py` (the Port, the frozen dataclass, a plain class satisfies it).
    - _Requirements: 10.5; D26_
  - [ ] 13.8 Re-run task 12.1 on the new modules (`metadata.py`, `fmt.py`, `shapes.py`, `info.py`, `interfaces/resource.py`): standard library only, no file I/O
    - Note (2026-11-08): `uv run pytest tests -q` and `uv run pytest tests/budget -q` pass, and `uv run mypy src/skye/base/dsl` reports no error, but the open point of 12.2 (`ConfigLoader._load_from_file` reads a file in `base`) is still there, so 12.1 and this task stay open.
    - _Requirements: 3.2, 54.2, 54.11_

## Notes

- Tasks marked with `*` are optional (tests) and can be skipped for a faster path.
- Status reflects the code in `src/skye/base` and `tests/` at writing time.
- The top-level public surface (`skye/__init__.py` re-exporting `messages`, `completion`, `exceptions`, `config`,
  Requirement 7.8) is owned by the cross-cutting spec `0-base-structure`, not this one.
- Done on 2026-11-03: every task, including the final checkpoint (9), verified by running the full suite and the budget
  gate. 3.2 and 6.2 add the log-event shape, the per-component log levels and decision D32; 7.2 moves the base contracts to
  validated dataclasses. The project-wide pydantic removal (O4, taken as D49): `tools`, `memory`, `utils` and `router` still
  import it, tracked in `0-base-structure` tasks 14.1 to 14.4. Tasks 10 (the `.skye` parser), 11 (the cache, D63) and 12 (final
  verification, run with Kiro) were added after D50 to D61.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "2.1", "3.1", "6.1"] },
    { "id": 1, "tasks": ["2.2", "3.2", "4.1", "5.1", "5.2", "5.3", "7.1", "8.1", "8.2"] },
    { "id": 2, "tasks": ["4.2", "6.2", "7.2"] },
    { "id": 3, "tasks": ["9", "10.1", "10.3"] },
    { "id": 4, "tasks": ["10.2", "10.4"] },
    { "id": 5, "tasks": ["10.5", "10.6"] },
    { "id": 6, "tasks": ["10.7", "10.8"] },
    { "id": 7, "tasks": ["11.1", "11.2", "11.3"] },
    { "id": 8, "tasks": ["12.1", "12.2"] }
  ]
}
```
