"""``acomplete`` takes the same arguments as ``complete`` on every REST adapter (``messages=..., model=...`` or a request).

The documentation and the examples call ``await client.acomplete(messages=[...], model="gpt-4")``; the adapters for OpenAI and
Anthropic once overrode ``acomplete(request)`` only, so the documented call raised ``TypeError``.
"""

from __future__ import annotations

import asyncio

import pytest

import skye
from skye.base.messages import UserMessage
from tests.examples.fake_network import patched


@pytest.mark.parametrize("name,model", [("openai", "gpt-4"), ("anthropic", "claude-3-sonnet-20240229")])
def test_acomplete_accepts_messages_and_model(name, model):
    client = skye.provider(name, api_key="k")
    with patched():
        response = asyncio.run(client.acomplete(messages=[UserMessage(content="hi")], model=model))
    assert response.content


@pytest.mark.parametrize("name,model", [("openai", "gpt-4"), ("anthropic", "claude-3-sonnet-20240229")])
def test_complete_and_stream_work_without_temperature_or_max_tokens(name, model):
    """The boto3-style call `client.complete(messages=..., model=...)` needs no sampling arguments."""
    client = skye.provider(name, api_key="k")
    messages = [UserMessage(content="hi")]
    with patched():
        assert client.complete(messages=messages, model=model).content
        assert "".join(chunk.delta or "" for chunk in client.stream(messages=messages, model=model))
