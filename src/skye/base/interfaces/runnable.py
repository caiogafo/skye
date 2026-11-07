"""Runnable Port: Skye's single composition contract, one input -> one output.

Conceptual codename: vapor (documentation only, never used in names).

Model adapters, agents, teams and flows all satisfy this Protocol, so any of them
can stand wherever a ``Runnable`` is accepted. Composing units hold their children
as ``Runnable`` references instead of importing each other. The Port is pure
contract: standard library only, no I/O.

Raises: any exception of the unit propagates unchanged; composition adds none.
Missing: not applicable: one input, one output.
Concurrency: ``invoke`` is async and re-entrant unless the unit documents state.

``ainvoke`` is a thin alias of ``invoke`` that the built-in units (model adapters, agents) also offer, for users who try the ``x`` / ``ax``
name first; the Port requires only ``invoke``, so a class with just ``invoke`` is still a ``Runnable``.
"""

from typing import Protocol, TypeVar, runtime_checkable

In = TypeVar("In", contravariant=True)
Out = TypeVar("Out", covariant=True)


@runtime_checkable
class Runnable(Protocol[In, Out]):
    """A unit that turns exactly one input into exactly one output."""

    async def invoke(self, input: In) -> Out:
        """Run the unit on one input and return one output."""
        ...


__all__ = ["Runnable"]
