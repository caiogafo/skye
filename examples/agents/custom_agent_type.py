"""Register and run your own agent type (Live).

Classification: Live. This runs real library code end to end.

An agent type is a factory (usually a class) that produces a ``Runnable`` -- any
object with ``async def invoke(self, input) -> output``. You register the factory
by name through ``register_agent_type``, create instances with ``create_agent`` and
list what is available with ``list_agent_types``.

The registry is a process-wide singleton that the examples harness does not reset
between scripts, so this example registers under a script-local name with
``replace=True`` to stay idempotent.
"""

import asyncio

from skye.agents import create_agent, list_agent_types, register_agent_type
from skye.base.interfaces.runnable import Runnable


class EchoAgent:
    """A tiny agent type: it echoes the input, optionally with a prefix.

    Satisfies the ``Runnable`` Port structurally, so it needs no base class.
    """

    def __init__(self, *, prefix: str = "echo") -> None:
        self.prefix = prefix

    async def invoke(self, input: str) -> str:
        """Return the input prefixed with the configured label."""
        return f"[{self.prefix}] {input}"


async def main() -> None:
    # Register our factory under a script-local name. replace=True keeps the script
    # idempotent because the harness shares the agents registry across scripts.
    register_agent_type("echo-demo", EchoAgent, replace=True)

    # Create an instance; factory options flow straight to EchoAgent(**options).
    agent = create_agent("echo-demo", prefix="demo")
    assert isinstance(agent, Runnable)  # the Port is a structural Protocol

    reply = await agent.invoke("hi")
    print(reply)

    print("Registered agent types:", list_agent_types())


if __name__ == "__main__":
    asyncio.run(main())
