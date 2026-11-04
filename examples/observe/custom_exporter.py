"""Custom exporter: implement the observe event-handler Port as an exporter (Live, Port-level).

``EventHandlerInterface`` (``skye.base.interfaces.event_handler``)
is a real Port with eight lifecycle hooks. A user implements all of them; this
example appends each hook call to an export buffer and fires the model-invoke and
capability-invoke pairs, no client needed.
"""

from typing import Any

from skye.interfaces import EventHandlerInterface


class BufferingExporter(EventHandlerInterface):
    """An event handler that exports every lifecycle hook into a buffer."""

    def __init__(self) -> None:
        self.buffer: list[str] = []

    def on_model_invoke_start(self, model_id: str, request: Any) -> None:
        self.buffer.append(f"model_invoke_start model_id={model_id}")

    def on_model_invoke_end(self, model_id: str, response: Any) -> None:
        self.buffer.append(f"model_invoke_end model_id={model_id}")

    def on_model_invoke_error(self, model_id: str, error: Exception) -> None:
        self.buffer.append(f"model_invoke_error model_id={model_id} error={error}")

    def on_capability_invoke_start(self, capability_name: str, args: dict[str, Any]) -> None:
        self.buffer.append(f"capability_invoke_start name={capability_name} args={args}")

    def on_capability_invoke_end(self, capability_name: str, result: Any) -> None:
        self.buffer.append(f"capability_invoke_end name={capability_name} result={result}")

    def on_capability_invoke_error(self, capability_name: str, error: Exception) -> None:
        self.buffer.append(f"capability_invoke_error name={capability_name} error={error}")

    def on_execution_step(self, step_number: int, data: dict[str, Any]) -> None:
        self.buffer.append(f"execution_step step={step_number} data={data}")

    def on_execution_complete(self, result: Any) -> None:
        self.buffer.append(f"execution_complete result={result}")


def main() -> None:
    exporter = BufferingExporter()

    exporter.on_model_invoke_start("gpt-4", request={"prompt": "hi"})
    exporter.on_model_invoke_end("gpt-4", response={"content": "hello"})
    exporter.on_capability_invoke_start("get_weather", {"location": "Rome"})
    exporter.on_capability_invoke_end("get_weather", {"temp": 24})

    print(f"Exported {len(exporter.buffer)} record(s):")
    for record in exporter.buffer:
        print(f"  {record}")


if __name__ == "__main__":
    main()
