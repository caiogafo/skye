"""A small agent on low-level capabilities: ask, run the calls the model requests, feed the results back, repeat.

``skye.agents`` has no loop yet, so the loop is written by hand. With ``OPENAI_API_KEY`` it talks to OpenAI; without it the shared scripted client runs offline.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from skye import CapabilityMessage, SystemMessage, UserMessage
from skye.completion import CapabilityCall
from skye.tools import capability

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402


@capability
def get_weather(location: str, unit: str = "fahrenheit") -> dict:
    """Get the current weather for a location (unit: fahrenheit or celsius)."""
    temp = {"San Francisco": 72, "New York": 65, "London": 55}.get(location, 70)
    temp = round((temp - 32) * 5 / 9, 1) if unit.lower() == "celsius" else temp
    return {"location": location, "temp": temp, "unit": unit}


@capability
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


class CapabilityAgent:
    """Loop: complete, run every requested capability, append the results, stop when the model answers in text."""

    def __init__(self, client: Any, model: str, capabilities: list[Any], system: str = "", max_steps: int = 5) -> None:
        self.client, self.model, self.system, self.max_steps = client, model, system, max_steps
        self.capabilities = {c.get_schema().name: c for c in capabilities}

    async def run(self, question: str) -> str:
        messages: list[Any] = [SystemMessage(content=self.system), UserMessage(content=question)]
        for step in range(1, self.max_steps + 1):
            response = self.client.complete(messages=messages, model=self.model, capabilities=list(self.capabilities.values()))
            if not response.has_capability_calls():
                return response.content
            messages.append(response.to_message())
            for call in response.capability_calls:
                print(f"  step {step}: {call.name}({call.arguments})")
                messages.append(await self._execute(call))
        return "Stopped: the step limit was reached before the model gave an answer."

    async def _execute(self, call: CapabilityCall) -> CapabilityMessage:
        """Run one call. A failure becomes the content of the message, so the model can read it and recover."""
        try:
            result = await self.capabilities[call.name].aexecute(**call.arguments)
            content = result if isinstance(result, str) else json.dumps(result, default=str)
        except Exception as error:
            content = f"Error: {error!r}"
        return CapabilityMessage(content=content, capability_id=call.id, capability_name=call.name)


async def main() -> None:
    agent = CapabilityAgent(get_client("openai"), "gpt-4o-mini", [get_weather, add], system="Use the capabilities when they help.")
    print(await agent.run("What is the weather in London in celsius, and what is 25 + 4?"))


if __name__ == "__main__":
    asyncio.run(main())
