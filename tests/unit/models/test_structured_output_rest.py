"""Structured output with the REST adapters: the JSON text is validated against the declared schema and attached to the response."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

import skye
from skye.base.exceptions import ValidationError
from skye.base.messages import UserMessage
from tests.examples.fake_network import patched


class Person(BaseModel):
    name: str
    age: int


def test_a_conforming_answer_is_parsed_into_the_schema():
    client = skye.provider("openai", api_key="k")
    with patched():
        response = client.complete(messages=[UserMessage(content="x")], model="gpt-4", response_schema=Person)
    assert isinstance(response.structured_output, Person)
    assert response.structured_output.age == 1


def test_a_non_conforming_answer_raises_validation_error_naming_the_field(monkeypatch):
    client = skye.provider("openai", api_key="k")
    monkeypatch.setattr(
        "tests.examples.fake_network._fill", lambda schema: {"name": "Alice", "age": "not a number"}
    )
    with patched(), pytest.raises(ValidationError) as caught:
        client.complete(messages=[UserMessage(content="x")], model="gpt-4", response_schema=Person)
    assert "age" in str(caught.value)
