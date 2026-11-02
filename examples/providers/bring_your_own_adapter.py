"""Bring your own adapter: any object with ``async def invoke(self, input)`` is a ``Runnable``.

Skye has one built-in REST adapter per provider and no hidden selection of a vendor SDK. If you want to use an SDK, or any other model,
write a small class that satisfies the ``Runnable`` Port and use it wherever a model is accepted (for example as a step of a flow or a
member of a team). No configuration, no environment variable, no registration.
"""

import asyncio

from skye.base.interfaces.runnable import Runnable


class UppercaseModel:
    """A stand-in for your own model or SDK wrapper: one input in, one output out."""

    async def invoke(self, input: str) -> str:
        return input.upper()


async def main() -> None:
    model = UppercaseModel()
    assert isinstance(model, Runnable)  # the Port is a structural Protocol: no base class needed
    print(await model.invoke("hello from my own adapter"))


if __name__ == "__main__":
    asyncio.run(main())
