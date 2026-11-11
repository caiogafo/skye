Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Base contracts, Ports, Public API and lazy imports, Layers, Allowed imports)

# Design Document: base

## Overview

`base` is the layer-0 foundation (codename stratus). It holds the shapes every other component shares — the message and
completion models, the error hierarchy, the configuration loader, the `missing_extra` lazy-import helper and every Port — and
it imports only the standard library. It does no file, network or process I/O, with the one sanctioned exception of
`base/http.py`, the standard-library HTTP transport shared by `auth` and the adapters (Requirement 3.1, 3.2). Nothing in
`base` imports another component, and each Port performs no I/O and imports no component (Requirement 3.4). This document
describes only the internals of `base`; the layer, the allowed imports (none but the standard library), the Port catalogue
and the public-API rule are in the steering sections named above and are not restated here.

Ports defined by this component (all under `base/interfaces`): `model`, `decision`, `runnable`, `storage`, `registry`,
`cost_calculator`, `error_handler`, `token_counter`, `memory`, `vector_encoder`, `router`, `safety`, `observer`,
`event_handler`, `content_reader`, `multimodal_handler`, `prompt`, `config_loader`, `plugin`, `capability`, `resource`, `authorizer`,
`authentication` (design "Ports"). The `resource` Port (`ResourceProviderInterface`, `Resource`; D26) was added on 2026-11-08 and is implemented by the MCP clients of `tools`. Every cross-component dependency crosses one of these, never a concrete implementation.

## Architecture

`base` sits at layer 0 and may import only the standard library (design "Layers", "Allowed imports", enforced by
`tests/budget/test_import_matrix.py` and `tests/budget/test_clean_import.py`). The shape is four concerns in flat modules plus
one interfaces package:

- **Contracts** — the data shapes passed across Ports: `messages.py`, `completion.py`, `capability_schema.py`,
  `openai_shape.py`, `health.py`, `log_event.py`; they are dataclasses built on `validated.py`.
- **Errors** — the `SkyeError` hierarchy in `exceptions.py`.
- **Configuration** — `config.py` (the loader, precedence, `${VAR}` substitution) built on `lazy_import.py`.
- **Transport** — `http.py`, the single I/O module, used by `auth` and the adapters but by nothing else in `base`.
- **Ports** — `interfaces/`, one module per Port, re-exported from `interfaces/__init__.py`.

The top-level public surface (`skye/__init__.py` re-exporting `messages`, `completion`, `exceptions`, `config`) is owned by
the cross-cutting spec `0-base-structure`, not here; `base` only guarantees that those four modules import no optional or
provider library (design "Public API and lazy imports"; Requirement 2 of this spec realizes Requirement 16, not Requirement
7.8).

## Package layout

```
base/
  __init__.py             package docstring ending "Codename: stratus."
  messages.py             SkyeMessage + role variants (User/Assistant/System/Capability), ContentChunk
  completion.py           CompleteRequest, CompleteResponse, StreamChunk, TokenUsage, CapabilityCall
  capability_schema.py    the capability contract (name, description, parameters); handlers live in tools
  openai_shape.py         read-only helpers to accept the OpenAI message/tool shape at the boundary
  health.py               HealthMetrics shared by adapters and the router's health tracking
  validated.py            @validated keyword-only dataclasses: field checks, conversions, constraints (standard library)
  log_event.py            ModelInvocationEvent and the correlation id (the structured log event of a model call)
  exceptions.py           SkyeError, ProviderError (and its RateLimitError, ServerError, ProviderTimeoutError,
                          AuthenticationError, BadRequestError, ContentPolicyError), ConfigurationError,
                          ValidationError, CapabilityExecutionError, MissingExtraError
  config.py               ConfigLoader, SkyeConfig, ModelConfig, substitute_env_vars, the 2 prefixed vars
  lazy_import.py          missing_extra(): first-use import, MissingExtraError on absence
  http.py                 the one network-I/O module (urllib + json); request_json, stream_lines, send_bytes, request
  interfaces/
    __init__.py           re-exports every Port
    model.py decision.py runnable.py storage.py registry.py cost_calculator.py error_handler.py
    token_counter.py memory.py vector_encoder.py router.py safety.py observer.py event_handler.py
    content_reader.py multimodal_handler.py prompt.py config_loader.py plugin.py capability.py
    authorizer.py authentication.py resource.py
  dsl/                    the .skye language, text in and text out (no file I/O)
    lexer.py parser.py tree.py build.py specs.py expressions.py errors.py schema.py emit.py cache.py skeletons.py
    metadata.py           front matter (TOML between two --- lines); not frontmatter.py, `front` is a watermark (R4)
    fmt.py                format_text, FormatError: the text formatter behind `skye fmt`
    shapes.py             conform: checks a structured prompt variable and fills its optional fields in a copy
    info.py               describe(spec) for prompt, router and flow blocks; describe_prompt, prompt_help, PromptInfo (D83)
```

## Components and Interfaces

### Standard contracts (Requirement 2)

`messages.py` defines `SkyeMessage` with the role literal `user | assistant | system | capability` and the subclasses
`UserMessage`, `AssistantMessage`, `SystemMessage`, `CapabilityMessage`, plus `ContentChunk` for multimodal parts (design
"Base contracts"). `completion.py` defines `CompleteRequest` and `CompleteResponse` and the one standard response schema:
content, role, metadata, `TokenUsage`, model identifier and provider, normalized whatever the provider produced; a stream
yields `StreamChunk` values in one format (Requirement 16.4, 16.5). `CapabilityCall` (with its `execute()`, D45) lives here
so adapters in `models` need no import of `tools` (design "Base contracts"). The capability schema (name, description,
parameters) is a pure contract in `capability_schema.py`; the handlers and the registry stay in `tools`. `openai_shape.py`
lets a caller pass messages and tools in the OpenAI shape, which the boundary converts to library types without subclassing
or re-exporting an SDK class.

### Port catalogue (Requirement 2)

Every Port is one module in `interfaces/`, defining an ABC or Protocol with no I/O and no component import (Requirement 3.4).
The catalogue is the steering "Ports" list. The library validates a component's Port compliance at initialization and at
runtime, and supports dynamic registration and discovery of plugins through the `plugin` and `registry` Ports (Requirement
16.1, 16.2, 16.3). Naming follows the 00-rules convention `{Concept}Interface` (`ModelInterface`, `CapabilityInterface`,
`VectorEncoderInterface`, `EventHandlerInterface`, `ContentReaderInterface`); the composition Ports keep their design names
(`Runnable`, `DecisionModel`, `Decision`, `AuthorizerInterface`, `AuthenticationInterface`), matching `interfaces/__init__.py`.

### Errors and logging (Requirement 3)

`exceptions.py` defines `SkyeError` as the root and the specific types `ProviderError` (provider name, status code, original
error as context), `ConfigurationError`, `ValidationError` (field and value), `CapabilityExecutionError` and
`MissingExtraError` (names the extra, subclasses `ImportError`). A wrapped error keeps the original message and stack by being
raised `from` the cause. An error never logs itself (D105): `SkyeError.__init__` emits no record, and the code that
handles an error logs it once with structured `extra={...}` (Requirement 18.1, 18.2). The HTTP layer raises the `ProviderError`
subclass the response calls for, with `provider`, `status_code` and `retry_after` (D104). `log_event.py` defines the shape of the structured log event of a model invocation
(`ModelInvocationEvent`: phase start, end or error; model; provider; correlation id; request and response details, never the
message text; `log_extra()` gives the keys for `logging`'s `extra`) and the telemetry hook Ports (`observer`, `event_handler`)
consumed by `observe`; `SkyeConfig` carries the `correlation_id_header` and `component_log_levels` (a level per component, with
`level_for` and `apply_log_levels`) (Requirement 18.3, 18.4). Emitting the events is the job of `models` and `observe`. The structured-log rule is "message plus `extra={...}`", never f-string
interpolation (00-rules).

### Token usage and cost (Requirement 4)

`completion.py` carries `TokenUsage` (prompt, completion, total) in every `CompleteResponse`, and `ModelConfig` in
`config.py` carries `cost_per_1k_prompt_tokens` / `cost_per_1k_completion_tokens` so a cost estimate can be attached to the
response metadata and custom pricing accepted for private models (Requirement 19.1, 19.2). `base` defines the
`cost_calculator` and `token_counter` Ports; the concrete counter and `CostCalculator` live in `models` (design "Extras and
budgets"), and aggregation across requests is exposed through the response metadata (Requirement 19.3).

### Configuration (Requirement 5)

`config.py` holds `ConfigLoader`, which loads from a dictionary, environment variables, and a YAML or JSON file named by
`SKYE_CONFIG`, applying them in the order file, then environment, then code overrides (highest precedence), so the effective
precedence is code > environment > file (Requirement 20.1, 20.2). `substitute_env_vars` expands `${VAR}` in every string field
and raises `ConfigurationError` when the variable is missing (Requirement 20.4). A YAML file needs the extra `yaml`: `_yaml()`
calls `missing_extra("yaml", extra="yaml")`, so a missing parser raises `MissingExtraError` naming the extra, while JSON needs
nothing (Requirement 20.1; D29). An invalid value raises `ConfigurationError` with details (Requirement 20.3). The prefixed
environment variables are `SKYE_LOG_LEVEL` and `SKYE_CONFIG` (`ALL_ENV_VARS`; the telemetry variable left with the
`enable_telemetry` key, D106); provider credentials never come from a prefixed variable (D18). `SkyeConfig` holds only the keys
that code reads (`log_level`, `correlation_id_header`, `component_log_levels`); an unknown key in the file or the overrides is a
`ConfigurationError` naming it, and `skye.load_config` applies the log levels it reads (D106).

### The `.skye` language: text-level features (Requirement 54.16 to 54.20; D69 to D73)

All of it takes text and returns text or models; nothing reads a file (Requirement 3.2).
- **Comments.** The lexer skips `#` to the end of the line and `/* ... */` / `/** ... **/` over lines (no nesting; an unclosed one is an
  error with its start position). `//` is floor division, not a comment. Inside an expression (`_expression_text` in `parser.py`) a
  comment counts as one space, so the column numbers of the rest stay right.
- **Front matter.** `metadata.split_metadata` cuts the lines between two `---` at the top, reads them with `tomllib`, and gives the parser
  the rest padded with blank lines so the line numbers do not move; a `key: value` line is an error that shows the TOML form. The result is
  `Tree.metadata` / `Document.metadata`; `format_metadata` writes it back and `to_text` puts one blank line after it.
- **`format_text`** (`fmt.py`) re-indents the text (two spaces per open bracket, one level for a line that opens two such as `list({`),
  strips trailing spaces, keeps at most one blank line, exactly one after the front matter, and a final newline; comments and `"""`
  strings are copied as they are. It raises `FormatError` for a text with mistakes, and refuses a result whose `to_text` differs from the
  original's (a different model). It is idempotent. `skeletons.py` returns formatted text.
- **Prompt variables.** The parser keeps a string after a type as a description (`Attribute.description`, `MapEntry.description`) only in
  `variables` and in `output`; the builder puts it in `VariableSpec.description` and `OutputFieldSpec.description`. A structured type
  (`list(T)`, `[T]`, `list({ ... })`, `map({ ... })`, `{ ... }`, nested) becomes `VariableSpec.item_type` / `fields`; its default is the second
  argument (`TypeCall.second`, D83). Inside a structure `map({})` / `list([])` is an optional field with that default and
  `map({ a = string })` a shape (`_is_shape`). `shapes.conform` checks a value and lists every mistake with its path.
- **`output`** blocks (D70) are parsed and checked here into `OutputSpec` (also inside a top-level `when`, as
  `PromptPartSpec(kind="output")`, listed by `PromptSpec.output_variants()`); `prompts` writes the instructions.
- **`each`** has one variable; the checker accepts `loop` inside it (D69).
- **`info.describe_prompt`** builds a `PromptInfo` from a `PromptSpec` and the metadata; `prompt_help` prints it.

### Type safety (Requirement 6)

Every public API in `base` is fully type-hinted with Python 3.10 syntax (`list[str]`, `X | None`), the minimum supported
version (Requirement 21.1; 00-rules). Invalid data raises `ValidationError` carrying the field and the value (Requirement
21.3). Requirement 21.2 — data structures as dataclasses, not pydantic — holds for every `base` contract: `validated.py` gives
the dataclasses what pydantic gave them, in the standard library. `@validated` makes a keyword-only dataclass; when one is built
each field is checked against its annotation and the safe conversions are applied (an `int` for a `float`, a numeric string for
an `int`, an ISO string for a `datetime`, a `dict` for a nested dataclass); a value that cannot be read, a constraint that is
broken (`field(ge=…, le=…, min_length=…)`), a missing argument or one the class does not have raises `ValidationError` naming
the field. `ValidationError` is also a `ValueError`. `from_dict`, `to_dict`, `to_json`, `from_json` and `json_schema` replace
`model_validate`, `model_dump`, `model_dump_json`, `model_validate_json` and `model_json_schema`. A user's structured-output
class (`response_schema`) may still be a pydantic model: `base` only needs the class to be callable.

## Data Models

`base` is where the shared data models are defined, not consumed from elsewhere: the `SkyeMessage` role variants and
`ContentChunk` (`messages.py`); `CompleteRequest`, `CompleteResponse`, `StreamChunk`, `TokenUsage`, `CapabilityCall`,
`CapabilitySchema` (`capability_schema.py`); `HealthMetrics` (`health.py`); and
the configuration models `SkyeConfig`, `ModelConfig`, `RateLimitConfig`, `RetryConfig`, `CooldownConfig`, `RouterConfig`
(`config.py`). All of them are `@validated` dataclasses (Requirement 21.2, D24).

## Error Handling

`SkyeError` is the one root; `ProviderError` wraps a provider failure with its context and status, `ConfigurationError`
reports a bad configuration value or file, `ValidationError` names the field and value, and `MissingExtraError` names the
absent extra while subclassing `ImportError` so existing `except ImportError` sites keep working. Every error is raised `from`
its cause to keep the original message and stack; it is logged once by the code that handles it, never on construction
(Requirement 18.1, 18.2; D105). `http.py` maps a `urllib` HTTP error or transport failure to the `ProviderError` subclass of the
status (429 `RateLimitError`, 5xx `ServerError`, 401/403 `AuthenticationError`, other 4xx `BadRequestError` or
`ContentPolicyError`, a timeout or dropped connection `ProviderTimeoutError`), with `retry_after` from `Retry-After`, keeping
the cause (D104).

## Testing Strategy

Unit tests in `tests/unit` cover the message and completion models, the error hierarchy (wrapping, context, logging), the
configuration loader (precedence, `${VAR}` substitution, invalid values, YAML needing the extra) and each Port's contract,
all with no network. The deterministic budget tests guard the architecture: `test_import_matrix.py` (base imports only the
standard library), `test_clean_import.py` (`import skye` pulls no optional or provider library), `test_codenames.py` (the
codename stratus appears only in the sanctioned places) and `test_steering.py`. `base` carries `http.py`, so the import-matrix
test allows network I/O only in that module.

## Correctness Properties

*A property is a characteristic that should hold across all valid executions; it bridges the user stories and the tests.*

### Property 1: `base` imports only the standard library

For any module under `base`, a static import scan finds no third-party package, so installing `base` installs nothing and
importing it reaches no optional library.

**Validates: Requirement 1 (Requirement 3.1, 3.3, 3.5 of steering)**

### Property 2: `base` does no I/O outside `http.py`

For any module under `base` other than `http.py`, a static scan finds no file, network or process I/O, and no Port performs
I/O or imports a component.

**Validates: Requirement 1 (Requirement 3.2, 3.4 of steering)**

### Property 3: One response shape whatever the provider

For any `CompleteResponse` a component produces, it carries content, role, metadata, token usage, model identifier and
provider, and a stream yields `StreamChunk` values in one format.

**Validates: Requirement 2 (Requirement 16.4, 16.5 of steering)**

### Property 4: A wrapped error keeps its cause and is logged

For any error raised through the `SkyeError` hierarchy, the original message and stack are preserved (raised `from` the cause)
and the error is logged with structured context at an appropriate level.

**Validates: Requirement 3 (Requirement 18.1, 18.2 of steering)**

### Property 5: Configuration precedence and substitution

For any set of sources, the loader applies file, then environment, then code, and expands `${VAR}` in every string; a missing
variable or an invalid value raises `ConfigurationError`, and a YAML file without the `yaml` extra raises `MissingExtraError`.

**Validates: Requirement 5 (Requirement 20.1–20.4 of steering), Requirement 6 (Requirement 21.3)**

## Open items

- **pydantic leaves the core only when the other components move.** `base` no longer imports it (Requirement 3.3), but `tools`,
  `memory`, `utils` and `router` still do; tasks 14.1 to 14.3 of `0-base-structure` remove the dependency (D24, O4).
- **O6 is closed by D32:** `base/http.py` stays in `base` as the one network-I/O module (Requirement 3.2); the import-matrix test
  allows network I/O only there; cloud secret managers are in scope of `auth` over `base/http.py`.
