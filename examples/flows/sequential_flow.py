"""Chain Runnables in sequence with cycle detection (proposed-interface, guarded).

The ``flows`` component has no public API yet. What is real today is the ``Runnable`` Port (``async invoke(input) -> output``): this example
chains user ``Runnable``s in order with a tiny local runner and a cycle check. A configured cycle prints a line with the word ``Expected``,
a deliberately shown error that the examples harness treats as success. The planned ``flows`` API will own the graph and its validation.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field

from skye.interfaces import Runnable


class Apply:
    """A step that applies a function to its input."""

    def __init__(self, fn: Callable[[str], str]) -> None:
        self.fn = fn

    async def invoke(self, input: str) -> str:
        return self.fn(input)


@dataclass
class Step:
    """A named step: its Runnable and the name of the next step (None for the last)."""

    name: str
    runnable: Runnable[str, str]
    next: str | None = None


@dataclass
class Flow:
    steps: dict[str, Step] = field(default_factory=dict)

    def has_cycle(self, start: str) -> bool:
        seen: set[str] = set()
        current: str | None = start
        while current is not None:
            if current in seen:
                return True
            seen.add(current)
            current = self.steps[current].next
        return False

    async def run(self, start: str, value: str) -> str:
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
    flow = Flow({
        "trim": Step("trim", Apply(str.strip), next="upper"),
        "upper": Step("upper", Apply(str.upper), next="exclaim"),
        "exclaim": Step("exclaim", Apply(lambda text: f"{text}!")),
    })
    print("Flow result:", await flow.run("trim", "  hello flow  "))

    looping = Flow({"a": Step("a", Apply(str.strip), next="b"), "b": Step("b", Apply(str.upper), next="a")})
    try:
        await looping.run("a", "x")
    except ValueError as error:
        print(f"Expected cycle refused by the flow runner: {error}")


if __name__ == "__main__":
    asyncio.run(main())
