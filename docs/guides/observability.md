---
title: "Observability"
status: current
---

# Observability

This guide shows you what you can watch in a Skye application today (logs, token usage, health) and how to implement the two
observability Ports for your own telemetry.

!!! note
    The `observe` component, which will send events, metrics and traces to an observability stack, is planned and has no code yet. The
    Ports it will use exist today, but no Skye component calls them yet. See [Status and roadmap](../project/roadmap.md).

## What you need

- `pip install skyeai`. Everything on this page is standard library.

## Logs

Skye logs with the standard `logging` module, on loggers named after its modules (`skye.models...`, `skye.router...`,
`skye.tools...`). It installs no handler: configure one; `skye.load_config` sets the levels from the configuration. See
[Configuration](configuration.md#logging).

Most Skye records carry their values as fields of the record (`extra=`), so a JSON formatter or CloudWatch Logs Insights can query them. Log your own events
the same way:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("model invocation completed", extra={"model": "gpt-4o-mini", "total_tokens": 150, "latency_ms": 234})
```

### One record per phase of a model call

Every `complete` and `stream` of a model client logs the phases of the call on the `skye.models` logger, each with the same
`skye_correlation_id`, so one call can be followed from its start to its end:

| Phase (`skye_phase`) | Level | Fields |
|---|---|---|
| `start` | DEBUG | `skye_model`, `skye_provider`, `skye_request` (number of messages, temperature, max tokens, stream) |
| `end` | INFO | `skye_response` (finish reason, prompt, completion and total tokens, `cost`, `latency_ms`) |
| `error` | WARNING | `skye_error` (the error class and message), once, after the retries |

The records hold no message text. A stream the caller stops reading still logs its `end`, with the finish reason
`interrupted` and the tokens counted so far. Logging never breaks a call: if a record cannot be built, the call goes on. To see
them, set the level of `models` in `component_log_levels` to `DEBUG` or `INFO`.

## Token usage and health

Every response carries its token usage, and every provider client keeps its own health counters:

```python
response = client.complete(messages=question, model="gpt-4o-mini")
print(response.usage.prompt_tokens, response.usage.completion_tokens, response.usage.total_tokens)

metrics = client.get_health_metrics()  # success_count, failure_count, success_rate, average_latency_ms, ...
print(f"{metrics['success_rate']:.0%} ok, {metrics['average_latency_ms']:.0f} ms on average")
```

A router keeps the same counters per model, plus the cooldown state: `router.get_model_health(model_id)` returns a
`ModelHealthMetrics` (success rate, latency, `is_in_cooldown`, `failure_reasons`, ...). See
[Health and cooldown](routing/health-and-cooldown.md). To turn tokens into money, see [Tokens and cost](models/tokens-and-cost.md).

## The observer Port

`ObserverInterface` in [`skye.interfaces`](../reference/api/interfaces.md) is the contract of a telemetry exporter: structured events,
metrics and traces. `EventType` names the events (`MODEL_INVOKE_START`, `MODEL_INVOKE_END`, `MODEL_INVOKE_ERROR`, the same three for
capabilities, `AGENT_STEP`, `AGENT_COMPLETE`).

```python
--8<-- "examples/observe/telemetry.py:12:44"
```

An observer must be thread-safe, must not block, and must never raise to its caller: a failure is logged and swallowed.

Until the runtime calls it for you, call the observer around your own code:

```python
observer = InMemoryObserver()
trace_id = observer.start_trace("completion", metadata={"model": "gpt-4o-mini"})
observer.log_event(EventType.MODEL_INVOKE_START, {"model": "gpt-4o-mini"})

response = client.complete(messages=question, model="gpt-4o-mini")

observer.record_metric("total_tokens", response.usage.total_tokens, tags={"model": response.model})
observer.log_event(EventType.MODEL_INVOKE_END, {"model": response.model, "finish_reason": response.finish_reason})
observer.end_trace(trace_id, metadata={"status": "ok"})
```

## The event handler Port

`EventHandlerInterface` has one hook per moment of a run: the start, end and error of a model call and of a capability call, each step
of an execution, and its completion. It is the shape the agent loop will call; implement all eight hooks.

```python
--8<-- "examples/observe/custom_exporter.py:11:42"
```

## What is planned

- The `observe` component: exporters behind these Ports for common observability stacks.
- The runtime (`agents`, `teams`, `flows`, `gateway`) taking an observer or an event handler by injection, so it calls your hooks
  without importing `observe`.

Both are tracked in [Status and roadmap](../project/roadmap.md).

## See also

- [Configuration](configuration.md): log levels per component.
- [Which Port to implement](extend/index.md): every Port and where it plugs in.
- Reference: [`skye.interfaces`](../reference/api/interfaces.md).
- Examples: [`telemetry.py`](https://github.com/ggiallo28/skye/blob/main/examples/observe/telemetry.py),
  [`custom_exporter.py`](https://github.com/ggiallo28/skye/blob/main/examples/observe/custom_exporter.py).
