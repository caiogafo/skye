Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, Optional services, Extension points, Extras and budgets)

# Design Document: observe

## Overview
`observe` is the services layer-2 component (codename radar). It provides events, logs, metrics and traces behind the observer and
event-handler Ports of `base`, and a registry of exporters through which a new destination is added without editing the component
(Requirement 53.1, 53.2, 6.1). It imports only `base` (`11-design.md`, "Allowed imports"). Runtime components never import it: they
receive an `ObserverInterface` or an `EventHandlerInterface` by injection or through the observability hook of the agent
(Requirement 53.4, 4.1; D9). The core of `observe` uses the standard library only; an exporter that has no standard-library path
declares its library in the extra `observe` and nothing else (Requirement 53.3). The layer, the allowed imports, the Ports, the
extension-point table and the extras policy are in the steering sections named above and are not restated here.

## Current state
`skye.observe` is a placeholder: `__all__` is empty and any attribute raises `ImportError("skye.observe is planned, not available yet")`
(D40). The extra `observe` is empty and listed in `known_empty`, with the note "declare it with the code that does". The Ports exist in
`base`: `ObserverInterface` (`log_event(EventType, data)`, `record_metric(name, value, tags)`, `start_trace(name, metadata) -> id`,
`end_trace(id, metadata)`), the `EventType` enumeration (model invoke start, end and error; capability invoke start, end and error;
agent step; agent complete), and `EventHandlerInterface` with eight `on_*` methods. Their footers say an observer never raises to the
caller, is thread-safe and must not block. Several components already want to write structured lines (`policy`, `gateway`, the
router) and count things through `record_metric`.

## Architecture
```
observe/
  observers.py      built-in observers: LoggingObserver (JSON lines through the standard logging module), MemoryObserver (keeps events for tests), CompositeObserver (fan-out)
  handlers.py       ObserverEventHandler: an EventHandlerInterface that turns each on_* call into a log_event on an observer
  metrics.py        a small in-process counter and gauge set, and the metric line format
  tracing.py        trace and span identifiers, W3C trace-context headers, the active trace of a run
  exporters.py      the Exporter protocol and the registry: register_exporter(name, factory), resolve_exporter(name)
  exporters/        one module per exporter: stdout JSON (core), CloudWatch embedded metric format (core, no library)
```
The registry follows the shape of the `auth` registry (`register_credential_source` / `resolve_credential_source`): a name maps to a
factory, registering a name twice is an error unless `replace=True`, and an unknown name raises a `ConfigurationError` listing the
known ones. A new exporter is one new module plus one registration, touching no file outside `observe` (Requirement 6.2).

### Events and logs (Requirement 53.1)
`LoggingObserver.log_event` writes one JSON object per event with the event type, a timestamp, the trace id when there is one and the
data, through the `logging` module with `extra={...}`. It writes no field the caller did not put in `data`, and a configured list of
keys is redacted (replaced, not dropped) so a secret or a prompt does not reach the log by accident. `ObserverEventHandler` adapts the
eight lifecycle methods to events: for example `on_capability_invoke_error` becomes `EventType.CAPABILITY_INVOKE_ERROR` with the
capability name and the error type, and no arguments or results unless a setting enables them (the same rule `policy` and `gateway`
follow).

### Metrics (Requirement 53.1)
`record_metric(name, value, tags)` adds to an in-process counter or sets a gauge keyed by name and tags, and hands the sample to the
exporters. A metric name follows `skye.<component>.<name>`. The counters of other components (`policy` allow, deny and error;
`gateway` requests) use this Port and need nothing from `observe` at import time.

### Traces (Requirement 53.1)
`start_trace` returns an identifier and `end_trace` closes it; the active trace is kept in a `contextvars` variable so concurrent tasks
do not mix. Identifiers follow W3C trace context (32 hex characters for a trace, 16 for a span) so a trace started by the caller
continues. `observe` creates no spans on its own: the agent and the router call the Port at their operations.

### Exporters and flushing (Requirement 53.2, 53.3)
An exporter receives events, metric samples and finished traces. The core ships two with no library: standard output as JSON lines,
and the CloudWatch embedded metric format, which is a JSON line a Lambda writes to standard output and CloudWatch turns into metrics
without a client library. An exporter that needs a library (an OpenTelemetry exporter, for instance) lives in its own module, imports
the library lazily and raises `MissingExtraError` naming the extra `observe`; the extra declares only that library (Requirement 53.3,
7.3).

Serverless rule: no background thread and no process (`00-rules`). An exporter that sends over the network therefore buffers in
memory and sends when the buffer is full or when `flush()` is called, and the caller (the Lambda handler, or the agent at the end of a
run) must call `flush()` before the invocation returns, since the environment is frozen afterwards. The Port has no `flush`; this is
listed under "Open points". The built-in exporters write synchronously and need no flush.

### Failure rule
An observer never raises into its caller and never blocks the run (Port footer): an exporter exception is caught, logged once at
WARNING level through the standard `logging` module without recursion into the observer, and counted.

## Data Models
Dataclasses (D24): `ObservedEvent` (type, timestamp, trace id, data), `MetricSample` (name, value, tags, timestamp), `TraceRecord`
(trace id, name, start, end, metadata). `EventType` is the one in `base`.

## Error Handling
A configuration error (an unknown exporter, a bad redaction list) raises `ConfigurationError` at construction. Runtime exporter
errors are swallowed as above. A missing optional library raises `MissingExtraError` naming `observe` when that exporter is built.

## Testing Strategy
Tests in `tests/unit/observe/`: each built-in observer and both exporters (a captured stream), the event handler adapter for each of
the eight methods, redaction, an exporter that raises (the run continues, one warning, a counter), the registry (register, replace,
unknown name), the trace context across concurrent tasks (`asyncio.gather`), the W3C header round trip, and the embedded metric line
format against the CloudWatch documentation example. The compliance checker runs every built-in observer through the Port. The budget
tests check that `import skye.observe` imports no third-party library.

## Correctness Properties
1. An observer method never raises, whatever the exporter does.
2. Two concurrent tasks each see their own active trace.
3. A redacted key never appears in the written line.
4. Registering an exporter touches no file outside `observe`, and a second registration of a name is an error unless replacing.
5. A trace context parsed from a W3C header and written again is the same.
6. Importing `observe` imports no third-party library, and an absent optional library raises `MissingExtraError` naming `observe`.

## Open points (not decided here)
- The observer Port has no `flush`; with no background thread a buffering exporter needs one. Adding it is a Port change (Requirement 16.9: a Port with many methods is split by role, so it may be a small separate Port).
- Which optional exporters ship (OpenTelemetry, Datadog) and under which extras, or whether only the two core exporters ship at first.
- The metric name scheme `skye.<component>.<name>` is an assumption; the components that already count (policy, gateway) cite it.
- Whether the log line shape of `policy` and `gateway` (Requirements 37.7 and 48.5) is produced by `observe` or by each component directly.
