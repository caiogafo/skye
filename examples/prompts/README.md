# prompts

What you learn: prompts written in the `.skye` language (the library's bundled prompts use it too): `message` blocks with real roles, `when` / `each`, filters, few-shot turns, `output` blocks, and the bundled agent prompts. Each Python file loads the `.skye` file of the same name. Every `.skye` file declares its variables with a type and a description (structured ones with their fields, like `notes = list({ role = string, text = string }, [])`), and ends with a `/** Example: ... **/` comment showing a call that renders. Read in this order:

1. `basic_rendering.py` with `basic_rendering.skye`: register a prompt file, render it to messages, defaults, a partial builder, an optional variable and the error for a missing one
2. `control_flow.py` with `control_flow.skye`: `when` / `when not`, `each` with `loop.index` and `loop.last`, the entries of a map, the filters `upper`, `join` and `map`
3. `message_roles.py` with `message_roles.skye`: `message "system"` / `"user"`, `placeholder "history"` filled with message objects or dicts (conversation history is always this placeholder, never a variable), a role taken from data
4. `few_shot.py` with `few_shot.skye`: worked examples turned into user and assistant turns by `each`
5. `output_schema.py` with `output_schema.skye`: an `output` block with field descriptions as JSON, a table and XML, the bundled `structured_output`, and a dataclass schema on a prompt with no `output` block
6. `agent_prompt.py`: the bundled `planner_agent`, whose tools and memory sections appear only when given
7. `group_chat.py`: three agents in one conversation with the bundled `group_chat_participant` and `group_chat_manager`, driven by a scripted fake model
8. `validation.py`: the diagnostics (line, column, fix) of a badly written prompt, as `skye check` reports them; `skye fmt` lays a file out and `skye fmt --check` tells whether it already is

Run: `python examples/prompts/control_flow.py`

What you see: the rendered messages and instructions; nothing calls a model.

What you need: `pip install skyeai`; no key and no network.
