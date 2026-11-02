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
3. a configuration file (YAML or JSON).

A value set in code overrides the environment, which overrides the file.

## Environment-variable substitution

Both file and in-code configuration support `${VAR_NAME}` substitution, resolved at load
time. Use it for every secret — never commit a key.

```yaml
# skye.yaml
log_level: INFO
models:
  gpt-4:
    provider: openai
    api_key: ${OPENAI_API_KEY}
    temperature: 0.7
```

```python
from skye.router import ModelTarget

target = ModelTarget(
    model="gpt-4",
    provider="openai",
    api_key="${OPENAI_API_KEY}",  # substituted at load time
)
```

For router-specific YAML (routes, targets, fallbacks, retry policies) see the
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

```yaml
# skye.yaml
log_level: INFO
enable_telemetry: true

models:
  gpt-4:
    provider: openai
    api_key: ${OPENAI_API_KEY}
    temperature: 0.7
    max_tokens: 2000
    rate_limits:
      requests_per_minute: 60
      tokens_per_minute: 90000
```

### Load Configuration

```python
from pathlib import Path
from skye.base.config import ConfigLoader

config = ConfigLoader.load(
    config_path=Path("skye.yaml"),
    overrides={"log_level": "DEBUG"}
)
```

