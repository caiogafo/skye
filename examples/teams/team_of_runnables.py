"""Compose a team from the Runnable Port (proposed-interface, guarded).

The ``teams`` component has no public orchestration API yet. What is real today is the ``Runnable`` Port (``async invoke(input) -> output``):
this example builds a team from user ``Runnable``s and a tiny local coordinator that runs the members toward one objective. The planned
``teams`` API will own role assignment and coordination.
"""

import asyncio
from dataclasses import dataclass

from skye.interfaces import Runnable


class Step:
    """A member that prefixes its input: stands in for a model, a tool or an agent."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    async def invoke(self, input: str) -> str:
        return f"{self.prefix}: {input}"


@dataclass
class Member:
    """A team member: a free-string role and the Runnable that does the work."""

    role: str
    runnable: Runnable[str, str]


async def run_team(members: list[Member], objective: str) -> str:
    """Local stand-in for the planned coordinator: run each member in order, passing the result forward."""
    result = objective
    for member in members:
        print(f"[{member.role}] working on: {result}")
        result = await member.runnable.invoke(result)
    return result


async def main() -> None:
    members = [Member("researcher", Step("notes")), Member("writer", Step("draft")), Member("reviewer", Step("approved"))]
    assert all(isinstance(member.runnable, Runnable) for member in members)
    print("Team result:", await run_team(members, "serverless GenAI patterns"))


if __name__ == "__main__":
    asyncio.run(main())
