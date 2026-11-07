Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, The `.skye` language, Extras and budgets)

# Design Document: prompts

## Overview
`prompts` is the services layer-2 component (codename cirrus). It implements the `PromptBuilderInterface` Port of `base`: versioned
templates, variable injection, few-shot examples, message roles, multimodal content and output schemas, returning `SkyeMessage`
objects that every provider accepts. It follows the liteprompt design (loaders, role-based messages, registry, truncation) with a
standard-library template engine and needs no third-party library and no extra (Requirement 13; D20; Requirement 34.1). The prompt
text can also be written as a `prompt` block of the `.skye` language (D60). This document describes only the internals of `prompts`;
the layer, the allowed imports (`prompts` imports only `base`), the Ports and the extras policy are in the steering sections named
above and are not restated here. `tools` never imports `prompts` (D17).

It supersedes the design of the former `prompts-support` spec (a `Jinja2PromptBuilder` over a Jinja2 environment, pydantic
configuration models, an optional extra `skyeai[prompts]`). That design is recorded as history at the end of this file.

## Architecture
The package is small on purpose: one builder that holds the state, one engine that renders text, one loader that discovers the
bundled templates. Everything else the old design split into classes is a method or a private helper of the builder, because the
builder is the only caller (no second implementation of the Port exists).

| File | Role |
|---|---|
| `prompts/engine.py` | Standard-library template engine: `{{ expr }}`, `{# comment #}`, `if`/`elif`/`else`, `for` (with `loop.index`, `index0`, `first`, `last`, `length`), whitespace control, the built-in filters (`join`, `upper`, `lower`, `title`, `capitalize`, `trim`, `length`, `default`, `string`, `list`, `first`, `last`, `int`, `float`, `replace`, `tojson`) and filters added by the caller. An undefined variable stays visible and is falsy. Nothing is evaluated with `eval`. Realizes Requirement 30.8 and 30.9. |
| `prompts/messages.py` | `BasePromptBuilder`: registry (`name:version`), variable merge, examples, role sections, content and schema configuration, metadata and validation. Re-exports the message types for peers. |
| `prompts/loaders.py` | `load_default_templates(builder)`: reads the files of `prompts/templates/` and registers them as version `1.0`. |
| `prompts/templates/` | The 18 bundled templates (`.jinja` today, `.skye` after task 4). |

Flow of one rendering: look up the latest (or the given) version, extract the variable names, merge defaults, partial variables and
provided variables (the provided ones win, callable defaults are called at each rendering, Requirement 30.4), inject the selected
examples, render with the engine, split the text into role sections, create one message per section (a `UserMessage` when no role is
given, Requirement 32.1).

## Components and Interfaces
### Registry and variables (Requirement 29, 30.1 to 30.6)
`register_template(name, template, version="1.0", from_string=True)` stores the text under `name:version`; a file path with
`from_string=False` raises `FileNotFoundError` with the path. `get_template` returns the latest version or the exact one and raises
`KeyError` for a missing template. A missing required variable raises `ValueError` naming the variable, unless it is in the
allowed-missing set. `partial(**vars)` returns a new builder with those variables bound and leaves the original unchanged.
`compose_templates(name, parts, separator)` joins registered templates into a new one (Requirement 30.7). Version ordering is the
string order of the version (assumption: kept as it is, not changed here).

### Examples (Requirement 31)
`add_examples` stores the examples with an example template; `set_example_selector(name, type, max_examples)` chooses `fixed` or
`random`; the `semantic` selector (similarity) is a gap, see task 3.2. Without a selector the first `max_examples` are used.

### Roles and placeholders (Requirement 32.1 to 32.3)
A rendered text is split into sections at the markers `[SYSTEM]`, `[USER]`, `[ASSISTANT]` (today a text convention). The `.skye`
`prompt` block replaces the markers with real `message "<role>"` blocks (D60). An unknown role must raise a validation error (gap,
task 3.3). `add_message_placeholder` marks where a conversation history is inserted.

### Multimodal content (Requirement 32.4 to 32.6)
`add_image_content` and `add_multimodal_content` record which variables carry content and of which kind. The messages are built with
the typed content blocks of `base` (D46), not with provider-specific dictionaries. Today the configuration is recorded but the
messages carry no content blocks and no format validation exists (gap, task 3.4).

### Output schema (Requirement 33)
`set_output_schema(name, schema)` takes a dataclass or a JSON-schema dictionary (D24: no pydantic) and `get_output_instructions`
returns the text for the model, or an empty text without a schema. Today only a dictionary gets a real instruction (gap, task 3.5).

### Metadata and validation (Requirement 29.4 to 29.6)
`get_template_metadata` returns required and optional variables, examples, content types, roles and the schema; `validate_template`
returns a result without raising. Today the variable extraction reads single braces (`{name}`) and not the `{{ name }}` of the
engine, and the syntax check is a brace count; both must use the engine's parser (gap, task 2.2).

### The `.skye` renderer (version 1 and 2 of the `prompt` block)
What exists: the `prompt` block of version 1 is parsed and checked in `base` (`PromptSpec`: `variables`, `message "<role>"`, `text`,
`when`, `each`, `placeholder`, `allow_missing`) and can be written back. It is not rendered yet.

Version 1, to build in this component (`base` has no template engine): `PromptSpec` plus the variables gives a list of `SkyeMessage`
with real roles, a `placeholder` replaced by the history the caller passes, conditions and loops evaluated with
`skye.base.dsl.evaluate`, `{{ }}` rendered by `prompts/engine.py`; a missing required variable raises the `ValueError` of
Requirement 30.2, defaults and `allow_missing` as in 30.4. A flow step reaches it as `run = prompt.NAME`. The owner decided that the
whole of Jinja is not needed to start: the first thing built is the part an agentic workflow needs, the rest is version 2.

Version 2, measured on the 18 templates (what the language cannot say yet): `else` and `elif` for `when` (28 uses each, `elif` mostly
`X == "value"`); loop variables in `each` (`loop.index` 3 uses, `loop.last` 1 use, plus `first` and `length`); a loop over a dictionary
(`for key, value in collected_data.items()`, 2 uses, needs two loop variables and `items()`); a condition inside a line (20 lines in
11 files, for example `- {{ memory.content }}{% if memory.timestamp %} ({{ memory.timestamp }}){% endif %}`; options are a conditional
expression in `{{ }}` or an inline `when`); an inline loop with a separator (`tool_agent.jinja`; needs a `join` with an attribute).
Already enough in the engine: the filters `default`, `join`, `upper`, nested `each`, attribute access (`table.columns`). Not to be
added (D20): macros, inheritance, include, variable assignment. The fate of `prompts/engine.py` after the conversion is open decision
O35, decided at task 4.5.

## Data Models
No class of the old design survives as a public type. The state of the builder is private dictionaries keyed by template name.
New public data structures (a template entry, a content configuration) are dataclasses, never pydantic (D24), and are added only
when a second caller needs them.

## Error Handling
Errors use the `SkyeError` hierarchy with context (`raise ... from e`). The Requirements fix the visible types: `FileNotFoundError`
with the path (29.1), `KeyError` for a missing template (29.2), `ValueError` naming a missing variable (30.2), a validation error for
bad syntax with the engine's details (29.3), for an invalid role (32.3), for an invalid content format that lists the supported
formats (32.6) and for an invalid schema (33.4). Validation of a template never raises (29.6). The engine's `TemplateSyntaxError` is a
`ValueError` and is wrapped with the template name. Logging is structured (message plus `extra`), not f-strings; the loader's
`print` calls move to the logger (task 2.4).

## Testing Strategy
Tests are in `tests/unit/prompts/` (engine, callable defaults) and `tests/unit/test_prompts_base.py` (builder); the example set is in
`examples/prompts/` and runs under `tests/examples` once rewritten (task 5). Property-based tests use Hypothesis where it is already
a dev dependency and stay optional.

## Correctness Properties
Carried over from the former plan, restated for the current design; each is checked by a test named in the task that owns it.
1. Registering then retrieving a template returns the same text for the same name and version (29.1, 29.2).
2. Variable merging: provided variables win over partial variables, which win over defaults; callable defaults are called per rendering (30.4).
3. Rendering the same template with the same variables gives the same messages when no random selector is used (30.1).
4. A fixed selector always returns the same examples; a random one never returns more than the maximum (31.3).
5. Each role section yields exactly one message of the matching type (32.1).
6. An invalid content format is rejected with the supported formats listed (32.6).
7. Composing templates equals joining their texts with the separator (30.7).
8. The output instructions are empty without a schema and name every field of the schema with one (33.1 to 33.3).
9. Metadata lists exactly the variables found in the template (29.5).
10. A partial builder leaves the original unchanged (30.6).
11. Rendering a `.skye` prompt and its old `.jinja` template gives the same messages after normalising spaces, apart from the real roles (D60; task 4.4).

## History: design of the former `prompts-support` spec (superseded)
Kept as a record; nothing below is a source of truth.
- A `Jinja2PromptBuilder` over a configured Jinja2 environment with macros, inheritance and includes. Superseded by D20 and Requirement 30.9.
- `TemplateRegistry` with an LRU cache of compiled Jinja2 templates, `VariableValidator` (using `meta.find_undeclared_variables`),
  `ExampleSelector` with fixed, random, semantic (embedding) and length-based strategies, `MessageFormatter`, `ContentHandler`,
  `SchemaValidator` as separate classes. Replaced by one builder (see Architecture); the strategies and the cache remain as tasks.
- `PromptBuilderConfig` and `Jinja2Config` as pydantic models, an exception family under `PromptBuilderError` (`TemplateNotFoundError`,
  `TemplateValidationError`, `VariableValidationError`, `ContentValidationError`, `SchemaValidationError`). Superseded by D24 and by the
  error types fixed in Requirements 29 to 33.
- An optional extra `skyeai[prompts]`. Superseded: the extra is empty (`known_empty` in `budgets.toml`).
- A `Pydantic` model as the output schema. Superseded by D24 (Requirement 33.1).
