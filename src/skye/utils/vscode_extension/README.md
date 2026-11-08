# Skye (.skye language)

Support for `.skye` files (routers, flows and prompts of the Skye library) in Visual Studio Code:

- **Highlighting**: blocks, attributes, references (`registry.`, `flow.`, `context.`, `env.`, ...), types, durations, strings,
  `"""` strings and `{{ name | filter }}` interpolation, comments.
- **Diagnostics**: the extension runs `skye check --format json` on the text of the editor (while you type or on save) and
  shows every mistake where it is, with its fix. Exit code 0 means no mistakes, 1 means mistakes found.
- **Formatting**: "Format Document" (and format on save) runs `skye fmt -`; comments, `"""` strings and front matter are kept,
  and a file with mistakes is left as it is.
- **Command**: `Skye: Check current file`.

No dependencies: the extension only runs the `skye` command of the Python package.

## Install

```text
pip install skyeai          # or: uv add skyeai
skye vscode install         # packs this folder into a .vsix and installs it in VS Code
```

## Settings

| Setting | Default | Meaning |
|---|---|---|
| `skye.command` | `["skye"]` | The command to run, one argument per item, no shell: `["uv", "run", "skye"]`, `["python", "-m", "skye.utils.cli"]` |
| `skye.run` | `"onType"` | `"onType"` checks while you type (after a 300 ms pause); `"onSave"` checks when a file is opened or saved |
| `skye.registry` | `[]` | Names known to the registry, passed as `--registry a,b` so that `registry.NAME` is checked |

If the command cannot be run, a warning appears once per session with a button to `skye.command`.

## License

MIT, see `LICENSE.txt`.
