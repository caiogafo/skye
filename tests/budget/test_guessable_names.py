"""Names a newcomer tries exist as thin aliases, or are recorded as known missing (Requirement 22.7 of steering, decision D39).

Each name is `exists` or `known_missing`. The list of missing names only shrinks: a name that starts to exist fails the test until it is
moved to `exists`. An alias stores no second value: it returns what the name it delegates to returns.
"""

from __future__ import annotations

import inspect

import pytest

import skye
from skye.agents import ReActAgent
from skye.completion import CompleteRequest, CompleteResponse, TokenUsage
from skye.data import Validated
from skye.messages import UserMessage
from skye.models.base import BaseModelProvider
from skye.tools import CapabilityRegistry


def _response(content: str = "hello") -> CompleteResponse:
    usage = TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2)
    return CompleteResponse(model="m", provider="p", content=content, finish_reason="stop", usage=usage)


EXISTS = {
    "CompleteResponse.text": lambda: hasattr(CompleteResponse, "text"),
    "CapabilityRegistry.list": lambda: callable(getattr(CapabilityRegistry, "list", None)),
    "ReActAgent.ainvoke": lambda: inspect.iscoroutinefunction(getattr(ReActAgent, "ainvoke", None)),
    "BaseModelProvider.ainvoke": lambda: inspect.iscoroutinefunction(getattr(BaseModelProvider, "ainvoke", None)),
}

# Not added on purpose (D39): the documentation names the word that exists. The list only shrinks.
KNOWN_MISSING = {
    "CompleteRequest.tool_choice": lambda: "tool_choice" in CompleteRequest.__dataclass_fields__,
    "CompleteRequest.tools": lambda: "tools" in CompleteRequest.__dataclass_fields__,
    "skye.provider(kind=...)": lambda: "kind" in inspect.signature(skye.provider).parameters,
    "skye.Router": lambda: hasattr(skye, "Router"),
    "skye.tool": lambda: hasattr(skye, "tool"),
    "Validated.model_dump": lambda: hasattr(Validated, "model_dump"),
    "Validated.model_validate": lambda: hasattr(Validated, "model_validate"),
    "Validated.model_json_schema": lambda: hasattr(Validated, "model_json_schema"),
}


@pytest.mark.parametrize("name", EXISTS)
def test_the_name_exists(name: str):
    assert EXISTS[name](), f"{name} is recorded as existing but is missing"


@pytest.mark.parametrize("name", KNOWN_MISSING)
def test_the_known_missing_name_is_still_missing(name: str):
    assert not KNOWN_MISSING[name](), f"{name} now exists: move it to EXISTS (the missing list only shrinks)"


def test_text_returns_content_and_stores_nothing_of_its_own():
    response = _response("Paris")
    assert response.text == response.content == "Paris"
    assert "text" not in CompleteResponse.__dataclass_fields__
    with pytest.raises(AttributeError):
        response.text = "other"  # type: ignore[misc]


def test_registry_list_returns_what_list_all_returns():
    registry = CapabilityRegistry()
    assert registry.list() == registry.list_all()


def test_the_documentation_names_the_word_that_exists():
    assert UserMessage(content="x").content == "x"
