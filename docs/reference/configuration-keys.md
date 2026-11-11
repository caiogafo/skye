---
title: "Configuration keys"
status: current
---

# Configuration keys

This page lists every key of the Skye configuration with its type, its default and the environment variable that sets it, so you can
write a configuration file or set the environment with nothing left to guess.

The configuration is a `SkyeConfig` (public in `skye.config`). You build it with `skye.load_config(path, overrides=...)`, which reads
a JSON file, then the environment, then your overrides. A router is not configured here: write a `router` block in a `.skye` file
(see [.skye language](skye-language.md#router)).

## Sources and precedence

Highest first:

1. **code**: the `overrides` dictionary you pass to `skye.load_config` or `ConfigLoader.load`;
2. **environment**: the `SKYE_` variables below;
3. **file**: a JSON object. `skye.load_config(path)` reads `path`; with no path, the file named by `SKYE_CONFIG`; with neither, only
   the environment and the overrides count.

The file must have the suffix `.json`. A `.yaml` or `.yml` file raises `ConfigurationError`: Skye reads no YAML. Inside the file and
the overrides, `${VAR}` is replaced by the environment variable `VAR` when the configuration loads; a variable that is not set raises
`ConfigurationError`. Every invalid value raises `ConfigurationError` naming the field, and a key that is not in the table below
raises `ConfigurationError` naming the key (in the file and in the overrides alike): a mistyped key is never ignored.

`skye.load_config` applies the log levels it reads: the `skye` logger takes `log_level` and each `skye.<component>` logger its entry
of `component_log_levels`.

```python
--8<-- "examples/basic/configuration.py:15:46"
```

The full example is [`configuration.py`](https://github.com/ggiallo28/skye/blob/main/examples/basic/configuration.py).

## Environment variables

Skye reads two variables of its own:

| Variable | Sets | Values |
|---|---|---|
| `SKYE_LOG_LEVEL` | `log_level` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `SKYE_CONFIG` | the path of the JSON file `skye.load_config()` reads when you give no path | a file path |

No other `SKYE_` variable is read.

Provider credentials never come from a `SKYE_` variable. Each provider reads its own standard variable:

| Provider | Variables |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, or `AZURE_TENANT_ID` with `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` (or `AZURE_CLIENT_CERTIFICATE_PATH`, `AZURE_FEDERATED_TOKEN_FILE`) |
| Google | `GOOGLE_API_KEY`, `GOOGLE_OAUTH_ACCESS_TOKEN` or `GOOGLE_APPLICATION_CREDENTIALS` |
| Cohere | `COHERE_API_KEY` |
| Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, or `AWS_BEARER_TOKEN_BEDROCK`; the container and web-identity variables of AWS also work |

[Credentials and secrets](../guides/security/credentials.md) explains every credential source.

## Keys (`SkyeConfig`)

| Key | Type | Default | Environment | Meaning |
|---|---|---|---|---|
| `log_level` | string | `"INFO"` | `SKYE_LOG_LEVEL` | level of the `skye` logger |
| `component_log_levels` | map of string | `{}` | | level per component, for example `{"router": "DEBUG"}`; a component not listed uses `log_level`; an unknown level raises an error |
| `correlation_id_header` | string | `"X-Correlation-ID"` | | HTTP header that carries the correlation id of an invocation |

These are all the keys. A key that no code reads is not a key: it comes back only with the code that reads it. Model, routing, retry
and rate-limit settings are not configured here: they belong to the router, written as a `router` block in a `.skye` file.

`skye.load_config` sets the log levels for you. A configuration built with `ConfigLoader` (below) does not touch the loggers: call
`config.apply_log_levels()` to set the level of the `skye` logger and of each listed `skye.<component>` logger.
`config.level_for("router")` returns the level one component uses.

## A complete file

```json
{
  "log_level": "INFO",
  "component_log_levels": {"router": "DEBUG", "tools": "WARNING"},
  "correlation_id_header": "X-Request-ID"
}
```

## Without a file

`skye.config.ConfigLoader` takes the text of a file and opens nothing, so you can build the configuration from a secret store, a test
or a string:

```python
from skye.config import ConfigLoader

config = ConfigLoader.from_text('{"log_level": "INFO"}', source="inline")
config = ConfigLoader.load(overrides={"log_level": "ERROR"})  # environment and code only
```

`ConfigLoader.load()` with no text raises `ConfigurationError` when `SKYE_CONFIG` is set, because it reads no file: use
`skye.load_config()` then.

## See also

- [Configuration guide](../guides/configuration.md): the configuration file and logging, step by step.
- [Credentials and secrets](../guides/security/credentials.md): where keys come from.
- [skye API reference](api/skye.md): `load_config` and the configuration classes.
