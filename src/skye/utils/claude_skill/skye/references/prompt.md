# Prompts

A prompt block declares its variables and builds messages with real roles. Conditions and loops are blocks (`when`, `each`), not template
tags; only `{{ name }}` (with the filters of the template engine) appears in the text.

```skye
prompt "chat" {
  variables = { persona = string("a helpful AI assistant"), domain = string(""), guidelines = list, user_message = string }

  message "system" {
    text = "You are {{ persona }}."
    when domain { text = "Specialized in {{ domain }}." }
    when guidelines {
      text = "Please follow these guidelines:"
      each guideline in guidelines { text = "- {{ guideline }}" }
    }
  }

  placeholder "history"                     # the conversation history is inserted here at run time

  message "user" { text = "{{ user_message }}" }
}
```

## Rules

- `variables = { name = type }` or `name = type(default)` (`string`, `number`, `bool`, `list`, `map`). A variable without a default is
  required. `allow_missing = ["name"]` lists variables the caller may leave out.
- `message "role" { ... }`: the roles are `system`, `user` and `assistant`. A role can come from data: `message turn.role { ... }` inside `each`.
- Inside a message, `text = "..."` may appear several times, interleaved with `when` and `each` blocks; the parts are joined in order, one per line.
- Variables are written bare here (not `context.x`). A variable that is not declared is an error.
- **Convert a Jinja template** by turning each `{% if x %}...{% endif %}` into `when x { text = "..." }`, each `{% for x in xs %}` into
  `each x in xs { ... }`, and the `[SYSTEM]` / `[USER]` markers into `message "system"` / `message "user"`. Do not leave `{% %}` tags in the text.

## Not available yet (version 2)

Few-shot `examples`, multimodal `content`, `output` schema, and `from` / `bind` / `parts` / `separator` (partial and composed prompts) are rejected with
"not available in this version". Say so and keep that part in Python.
