# Using Skye from Python

```python
import skye
from skye import UserMessage

client = skye.provider("openai", api_key="sk-...")   # "anthropic", "bedrock", "azure", "google", "cohere" work the same way
response = client.complete(messages=[UserMessage(content="Hello!")], model="gpt-4")
print(response.content)
```

## Routers

- From a file: `ModelRouter.from_file("router.skye", name="main")`. A `.json` file with the configuration object also works. **YAML is not read.**
- From Python: `ModelRouter({"fast": ["openai/gpt-4o-mini", "anthropic/claude-haiku"]})`.
- Back to a file: `router.to_skye("main")` returns the `router` block as `.skye` text and `router.to_config()` the configuration dictionary
  (`ModelRouter.from_config_dict` rebuilds the router from it). Use them to move a router built in Python to a file. **Secrets are not
  exported:** a key written as `env.NAME` comes back as `env.NAME`; a key written in clear is left out unless `include_secrets=True`.
  The text has no comments, and extra fields of a target are not exported.

## Reading and writing a `.skye` text

The parser lives in `skye.base.dsl` and takes text, not a path: `parse`, `build`, `check_text`, `block_schema`, `build_cached`, and the
skeleton functions `new_router`, `new_flow`, `new_prompt`, `skeleton`. `to_text(spec)` is the opposite of `build`: it writes a router, flow or
prompt spec (or a whole document) back as `.skye` text that passes `skye check` and builds an equal spec (comments are not kept);
`format_duration(seconds)` gives `"30s"`, `"5m"` or `"24h"` for a number of seconds. The front matter of a file is in
`build(text).metadata` (a dict); `split_metadata(text, filename)` returns `(metadata, text_without_it, diagnostics)` and
`format_metadata(metadata)` writes it back (`to_text(document)` keeps it). `format_text(text)` is `skye fmt` (comments kept; raises
`FormatError` with `.diagnostics` for a text with mistakes). `skye.utils.skye_files.load_document(path)` reads a file
and skips the parse when the file did not change; the documents it returns are shared and read-only.

## Prompt help

`from skye.prompts import describe_prompt, prompt_help, PromptInfo`: `describe_prompt(document.prompt("chat"), document.metadata)`
returns a `PromptInfo` (inputs with type, default and description; placeholders; roles; output fields) and `prompt_help(spec, metadata)`
the same as plain text (what `skye prompt info` prints). `BasePromptBuilder().help("planner_agent")` / `.describe(name)` work on a
registered template, bundled ones included. Import these from `skye.prompts`, not from `skye.base.dsl.info`.

## MCP resources

`from skye.tools import ResourceProviderInterface, Resource`: the Port that lists resources and reads one by URI (`Resource` has `uri`,
`mime_type`, and `text` or `data`); the MCP clients of `skye.tools` implement it.

## Loading a file

- `skye.load("app.skye")` reads, parses and checks a file and returns the `Document` (`routers`, `flows`, `prompts`; `document.flow("name")`,
  `document.router()`, `document.prompt()`). A file with mistakes raises `ConfigurationError` whose message lists every one as
  `file:line:column reason fix`. Pass `registry_names=[...]` to check `registry.NAME` references. An unchanged file is not parsed again.
- `Flow.from_file("app.skye", name="research", registry={"planner": planner})` (also `skye.Flow`, or `from skye.flows import Flow`) loads one
  flow. `name` is optional when the file has one flow; `registry` is a dictionary of name to step, and `registry.NAME` must be one of its keys.
  `Flow.from_text(text, name=..., registry=..., filename=...)` does the same for a text. A `Flow` has `.spec`, `.name`, `.registry`,
  `.check()` (the mistakes now, with the registry keys) and `.to_text()`.

## Not built yet

Running a flow: `Flow.run(...)` raises `NotImplementedError` (the flow runtime belongs to the spec `3-runtime-flows`). `skye.load` and
`Flow.from_file` exist and validate, so a flow file is checked and built into specs, but it does not run. Say so when asked to run one, and
offer to check it and to write the steps as registry functions.
