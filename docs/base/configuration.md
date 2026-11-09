---
title: "Configuration"
status: current
last_updated: 2026-11-02
---

# Configuration

How Skye resolves configuration. Configuration loading lives in `base/config.py` (standard
library only).

## Sources, in priority order

1. values passed in code (highest priority);
2. environment variables, prefixed `SKYE_` (for example `SKYE_LOG_LEVEL`);
3. a configuration file (JSON). The library reads no YAML: a `.yaml` or `.yml` file raises a `ConfigurationError` that asks for `.skye` or JSON. A router is written as a `router` block in a `.skye` file (see the [language guide](skye-language.md)).

A value set in code overrides the environment, which overrides the file.

## Environment-variable substitution

Both file and in-code configuration support `${VAR_NAME}` substitution, resolved at load
time. Use it for every secret — never commit a key.

```json
{
  "log_level": "INFO",
  "models": {
    "gpt-4": {"provider": "openai", "api_key": "${OPENAI_API_KEY}", "temperature": 0.7}
  }
}
```

```python
from skye.router import ModelTarget

target = ModelTarget(
    model="gpt-4",
    provider="openai",
    api_key="${OPENAI_API_KEY}",  # substituted at load time
)
```

For a router (routes, targets, fallbacks, retry policies) write a `router` block in a `.skye` file: see the
[routing guide](../router/routing-guide.md). For secret handling rules see the `security`
steering.

## Configuration examples

Skye supports multiple configuration sources with precedence: code > environment > file.

### Environment Variables

```bash
export SKYE_LOG_LEVEL=INFO
export OPENAI_API_KEY=sk-...  # provider credentials use the provider-standard variable
export SKYE_ENABLE_TELEMETRY=true
```

### Configuration File

```json
{
  "log_level": "INFO",
  "enable_telemetry": true,
  "models": {
    "gpt-4": {
      "provider": "openai",
      "api_key": "${OPENAI_API_KEY}",
      "temperature": 0.7,
      "max_tokens": 2000,
      "rate_limits": {"requests_per_minute": 60, "tokens_per_minute": 90000}
    }
  }
}
```

### Load Configuration

```python
import skye

# Reads skye.json (or the file SKYE_CONFIG names when no path is given), then the environment, then the overrides
config = skye.load_config("skye.json", overrides={"log_level": "DEBUG"})
```

`skye.load_config` is the function that opens the file. `skye.config.ConfigLoader` takes the text of the file and opens nothing,
because `base` does no file I/O: use it when the configuration comes from somewhere else (a secret store, a test, a string).

```python
from skye.config import ConfigLoader

config = ConfigLoader.from_text('{"log_level": "INFO"}', source="inline")
config = ConfigLoader.load(overrides={"log_level": "ERROR"})  # environment and code only
```

