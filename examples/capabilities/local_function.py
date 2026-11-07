"""Local Python functions as capabilities.

``@capability`` turns a function into a capability: the schema (name, description, parameters) comes from the signature and the docstring,
and the function runs locally when the model asks for it. Sync and async functions are both supported. For a loop that feeds the results
back to the model, see ``capability_agent.py``.

With OPENAI_API_KEY set the model is real; without a key a scripted client asks for the capabilities and the example says so.
"""

import asyncio
import sys
from pathlib import Path

from skye import UserMessage
from skye.tools import capability

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402


@capability
def get_weather(location: str, unit: str = "fahrenheit") -> dict:
    """Get the current weather for a location (unit: fahrenheit or celsius)."""
    temp = {"San Francisco": 72, "New York": 65, "London": 55}.get(location, 70)
    return {"location": location, "temp": round((temp - 32) * 5 / 9, 1) if unit == "celsius" else temp, "unit": unit}


@capability
async def fetch_user(user_id: str) -> dict:
    """Fetch a user record (an async capability)."""
    await asyncio.sleep(0.01)
    return {"user_123": {"name": "Alice", "role": "admin"}}.get(user_id, {"error": f"user {user_id} not found"})


def show_schemas() -> None:
    for cap in (get_weather, fetch_user):
        schema = cap.get_schema()
        required = schema.parameters.get("required", [])
        params = ", ".join(f"{n}{'*' if n in required else ''}: {p.get('type')}" for n, p in schema.parameters["properties"].items())
        print(f"{schema.name}({params}) - {schema.description}")


async def main() -> None:
    show_schemas()

    # Run a capability yourself: sync ones with execute, async ones with aexecute
    print("execute:", get_weather.execute(location="London", unit="celsius"))
    print("aexecute:", await fetch_user.aexecute(user_id="user_123"))

    # Let the model ask for them, then run the calls it requested
    client = get_client("openai")
    question = [UserMessage(content="What's the weather in San Francisco?")]
    response = client.complete(messages=question, model="gpt-4", capabilities=[get_weather])
    for call in response.capability_calls or []:
        print(f"the model asks for: {call.name}({call.arguments})")
    if response.has_capability_calls():
        for message in await response.aexecute_capability_calls():
            print(f"result of {message.capability_name}: {message.content}")


if __name__ == "__main__":
    asyncio.run(main())
