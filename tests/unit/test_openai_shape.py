"""SDK compatibility at the data level (Requirement 22): OpenAI-shaped dicts in, Skye types out."""

import copy

import pytest

from skye.base.exceptions import ValidationError
from skye.base.messages import AssistantMessage, CapabilityMessage, SystemMessage, UserMessage
from skye.base.openai_shape import capabilities_from_openai_tools, messages_from_openai

MSGS = [
    {"role": "system", "content": "be brief"},
    {"role": "user", "content": "weather?"},
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": "c1", "type": "function", "function": {"name": "get_weather", "arguments": '{"city": "NYC"}'}}
        ],
    },
    {"role": "tool", "tool_call_id": "c1", "content": "sunny"},
]
TOOL = {
    "type": "function",
    "function": {"name": "get_weather", "description": "Weather", "parameters": {"type": "object"}},
}


def test_messages_become_skye_types():
    out = messages_from_openai(MSGS)
    assert [type(m) for m in out] == [SystemMessage, UserMessage, AssistantMessage, CapabilityMessage]
    assert out[2].capability_calls == [{"id": "c1", "name": "get_weather", "args": {"city": "NYC"}}]
    assert (out[3].capability_id, out[3].capability_name) == ("c1", "get_weather")


def test_tools_become_capability_schemas():
    (cap,) = capabilities_from_openai_tools([TOOL])
    assert (cap.name, cap.description, cap.parameters) == ("get_weather", "Weather", {"type": "object"})


@pytest.mark.parametrize(
    ("bad", "field"),
    [
        ([{"role": "robot", "content": "x"}], "messages[0].role"),
        ([{"role": "user", "content": 3}], "messages[0].content"),
        (["nope"], "messages[0]"),
        ([{"role": "tool", "content": "x"}], "messages[0].tool_call_id"),
        ([{"role": "tool", "tool_call_id": "z", "content": "x"}], "messages[0].name"),
        (
            [{"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "f", "arguments": "{"}}]}],
            "messages[0].tool_calls[0].function.arguments",
        ),
    ],
)
def test_non_conforming_messages_name_the_field_and_leave_input_untouched(bad, field):
    before = copy.deepcopy(bad)
    with pytest.raises(ValidationError) as exc:
        messages_from_openai(bad)
    assert exc.value.details["field"] == field
    assert bad == before


def test_non_conforming_tool_is_rejected():
    with pytest.raises(ValidationError) as exc:
        capabilities_from_openai_tools([{"type": "function", "function": {"description": "no name"}}])
    assert exc.value.details["field"] == "tool.function.name"
