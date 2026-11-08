---
title: "base"
codename: "stratus"
status: current
last_updated: 2026-11-02
---

# base

*codename: stratus*

Messages, completion, errors, config and the Ports (interfaces). Standard library only.

Pages:

- [Configuration](configuration.md)
- [Core interfaces](interfaces.md)
- [Extending Skye](extending.md): which Port to implement, where to register it, which example to copy
- [The .skye language](skye-language.md): grammar, blocks, references, expressions, errors, `skye check` and `skye new`
- [Editor support](editor.md): the VS Code extension for `.skye` files (`skye vscode install`) and `skye check --format json`

## Models are validated dataclasses

The messages, the completion request and response, and the configuration are plain `dataclasses` built with
`@validated` (`skye.base.validated`), in the standard library. When one is built each field is checked and, when it can be
done safely, converted (an `int` for a `float`, a numeric string for an `int`, a `dict` for a nested model); a value that cannot
be read, a broken limit (`field(ge=0, le=2)`), a missing argument or one the class does not have raises `ValidationError`
naming the field. `to_dict`, `to_json`, `from_dict`, `from_json` and `json_schema` replace the pydantic methods
(`model_dump`, `model_validate`, `model_json_schema`). A structured-output class you pass as `response_schema` can still be a
pydantic model.
