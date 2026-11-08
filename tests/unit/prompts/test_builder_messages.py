"""Roles, placeholders, multimodal content and capability messages (tasks 3.3, 3.4, 3.6;
properties 5 and 7)."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from skye.base.exceptions import ValidationError
from skye.base.messages import (
    AssistantMessage,
    CapabilityMessage,
    SystemMessage,
    UserMessage,
)
from skye.prompts import BasePromptBuilder


@pytest.fixture(scope="module")
def shared() -> BasePromptBuilder:
    return BasePromptBuilder()


@pytest.fixture
def builder(shared: BasePromptBuilder) -> BasePromptBuilder:
    return shared.partial()


def roles(messages: list) -> list[tuple[str, str]]:
    return [(m.role, m.content) for m in messages]


# -- 3.3 placeholders and roles -------------------------------------------------------------------


HISTORY = [
    {"role": "user", "content": "earlier question"},
    AssistantMessage(content="earlier answer"),
]


@pytest.mark.parametrize("marker", ["[PLACEHOLDER history]", "[PLACEHOLDER:history]"])
def test_history_goes_at_the_placeholder_line(builder: BasePromptBuilder, marker: str) -> None:
    builder.register_template("t", f"[SYSTEM]\nBe brief.\n{marker}\n[USER]\n{{{{ q }}}}")
    builder.add_message_placeholder("t", "history")
    messages = builder.render("t", {"q": "now?", "history": HISTORY})
    assert roles(messages) == [
        ("system", "Be brief."),
        ("user", "earlier question"),
        ("assistant", "earlier answer"),
        ("user", "now?"),
    ]


def test_history_goes_before_the_last_user_message_without_a_marker(
    builder: BasePromptBuilder,
) -> None:
    builder.register_template("t", "[SYSTEM]\nBe brief.\n[USER]\n{{ q }}")
    builder.add_message_placeholder("t", "history", role="assistant")
    messages = builder.render("t", {"q": "now?", "history": ["plain text answer"]})
    assert roles(messages) == [
        ("system", "Be brief."),
        ("assistant", "plain text answer"),
        ("user", "now?"),
    ]
    # Without a history nothing is inserted.
    assert len(builder.render("t", {"q": "now?"})) == 2


def test_history_with_an_invalid_role_is_rejected(builder: BasePromptBuilder) -> None:
    builder.register_template("t", "{{ q }}")
    builder.add_message_placeholder("t", "history")
    with pytest.raises(ValidationError, match="system, user, assistant, capability"):
        builder.render("t", {"q": "x", "history": [{"role": "robot", "content": "x"}]})


def test_invalid_roles_are_rejected_at_configuration(builder: BasePromptBuilder) -> None:
    with pytest.raises(ValidationError, match="Valid roles: system, user, assistant, capability"):
        builder.set_message_roles("t", {"intro": "narrator"})
    with pytest.raises(ValidationError, match="Valid roles"):
        builder.add_message_placeholder("t", "history", role="human")


def test_unknown_marker_is_rejected(builder: BasePromptBuilder) -> None:
    builder.register_template("t", "[SYSTEM]\nx\n[NARRATOR]\ny")
    with pytest.raises(ValidationError, match=r"\[NARRATOR\].*Valid roles"):
        builder.render("t", {})


def test_role_mapping_names_custom_sections(builder: BasePromptBuilder) -> None:
    builder.register_template("t", "[context]\nFacts.\n[question]\nWhy?")
    builder.set_message_roles("t", {"context": "system", "question": "user"})
    assert roles(builder.render("t", {})) == [("system", "Facts."), ("user", "Why?")]


def test_text_in_brackets_is_not_a_marker(builder: BasePromptBuilder) -> None:
    builder.register_template("t", "[note] keep this\n[1]")
    assert roles(builder.render("t", {})) == [("user", "[note] keep this\n[1]")]


# -- 3.4 multimodal content -----------------------------------------------------------------------


def test_image_url_goes_to_the_user_message(builder: BasePromptBuilder) -> None:
    builder.register_template("t", "[SYSTEM]\nLook.\n[USER]\nDescribe {image}")
    builder.add_image_content("t", "image", "url")
    messages = builder.render("t", {"image": "https://example.com/a.png"})
    user = messages[-1]
    assert isinstance(user, UserMessage)
    assert user.images == ["https://example.com/a.png"]
    assert "https://example.com/a.png" in user.content
    assert all(m.metadata["content_types"] == {"image": "image:url"} for m in messages)


def test_image_base64_becomes_bytes(builder: BasePromptBuilder) -> None:
    raw = b"\x89PNG fake"
    builder.register_template("t", "Describe the image")
    builder.add_image_content("t", "img", "base64")
    messages = builder.render("t", {"img": [base64.b64encode(raw).decode()]})
    assert messages[0].images == [raw]
    with pytest.raises(ValidationError, match="not valid base64.*url, base64, path"):
        builder.render("t", {"img": "%%%not base64"})


def test_image_path_must_exist(builder: BasePromptBuilder, tmp_path: Path) -> None:
    image = tmp_path / "a.png"
    image.write_bytes(b"\x89PNG")
    builder.register_template("t", "Describe the image")
    builder.add_image_content("t", "img", "path")
    assert builder.render("t", {"img": str(image)})[0].images == [image]
    with pytest.raises(ValidationError, match="no file"):
        builder.render("t", {"img": str(tmp_path / "missing.png")})


def test_invalid_url_and_formats_list_the_supported_ones(builder: BasePromptBuilder) -> None:
    builder.register_template("t", "x")
    builder.add_image_content("t", "img")
    with pytest.raises(ValidationError, match="Supported formats: url, base64, path"):
        builder.render("t", {"img": "ftp://example.com/a.png"})
    with pytest.raises(ValidationError, match="Supported formats: url, base64, path"):
        builder.add_image_content("t", "img", "svg")
    with pytest.raises(ValidationError, match="Supported types: text, image, audio"):
        builder.add_multimodal_content("t", {"clip": "hologram"})
    with pytest.raises(ValidationError, match="Supported formats"):
        builder.add_multimodal_content("t", {"pic": "image:svg"})


def test_multimodal_content_types_are_recorded(builder: BasePromptBuilder) -> None:
    builder.register_template("t", "Listen to {audio}")
    builder.add_multimodal_content("t", {"audio": "audio", "pic": "image:url"})
    messages = builder.render(
        "t", {"audio": "s3://bucket/a.mp3", "pic": "data:image/png;base64,AAAA"}
    )
    assert messages[0].metadata["content_types"] == {"audio": "audio", "pic": "image:url"}
    assert messages[0].images == ["data:image/png;base64,AAAA"]
    assert builder.get_template_metadata("t")["content_types"] == ["audio", "image:url"]


# -- 3.6 capability messages ----------------------------------------------------------------------


def test_capability_section_makes_a_capability_message(builder: BasePromptBuilder) -> None:
    builder.register_template(
        "t", "[USER]\nWeather?\n[CAPABILITY get_weather call_1]\n{{ result }}\n[ASSISTANT]\nSunny."
    )
    messages = builder.render("t", {"result": '{"sky": "clear"}'})
    assert [type(m) for m in messages] == [UserMessage, CapabilityMessage, AssistantMessage]
    capability = messages[1]
    assert isinstance(capability, CapabilityMessage)
    assert (capability.capability_name, capability.capability_id) == ("get_weather", "call_1")


def test_capability_section_needs_a_name_and_an_id(builder: BasePromptBuilder) -> None:
    builder.register_template("t", "[CAPABILITY get_weather]\nresult")
    with pytest.raises(ValidationError, match=r"\[CAPABILITY name call_id\]"):
        builder.render("t", {})


def test_capability_message_helper(builder: BasePromptBuilder) -> None:
    message = builder.capability_message("search", "c9", {"hits": [1, 2]})
    assert message.content == json.dumps({"hits": [1, 2]})
    assert (message.capability_name, message.capability_id, message.is_error) == (
        "search",
        "c9",
        False,
    )
    assert builder.capability_message("s", "c", "raw", status="error").content == "raw"
    assert builder.capability_message("s", "c", "raw", status="error").is_error


# -- properties 5 and 7 ---------------------------------------------------------------------------

SECTIONS = [
    [("SYSTEM", "s")],
    [("USER", "u")],
    [("SYSTEM", "s"), ("USER", "u")],
    [("SYSTEM", "s"), ("USER", "u"), ("ASSISTANT", "a"), ("USER", "u2")],
    [("ASSISTANT", "a1"), ("ASSISTANT", "a2")],
]
TYPES = {"SYSTEM": SystemMessage, "USER": UserMessage, "ASSISTANT": AssistantMessage}


@pytest.mark.parametrize("sections", SECTIONS)
def test_property_5_one_message_per_role_section(
    builder: BasePromptBuilder, sections: list[tuple[str, str]]
) -> None:
    text = "\n".join(f"[{marker}]\n{body} {{{{ v }}}}" for marker, body in sections)
    builder.register_template("t", text)
    messages = builder.render("t", {"v": "x"})
    assert [type(m) for m in messages] == [TYPES[marker] for marker, _ in sections]
    assert [m.content for m in messages] == [f"{body} x" for _, body in sections]


@pytest.mark.parametrize(
    "parts", [["a"], ["a", "b"], ["Hi {name}", "{{ x }}", "plain"], ["", "x", ""]]
)
@pytest.mark.parametrize("separator", ["\n\n", " | ", ""])
def test_property_7_composition_equals_join(
    builder: BasePromptBuilder, parts: list[str], separator: str
) -> None:
    names = []
    for i, text in enumerate(parts):
        builder.register_template(f"part{i}", text)
        names.append(f"part{i}")
    builder.compose_templates("whole", names, separator)
    assert builder.get_template("whole") == separator.join(parts)
