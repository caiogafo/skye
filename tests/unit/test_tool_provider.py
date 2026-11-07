"""The ``ToolProvider`` Port: the registry offers schemas and runs one call with a separate context (D44, task 3.12)."""

from __future__ import annotations

import asyncio

from skye.completion import CapabilityCall
from skye.interfaces import CapabilityContext, ToolProvider
from skye.messages import CapabilityStatus
from skye.tools import CapabilityRegistry, capability


@capability
def echo(text: str) -> str:
    """Echo the text."""
    return text


def test_the_registry_lists_schemas_and_runs_a_call():
    registry = CapabilityRegistry()
    registry.add(echo)

    async def go():
        schemas = await registry.list_schemas("any operation")
        message = await registry.run(CapabilityCall(id="1", name="echo", arguments={"text": "hi"}), CapabilityContext(scope_token="t"))
        await registry.close()
        return schemas, message

    schemas, message = asyncio.run(go())
    assert [s.name for s in schemas] == ["echo"]
    assert message.content == "hi" and message.status is CapabilityStatus.OK
    assert isinstance(registry, ToolProvider)


def test_the_context_is_not_an_argument_of_the_model():
    registry = CapabilityRegistry([echo])
    context = CapabilityContext(scope_token="secret", operation="summarise", metadata={"text": "from context"})
    call = CapabilityCall(id="1", name="echo", arguments={"text": "from model"})
    assert asyncio.run(registry.run(call, context)).content == "from model"


def test_an_unknown_name_is_an_error_message_not_an_exception():
    message = asyncio.run(CapabilityRegistry().run(CapabilityCall(id="1", name="nope")))
    assert message.status is CapabilityStatus.ERROR


def test_a_class_with_the_three_methods_is_a_tool_provider_with_no_inheritance():
    class Mine:
        async def list_schemas(self, operation=None):
            return []

        async def run(self, call, context=None):
            return None

        async def close(self):
            return None

    assert isinstance(Mine(), ToolProvider)
