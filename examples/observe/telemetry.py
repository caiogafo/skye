"""Telemetry: implement the observe Port and collect events, metrics and traces (Live, Port-level).

The ``observe`` component exports nothing concrete yet, but the
``ObserverInterface`` Port and its ``EventType`` enum are real
(``skye.base.interfaces.observer``). A user implements the Port; this example
collects everything into in-memory lists and drives a model-invoke pair, no client
needed.
"""

from typing import Any

from skye.interfaces import EventType, ObserverInterface


class InMemoryObserver(ObserverInterface):
    """An observer that records events, metrics and traces into lists."""

    def __init__(self) -> None:
        self.events: list[tuple[EventType, dict[str, Any]]] = []
        self.metrics: list[tuple[str, float, dict[str, str] | None]] = []
        self.traces: dict[str, dict[str, Any]] = {}
        self._trace_counter = 0

    def log_event(self, event_type: EventType, data: dict[str, Any]) -> None:
        """Record a structured event."""
        self.events.append((event_type, data))

    def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a metric value with optional tags."""
        self.metrics.append((name, value, tags))

    def start_trace(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        """Start a trace span and return its correlation id."""
        self._trace_counter += 1
        trace_id = f"trace-{self._trace_counter}"
        self.traces[trace_id] = {"name": name, "metadata": metadata, "ended": False}
        return trace_id

    def end_trace(self, trace_id: str, metadata: dict[str, Any] | None = None) -> None:
        """Mark a trace span as ended."""
        span = self.traces.get(trace_id)
        if span is not None:
            span["ended"] = True
            span["end_metadata"] = metadata


def main() -> None:
    observer = InMemoryObserver()

    trace_id = observer.start_trace("completion", metadata={"model": "gpt-4"})
    observer.log_event(EventType.MODEL_INVOKE_START, {"model": "gpt-4"})
    observer.record_metric("prompt_tokens", 12.0, tags={"model": "gpt-4"})
    observer.log_event(EventType.MODEL_INVOKE_END, {"model": "gpt-4", "latency_ms": 42})
    observer.end_trace(trace_id, metadata={"status": "ok"})

    print("Events:")
    for event_type, data in observer.events:
        print(f"  {event_type.value}: {data}")

    print("Metrics:")
    for name, value, tags in observer.metrics:
        print(f"  {name}={value} tags={tags}")

    print("Traces:")
    for tid, span in observer.traces.items():
        print(f"  {tid}: name={span['name']} ended={span['ended']}")


if __name__ == "__main__":
    main()
