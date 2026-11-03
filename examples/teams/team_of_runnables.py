"""Compose a team from the Runnable Port (proposed-interface, guarded).

The ``teams`` component is declared
but minimal: there is no public teams orchestration API yet. What is real and
composable today is the ``Runnable`` Port (``async invoke(input) -> output``), so
this example builds a team purely from user ``Runnable``s and a tiny local
coordinator that assigns free-string roles and runs the members toward a shared
objective.

The planned ``teams`` API will own role assignment and coordination; here we show
the intended composition shape (members held as ``Runnable`` references, roles as
free strings) and guard-return before any not-yet-existing teams call.
"""

import asyncio
from dataclasses import dataclass

from skye.base.interfaces.runnable import Runnable


class Researcher:
    """A tiny member Runnable that gathers notes for the objective."""

    async def invoke(self, input: str) -> str:
        return f"notes about {input}"


class Writer:
    """A tiny member Runnable that drafts from whatever it receives."""

    async def invoke(self, input: str) -> str:
        return f"draft based on: {input}"


class Reviewer:
    """A tiny member Runnable that signs off on the input."""

    async def invoke(self, input: str) -> str:
        return f"reviewed and approved: {input}"


@dataclass
class Member:
    """A team member: a free-string role paired with a Runnable.

    Attributes:
        role: A free-form role label the planned teams API will understand.
        runnable: The unit that does the work, held via the Runnable Port.
    """

    role: str
    runnable: Runnable[str, str]


async def run_team(members: list[Member], objective: str) -> str:
    """Local stand-in for the planned teams coordinator.

    Runs each member in order, passing the running result forward. The real
    ``teams`` API will own this coordination; this mirrors its intended shape.
    """
    result = objective
    for member in members:
        print(f"[{member.role}] working on: {result}")
        result = await member.runnable.invoke(result)
    return result


async def main() -> None:
    members = [
        Member(role="researcher", runnable=Researcher()),
        Member(role="writer", runnable=Writer()),
        Member(role="reviewer", runnable=Reviewer()),
    ]
    for member in members:
        assert isinstance(member.runnable, Runnable)

    objective = "serverless GenAI patterns"
    final = await run_team(members, objective)
    print("Team result:", final)

    print("Composition is via the Runnable Port; the teams orchestration API")
    print("ships with the future teams spec, so no teams call is made here.")
    return


if __name__ == "__main__":
    asyncio.run(main())
