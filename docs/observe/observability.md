# Observability

How Skye emits signals you can watch in production. `observe` provides the hooks; it imports
only `base` and is optional behind its own extra.

## Structured logging

Log an event plus fields, not an interpolated string. Structured records are queryable in
CloudWatch Logs Insights and keep one stable message per event.

```python
import logging

logger = logging.getLogger(__name__)

# Good: message is stable, values are fields
logger.info(
    "model invocation completed",
    extra={
        "model": "gpt-4",
        "tokens": 150,
        "latency_ms": 234,
        "correlation_id": "abc-123",
    },
)

# Avoid: values baked into the message
logger.info(f"gpt-4 used 150 tokens in 234ms")
```

Levels: DEBUG (diagnostics), INFO (normal events), WARNING (recoverable), ERROR (failed
operation), CRITICAL (the process cannot continue).

## Correlation IDs

Carry a correlation id through a request so every log line and emitted event for one
invocation can be joined. Set it once at the entry point (the Lambda handler) and attach it
to every record via `extra`.

## Token and cost tracking

Real token usage comes back in provider responses; record it per invocation (model, prompt
tokens, completion tokens, estimated cost) as an event so usage and spend can be aggregated
downstream. Pre-call token counts are only estimates used for rate-limit checks.

## Telemetry hooks

`observe` exposes hooks for custom telemetry. The runtime components (`gateway`, `agents`,
`teams`, `flows`) receive an observer through a `base` Port by injection — they never import
`observe`, so it is not required to run them.
