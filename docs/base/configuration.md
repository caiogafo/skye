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
