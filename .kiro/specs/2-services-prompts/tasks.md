# Implementation Plan: prompts

## Overview
Milestones in build order for the `prompts` component (codename cirrus): what exists first (builder, registry, engine, loaders),
then the gaps against Requirements 29 to 34, then few-shot, roles, content and schema, then the `.skye` prompts of decision D60, then
the stale examples and the licence notice. Status is judged from the code in `src/skye/prompts` and the tests in
`tests/unit/prompts` and `tests/unit/test_prompts_base.py`, not from the checkboxes of the former `prompts-support` plan, which
described a Jinja2 and pydantic design (see the history at the end of `design.md`). The former checkpoint tasks are dropped: they
produced nothing. Each task cites the steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the
decision it honors. Task IDs cited from other documents are `prompts:N.k` (the former `prompts-support` task 3 is now
`prompts:5`, the former task 18 is now `prompts:4`).

## Tasks
- [x] 1. Builder, registry and engine (what exists)
  - [x] 1.1 Package structure and exports: `PromptBuilderInterface`, `BasePromptBuilder`
    - Evidence: `src/skye/prompts/__init__.py`; `tests/unit/test_exports.py`.
    - _Requirements: 34.2_
  - [x] 1.2 `BasePromptBuilder` implements the Port with a versioned registry (`name:version`), file registration and latest-version lookup
    - Evidence: `src/skye/prompts/messages.py`; `tests/unit/test_prompts_base.py` (`test_register_and_get_template`, `test_template_versioning`, `test_file_template_loading`, `test_nonexistent_template_error`).
    - _Requirements: 29.1, 29.2, 29.4_
  - [x] 1.3 Standard-library template engine (D20): `{{ }}`, `if`/`elif`/`else`, `for` with `loop.*`, filters, whitespace control, custom filters, no `set`/`macro`/`include`
    - Evidence: `src/skye/prompts/engine.py`; `tests/unit/prompts/test_engine.py` (includes `test_no_jinja_imports_in_prompts_package`).
    - _Requirements: 30.8, 30.9, 34.1; D20_
  - [x] 1.4 Defaults, callable defaults, allowed-missing variables and `partial`
    - Evidence: `src/skye/prompts/messages.py`; `tests/unit/prompts/test_callable_defaults.py`; `tests/unit/test_prompts_base.py` (`test_render_with_defaults`, `test_render_with_missing_allowed_variables`, `test_partial_binding`, `test_partial_with_callable`).
    - _Requirements: 30.3, 30.4, 30.6_
  - [x] 1.5 Role sections from the `[SYSTEM]`, `[USER]`, `[ASSISTANT]` markers, one message per section, `UserMessage` by default
    - Evidence: `src/skye/prompts/messages.py` (`_create_messages`); `tests/unit/test_prompts_base.py` (`test_role_based_messages`).
    - _Requirements: 32.1_
  - [x] 1.6 Fixed and random example selectors, example template, composition of templates
    - Evidence: `src/skye/prompts/messages.py`; `tests/unit/test_prompts_base.py` (`test_add_examples`, `test_custom_example_template`, `test_example_selectors`, `test_template_composition`).
    - _Requirements: 31.1, 31.3, 31.4, 30.7_
  - [x] 1.7 Loader for the bundled templates, sample templates and test data
    - Evidence: `src/skye/prompts/loaders.py`; `src/skye/prompts/templates/` (18 files); `tests/unit/prompts/test_data/`; `tests/unit/test_prompts_base.py` (`test_default_templates_work`, `test_agent_templates`).
    - _Requirements: 29.1, 29.4_

- [ ] 2. Registry, variables and validation: close the gaps
  - [ ] 2.1 Extract variables with the engine's parser, so `{{ name }}`, `if` conditions and `for` sources are found (today `_extract_variables` reads single braces)
    - Note: `src/skye/prompts/messages.py` `_extract_variables` uses the pattern `\{([^}]+)\}`; for a block template it returns expressions and not names, which also affects metadata and the required-variable check.
    - _Requirements: 30.5, 29.5_
  - [ ] 2.2 Validate a template with the engine's parser: syntax errors with the engine's details at registration, validation results without raising
    - Note: `validate_template` counts braces; `register_template` does not parse the template.
    - _Requirements: 29.3, 29.6_
  - [ ] 2.3 Raise `ValueError` naming every missing required variable for block templates too (today an undefined variable stays visible in the output)
    - _Requirements: 30.2_
  - [ ] 2.4 Errors in the `SkyeError` hierarchy with context, structured logging instead of `print` in `loaders.py`, `${VAR}` substitution in configuration
    - _Requirements: 34.3_
  - [ ] 2.5 Compile at registration and reuse the compiled template; cache the variable list and the formatted examples; keep memory bounded for many templates
    - Note: `render_template` parses the text at every call; there is no cache.
    - _Requirements: 34.4, 34.5, 34.6_
  - [ ] 2.6 Remove `register_jinja_macro` (macros are not supported) and decide the name of `register_jinja_filter` with the owner (public surface, `0-base-uxui`)
    - _Requirements: 30.8, 30.9; D20_
  - [ ]* 2.7 Property tests: registry round trip, variable merge precedence, partial immutability (properties 1, 2, 10 of `design.md`)
    - _Requirements: 29.2, 30.4, 30.6_

- [ ] 3. Few-shot examples, roles, content and output schema: close the gaps
  - [ ] 3.1 Format and inject examples with the example template at rendering; no selector uses all examples up to a default limit
    - Note: `render` injects examples as the variable `examples`; the default limit is 3 in `_select_examples` and 5 in `set_example_selector`; make it one value.
    - _Requirements: 31.1, 31.4_
  - [ ] 3.2 Semantic example selector by similarity, with the embedder passed in as a Port callable (no import of `models`)
    - _Requirements: 31.2_
  - [ ] 3.3 Insert a conversation history at a message placeholder; reject an invalid role with a validation error
    - Note: `add_message_placeholder` records the placeholder and nothing reads it at rendering; an unknown role falls back to a user message.
    - _Requirements: 32.2, 32.3_
  - [ ] 3.4 Multimodal content: process image URL, base64 and file path into the typed content blocks of `base` (D46), keep the content type, reject an invalid format listing the supported ones
    - Note: `add_image_content` and `add_multimodal_content` record the configuration only.
    - _Requirements: 32.4, 32.5, 32.6; D46_
  - [ ] 3.5 Output schema from a dataclass or a JSON-schema dictionary; instructions list every field; invalid schema raises a validation error
    - Note: `get_output_instructions` returns a generic text for anything that is not a dictionary.
    - _Requirements: 33.1, 33.2, 33.3, 33.4; D24_
  - [ ] 3.6 Create and format `CapabilityMessage` objects when the builder is used with capabilities
    - _Requirements: 34.2_
  - [ ]* 3.7 Property tests: fixed and random selectors, one message per role section, composition equals join, schema instructions (properties 4, 5, 7, 8 of `design.md`)
    - _Requirements: 31.3, 32.1, 30.7, 33.3_

- [ ] 4. Prompts in the `.skye` language (decision D60; the parser exists, the renderer does not)
  - [x] 4.1 The reduced `prompt` block of version 1 is parsed, checked and written back: `variables` (typed, with defaults), `message "<role>"`, `text`, `when`, `each`, `placeholder`, `allow_missing`, interpolation `{{ expr }}`
    - Evidence: `src/skye/base/dsl/specs.py` (`PromptSpec`); `src/skye/base/dsl/emit.py`; `tests/unit/dsl/test_emit.py`, `tests/unit/dsl/test_conformance.py`.
    - _Requirements: 30, 31, 32, 33; D60_
  - [ ] 4.2 Renderer in `skye.prompts` (not in `base`): `PromptSpec` plus variables gives a list of `SkyeMessage` with real roles, a `placeholder` replaced by the history the caller passes, `when` and `each` evaluated with `skye.base.dsl.evaluate`, `{{ }}` rendered by `prompts/engine.py`, required and default variables as in 30.2 and 30.4; a flow step reaches it as `run = prompt.NAME`
    - _Requirements: 30.1, 30.2, 30.4, 32.1; D60_
  - [ ] 4.3 Convert the 18 bundled templates in `src/skye/prompts/templates/` from `.jinja` to `.skye`, one by one (`chat`, `classification`, `code_agent`, `code_generation`, `explanation`, `form_agent`, `main_agent`, `memory_agent`, `multimodal_agent`, `ner`, `procedure_agent`, `question_answering`, `reasoning_agent`, `relation_extraction`, `sql_generation`, `summarization`, `tabular_extraction`, `tool_agent`); what version 1 cannot say is listed in `design.md` as version 2 and stays `.jinja` until the language grows
    - _Requirements: 30, 31, 32, 33; D60_
  - [ ] 4.4 Equivalence test: render each old and each new prompt with the same data (variable combinations that cover every `if` and `for` branch) and compare the messages after normalising spaces and blank lines; list each intended difference (real roles instead of text markers) in the test
    - _Requirements: 30.1, 32.1; D60_
  - [ ] 4.5 Keep `prompts/engine.py` for user `.jinja` templates and for the `{{ }}` interpolation of the new blocks; once 4.4 passes, decide with the owner open decision O35 (restrict the engine to interpolation only, control tags declared obsolete)
    - _Requirements: 30.8; D20; O35_
  - [ ] 4.6 `loaders.py` discovers `.skye` prompt files next to the `.jinja` ones; remove the `.jinja` copies of the bundled templates when 4.4 passes
    - _Requirements: 29.1, 29.4; D60_
  - [ ] 4.7 Update the existing prompt tests and the docs section `docs/prompts/` to the new files
    - _Requirements: 15.5; D60_

- [ ] 5. Rewrite the stale `examples/prompts/` set off Jinja2 (found 2026-11-03 in the example-coverage review)
  - [ ] 5.1 Rewrite the twelve files under `examples/prompts/` against the standard-library engine (`{{ }}`, `if`/`elif`/`else`, `for`, filters; no macros, inheritance, include or variable assignment), drop the Jinja2 wording, import normally without `sys.path` changes
    - Note: they use a `MockPromptBuilder` alias and manipulate `sys.path`.
    - _Requirements: 24.4, 24.5, 30.9; D20_
  - [ ] 5.2 Remove the `MockPromptBuilder` alias from `skye.prompts` once no example uses it
    - _Requirements: 24.5_
  - [ ] 5.3 Make each example runnable under `tests/examples` and remove `prompts` from `KNOWN_FOLDERS` and `EXEMPT_FOLDERS` of the example budget tests (`test_example_output_style.py`, `test_example_readmes.py`, `test_example_size.py`) and from the skip list of `test_examples_offline.py`; a budget list may only shrink
    - _Requirements: 24.3, 24.4_

- [ ] 6. Licence and attribution
  - [ ] 6.1 Check whether anything in `prompts` was taken from prompt-poet (MIT); if so add the notice file and a comment at the copied code, otherwise record in the task that ideas and API shapes only were reused
    - Note: no prompt-poet notice exists in the repository today. liteprompt is the owner's own earlier project (private repo `ggiallo28/liteprompt`, MIT), so reusing its code needs no third-party notice; it is a source for the gaps in milestones 2 and 3 (registry, loaders, truncation, example selectors), to be read when those tasks start.
    - _Requirements: 14.2, 14.3_
