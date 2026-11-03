"""Chain Runnables in sequence with cycle detection (proposed-interface, guarded).

Classification: proposed-interface, guarded. The ``flows`` component is declared
but minimal: there is no public flows API yet. What is real and composable today
is the ``Runnable`` Port (``async invoke(input) -> output``), so this example
chains user ``Runnable``s in order (each step's output feeds the next step's
input) with a tiny local sequential runner.

The planned ``flows`` API will own the graph and its validation; here we also show
a local cycle check. When a cycle is configured the runner refuses to run and
prints a line containing the word ``Expected`` -- a deliberately-shown error that
the examples harness treats as success, not a failure.
"""

import asyncio
from dataclasses import dataclass, field

from skye.base.interfaces.runnable import Runnable


class Trim:
    """Step one: strip surrounding whitespace."""

    async def invoke(self, input: str) -> str:
        return input.strip()


class Upper:
    """Step two: upper-case the text."""

    async def invoke(self, input: str) -> str:
        return input.upper()


class Exclaim:
    """Step three: add emphasis."""

    async def invoke(self, input: str) -> str:
        return f"{input}!"


@dataclass
class Step:
    """A named flow step holding its Runnable and the name of the next step.

    Attributes:
        name: Unique step name.
        runnable: The unit that does the work, held via the Runnable Port.
        next: Name of the following step, or None for the last step.
    """

    name: str
    runnable: Runnable[str, str]
    next: str | None = None


@dataclass
class Flow:
    """A sequential flow of steps, keyed by name.

    The planned ``flows`` API will own graph construction and validation; this
    local shape mirrors its intended form so the example stays honest.
    """

    steps: dict[str, Step] = field(default_factory=dict)

    def has_cycle(self, start: str) -> bool:
        """Return True if following ``next`` from ``start`` revisits a step."""
        seen: set[str] = set()
        current: str | None = start
        while current is not None:
            if current in seen:
                return True
            seen.add(current)
            current = self.steps[current].next
        return False

    async def run(self, start: str, value: str) -> str:
        """Run steps from ``start`` in order, feeding each output to the next."""
        if self.has_cycle(start):
            raise ValueError("flow has a cycle")
        current: str | None = start
        while current is not None:
            step = self.steps[current]
            value = await step.runnable.invoke(value)
            print(f"after {step.name}: {value!r}")
            current = step.next
        return value


async def main() -> None:
    flow = Flow(
        steps={
            "trim": Step("trim", Trim(), next="upper"),
            "upper": Step("upper", Upper(), next="exclaim"),
            "exclaim": Step("exclaim", Exclaim(), next=None),
        }
    )
    result = await flow.run("trim", "  hello flow  ")
    print("Flow result:", result)

    # Cycle detection: configure a loop and show the runner refuses it. The line
    # contains "Expected" so the harness does not treat it as a failure.
    looping = Flow(
        steps={
            "a": Step("a", Trim(), next="b"),
            "b": Step("b", Upper(), next="a"),
        }
    )
    try:
        await looping.run("a", "x")
    except ValueError as e:
        print(f"Expected cycle refused by the flow runner: {e}")

    print("Composition is via the Runnable Port; the flows orchestration API")
    print("ships with the future flows spec, so no flows call is made here.")
    return


if __name__ == "__main__":
    asyncio.run(main())
