---
title: "prompts"
codename: "cirrus"
status: current
last_updated: 2026-11-08
---

# prompts

*codename: cirrus*

Prompt templates rendered into role-based messages (`SystemMessage`, `UserMessage`, `AssistantMessage`, `CapabilityMessage`).
Part of the base install: the template engine is the standard library's, with no Jinja2 (decision D20).

## Two ways to write a prompt

- **A `.skye` prompt block** (decision D60): variables with types and defaults, `message "role"` blocks with real roles, `when` and
  `each` blocks, a `placeholder` for the conversation history and `{{ }}` interpolation. See the `prompt` section of
  [the .skye language](../base/skye-language.md).
- **A text template** registered on `BasePromptBuilder`: `{name}` (str.format) or `{{ name }}` with `{% if %}` / `{% for %}` and
  filters; roles come from `[SYSTEM]`, `[USER]`, `[ASSISTANT]` and `[CAPABILITY name id]` lines. Macros, inheritance, include and
  variable assignment are not supported (Requirement 30.9).

```python
from skye.prompts import BasePromptBuilder, load_prompt, render_prompt

builder = BasePromptBuilder()                        # loads the bundled templates
messages = builder.render("chat", {"user_message": "Hello"})

spec = load_prompt(open("prompts.skye").read(), "chat")
messages = render_prompt(spec, {"user_message": "Hello"}, history={"history": past_messages})
```

A missing required variable raises `ValueError` naming every missing one. A template with bad syntax is refused when it is
registered, with the engine's details; `validate_template` reports problems without raising.

## Builder features

- Versions (`name:version`, the latest by default), `compose_templates`, `partial`, defaults (callables are called at each
  rendering; `${VAR}` is substituted in configured values) and allowed-missing variables.
- Few-shot examples injected as `examples`, with a `fixed`, `random` or `semantic` selector (the semantic one takes an
  `embedder` callable; `skye.models` is never imported). A `.skye` prompt that declares `examples` as a list gets the selected
  examples as the list of dicts; a text template (or a `.skye` prompt with `examples = string`) gets them formatted with the
  example template.
- A history at a `[PLACEHOLDER name]` line, images in `UserMessage.images` (`url`, `base64`, `path`), content types in the
  message metadata.
- Output instructions from a dataclass or a JSON-schema dictionary (`set_output_schema(name, schema, output_format="json")`, with `"table"` and `"xml"` too; `get_output_instructions`), or from the `output` block of a `.skye` prompt (`output_instructions`, see [the language page](../base/skye-language.md)). The filters `tojson`, `toxml` and `totable` put data into a prompt.

## Help: what a prompt takes and gives back

`skye prompt list` lists the bundled prompts (name, title, version, description); `skye prompt info NAME|FILE` shows one: its inputs
(type, `required` / `optional` / `= default`, and the description written after the type in `variables`), its history placeholders, its
messages in order and its output. `--name PROMPT` picks a prompt of a file that holds several, `-` reads stdin, `--json` prints the
`PromptInfo`. Exit 2 for an unknown name or file, 1 (with the diagnostics) when the file has mistakes.

```text
$ skye prompt info planner_agent
planner_agent — Planner agent (plan and execute) (1.0)
One agent that breaks a task into a numbered JSON plan, carries out one step at a time, and revises the rest of the plan until the task is done.
Tags: agent, planning

Inputs
  system_prompt      string  = ""      Replaces the default system instructions when not empty
  task               string  required  The task to accomplish
  phase              string  = "plan"  "plan", "execute" or "replan"
  ...

History
  history

Messages
  system, history, user

Output
  free text
```

From Python, `describe_prompt(spec, metadata=None)` returns a `PromptInfo` (`name`, `title`, `description`, `version`, `tags`,
`inputs` as `InputInfo`, `placeholders`, `roles`, `output` as `OutputInfo` with nested `OutputFieldInfo` fields, or `None` for free
text or conditional outputs, and `outputs`, the conditional outputs written inside `when` blocks, each `OutputInfo` with its
`condition`; the help prints one `Output (when <condition>): <format>` section for each) and `prompt_help(spec, metadata=None)` the text above; pass `document.metadata` for the front matter.
`BasePromptBuilder.describe(name)` and `.help(name)` do the same for a registered template: a `.skye` one with its front matter, a text
template with its variables (type `any`), its `[ROLE]` / `[PLACEHOLDER x]` markers and the output of `set_output_schema`.

A structured variable (`categories = list({ name = string, description = string("") })`, see
[the .skye language](../base/skye-language.md)) is shown with its fields indented below it, and `render_prompt` checks the value
given against that shape.

`roles` lists the top-level messages and placeholders as written: a role (`"system"`), a role expression (`"turn.role"`) or a
placeholder name (`"history"`); a message inside an `each` ends with `*` (`"user*"`, zero or more), one inside a `when` with `?`
(`"system?"`), and the marks add up (`"user*?"`).

## Bundled templates

Task prompts (converted from `.jinja`): `chat`, `classification`, `code_agent`, `code_generation`, `explanation`, `main_agent`,
`memory_agent`, `ner`, `procedure_agent`, `question_answering`, `reasoning_agent`, `relation_extraction`, `sql_generation`,
`summarization`, `tabular_extraction`, `form_agent`, `multimodal_agent`, `tool_agent`. Every bundled prompt is a `.skye` file;
the builder still reads `.jinja` (and `.txt`, `.tmpl`) templates of your own.

Agent prompts (and the older `*_agent` templates too), all with optional `tools` and optional memories of every kind (`episodic_memory`, `semantic_memory`,
`procedural_memory`, `persona_memory`, `working_memory`) and a `placeholder "history"`:

| Kind | Templates |
|---|---|
| smolagents style | `smol_code_agent`, `smol_tool_calling_agent`, `smol_planning`, `smol_managed_agent` |
| Reasoning | `chain_of_thought_agent`, `tree_of_thoughts_agent`, `self_reflection_agent`, `planner_agent` |
| Supervisors | `supervisor_router`, `supervisor_planner`, `supervisor_reviewer`, `supervisor_hierarchical` |
| Shared conversation | `group_chat_participant`, `group_chat_manager`, `group_chat_summarizer` |
| Memory upkeep | `memory_update_agent` (add / update / delete operations for every memory kind from the conversation), `memory_consolidation_agent` (merge, resolve, distil), `working_memory_agent` (the scratchpad of the current task) |

### Shared shapes and removed names

Every bundled prompt that takes tools or memories declares them with the same structured types, so one value fits all of them
(the optional fields default to empty):

```skye
prompt "agent" {
  variables = {
    tools             = list({ name = string, description = string, parameters = map({}), returns = string("") }, [])
    persona_memory    = list({ content = string, source = string("") }, [])
    episodic_memory   = list({ content = string, timestamp = string(""), source = string("") }, [])
    semantic_memory   = list({ content = string, source = string("") }, [])
    procedural_memory = list({ name = string(""), content = string(""), steps = list(string, []) }, [])
    working_memory    = list({ content = string }, [])
  }
  message "user" { text = "..." }
}
```

Each field also has a description (see `skye prompt info NAME`). In `memory_update_agent`, `memory_consolidation_agent` and
`working_memory_agent` every memory item also has a first field `id = string("")`, the item to update or delete. A value of the
wrong shape is an error that names the path (`tools[0].description: missing`).

The conversation history is always `placeholder "history"`, filled with `history={"history": [...]}` or the variable `history`.
These names are removed, with no alias: `chat_history` and `conversation_history` (use the `history` placeholder),
`declarative_memory` (use `semantic_memory`), `procedural_memories` and `procedures` (use `procedural_memory`).

Each bundled file ends with a usage example, a `/** ... **/` comment with a `builder.render("<name>", {...})` call whose values
render as they are.

In a shared conversation each agent renders `group_chat_participant` with the transcript and its `triggers`; it answers the pass
token (`[PASS]`) unless the latest messages concern it or mention `@name`. `group_chat_manager` can instead pick the next speakers.

Examples: [examples/prompts](https://github.com/ggiallo28/skye/blob/main/examples/prompts/README.md).
