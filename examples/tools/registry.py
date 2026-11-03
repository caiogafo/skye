"""Capability registry: register, discover and execute capabilities (Live).

A ``CapabilityRegistry`` is the central place to register capabilities, look them up
by name, search them by a free-text query and execute them. This example builds a
fresh ``CapabilityRegistry()`` (not the process-wide singleton), registers two
``@capability`` functions, then lists, searches and executes them.

Runs fully offline: everything here is standard-library Skye code with no provider.
"""

from skye.tools import CapabilityRegistry, capability


@capability
def get_weather(location: str, unit: str = "celsius") -> dict:
    """Get the current weather for a location.

    Args:
        location: City name or location.
        unit: Temperature unit (``celsius`` or ``fahrenheit``).

    Returns:
        A dictionary with the temperature and a short condition.
    """
    temps = {"Paris": 18, "Tokyo": 24, "New York": 15}
    temp = temps.get(location, 20)
    if unit.lower() == "fahrenheit":
        temp = round(temp * 9 / 5 + 32)
    return {"location": location, "temperature": temp, "unit": unit}


@capability
def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return their sum.

    Args:
        a: First addend.
        b: Second addend.

    Returns:
        The sum of ``a`` and ``b``.
    """
    return a + b


def main() -> None:
    # A fresh registry: the harness does not reset the CapabilityRegistry singleton
    # between scripts, so instantiate one here rather than using get_instance().
    registry = CapabilityRegistry()
    registry.register(get_weather)
    registry.register(add_numbers)

    print("Registered capabilities:")
    for name in registry.list_all():
        print(f"  - {name}")

    print("\nSearch for 'weather':")
    for name, _cap, score in registry.search("weather"):
        print(f"  - {name} (score {score:.2f})")

    print("\nExecute get_weather(location='Paris'):")
    message = registry.execute("get_weather", {"location": "Paris"})
    print(f"  {message.capability_name} -> {message.content}")

    print("\nExecute add_numbers(a=2, b=3):")
    message = registry.execute("add_numbers", {"a": 2, "b": 3})
    print(f"  {message.capability_name} -> {message.content}")


if __name__ == "__main__":
    main()
