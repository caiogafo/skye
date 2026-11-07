"""Function calling: several capabilities, parallel execution and errors inside a capability.

``@capability`` turns a function into a capability: its schema comes from the signature and the docstring. The capabilities are passed
directly to the call; when the model asks for several of them, ``execute_capability_calls`` runs them and returns one result message
for each. A capability that raises does not stop the others: its message carries the error, which goes back to the model.

With OPENAI_API_KEY set the example calls OpenAI; without a key a scripted client asks for both capabilities.
"""

from skye import UserMessage
from skye.tools import capability

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402


@capability
def get_weather(location: str) -> str:
    """Get the weather for a location.

    Args:
        location: The city to look up
    """
    return {"Paris": "Sunny, 21 C", "London": "Rainy, 14 C"}.get(location, "Unknown location")


@capability
def get_population(location: str) -> str:
    """Get the population of a city.

    Args:
        location: The city to look up
    """
    if location == "Atlantis":
        raise ValueError("no such city")
    return {"Paris": "2.1 million", "London": "8.9 million"}.get(location, "Unknown")


def main() -> None:
    client = get_client("openai")
    question = [UserMessage(content="What is the weather in Paris, and how many people live there?")]
    capabilities = [get_weather, get_population]

    response = client.complete(messages=question, model="gpt-4", capabilities=capabilities)

    if response.has_capability_calls():
        for call in response.capability_calls:
            print("the model asks for:", call.name, call.arguments)

        # All requested calls are executed; a call that raises yields a message with the error instead of stopping the rest
        results = response.execute_capability_calls()
        for message in results:
            print(f"  {message.capability_name}: {message.content}")

        final = client.complete(
            messages=[*question, response.to_message(), *results], model="gpt-4", capabilities=capabilities
        )
        print(final.content)
    else:
        print(response.content)


if __name__ == "__main__":
    main()
