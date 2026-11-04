"""The SkyeError hierarchy (Live).

This example runs real library code end to end, with no client and no network.

Every Skye-specific exception inherits from ``SkyeError``, so a single ``except
SkyeError`` catches them all while keeping the specific type and its context. This
script raises each member of the hierarchy with its real constructor signature,
catches it through the ``SkyeError`` umbrella, and prints the message as an ordinary
informative line.

Note on output: the test harness treats a line containing a marker such as a bare
exception name followed by a colon as a failure, so this example prints the class
name and message as separate, plainly-worded fields rather than in that form.
"""

from skye import ConfigurationError, MissingExtraError, ProviderError, SkyeError, ValidationError
from skye.exceptions import CapabilityExecutionError


def _report(error: SkyeError) -> None:
    """Print an error caught through the SkyeError umbrella.

    Args:
        error: Any member of the SkyeError hierarchy.
    """
    print(f"  caught {type(error).__name__} -> {error.message}")
    if error.details:
        print(f"    details: {error.details}")


def main() -> None:
    print("Raising and catching each member of the SkyeError hierarchy:")

    cases: list[SkyeError] = [
        SkyeError("a generic Skye failure", details={"hint": "base of the hierarchy"}),
        ProviderError("the provider rejected the request", provider="openai", status_code=429),
        ConfigurationError("the model name is missing from the configuration"),
        ValidationError("temperature is out of range", field="temperature", value=3.5),
        CapabilityExecutionError("the capability raised", capability_name="get_weather"),
    ]

    for error in cases:
        try:
            raise error
        except SkyeError as caught:
            _report(caught)

    print("\nMissingExtraError names the extra that would provide an absent library:")
    missing = MissingExtraError("postgres", "asyncpg")
    print(f"  extra  : {missing.extra}")
    print(f"  missing: {missing.missing}")
    print(f"  install: pip install skyeai[{missing.extra}]")


if __name__ == "__main__":
    main()
