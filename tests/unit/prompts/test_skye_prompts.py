"""Tests for the ``.skye`` prompt renderer (task 4.2, D60)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from skye.base.dsl import PromptSpec
from skye.base.exceptions import ValidationError
from skye.base.interfaces.runnable import Runnable
from skye.base.messages import AssistantMessage, SkyeMessage, SystemMessage, UserMessage
from skye.prompts.skye_prompts import PromptRunnable, load_prompt, render_prompt

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "skye" / "prompts.skye"


@pytest.fixture(scope="module")
def fixture_text() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def _chat_vars(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "user_message": "Hi",
        "personality": [],
        "guidelines": [],
        "conversation_history": [],
    }
    return {**base, **overrides}


def _pairs(messages: list[SkyeMessage]) -> list[tuple[str, str]]:
    return [(m.role, m.content) for m in messages]


# -- load_prompt -------------------------------------------------------------------------------


def test_load_prompt_by_name(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "summarize")
    assert isinstance(spec, PromptSpec)
    assert spec.name == "summarize"


def test_load_prompt_single_without_name() -> None:
    spec = load_prompt('prompt "p" { message "user" { text = "hi" } }')
    assert spec.name == "p"


def test_load_prompt_unknown_name(fixture_text: str) -> None:
    with pytest.raises(KeyError):
        load_prompt(fixture_text, "nope")


def test_load_prompt_invalid_text_raises_validation_error_with_diagnostics() -> None:
    with pytest.raises(ValidationError) as info:
        load_prompt('prompt "p" { message "user" { text = "{{ ghost }}" } }')
    assert "ghost" in str(info.value)
    assert info.value.details["diagnostics"]


# -- chat (P0) ---------------------------------------------------------------------------------


def test_chat_minimal(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "chat")
    messages = render_prompt(spec, _chat_vars())
    assert _pairs(messages) == [("system", "You are a helpful AI assistant."), ("user", "Hi")]
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], UserMessage)


def test_chat_every_branch(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "chat")
    history = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hey"}]
    messages = render_prompt(
        spec,
        _chat_vars(
            persona="a lawyer",
            domain="law",
            personality=["kind", "calm"],
            guidelines=["be brief", "cite"],
            conversation_history=history,
            context="ctx",
            output_format="JSON",
        ),
    )
    assert _pairs(messages) == [
        (
            "system",
            "You are a lawyer.\nSpecialized in law.\nYour personality traits: kind, calm.\n"
            "Please follow these guidelines:\n- be brief\n- cite",
        ),
        ("user", "hello"),
        ("assistant", "hey"),
        ("user", "Hi\nContext: ctx\nPlease format your response as JSON."),
    ]
    assert isinstance(messages[2], AssistantMessage)


def test_role_from_invalid_role(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "chat")
    with pytest.raises(ValidationError) as info:
        render_prompt(spec, _chat_vars(conversation_history=[{"role": "robot", "content": "x"}]))
    message = str(info.value)
    assert "robot" in message
    for role in ("system", "user", "assistant"):
        assert role in message


def test_role_from_missing_key_is_invalid_role(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "chat")
    with pytest.raises(ValidationError):
        render_prompt(spec, _chat_vars(conversation_history=[{"content": "x"}]))


# -- variables (P1) -----------------------------------------------------------------------------


def test_defaults_apply_and_provided_win(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "summarize")
    assert _pairs(render_prompt(spec, {"text": "T"})) == [
        ("user", "Summarize the text in at most 100 words.\nStyle: neutral.\n---\nT")
    ]
    assert _pairs(render_prompt(spec, {"text": "T", "max_words": 5, "style": "formal"})) == [
        ("user", "Summarize the text in at most 5 words.\nStyle: formal.\n---\nT")
    ]


def test_falsy_value_skips_when(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "summarize")
    assert _pairs(render_prompt(spec, {"text": "T", "style": ""})) == [
        ("user", "Summarize the text in at most 100 words.\n---\nT")
    ]


def test_missing_required_variable(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "summarize")
    with pytest.raises(ValueError, match=r"^Missing required variable.*\btext\b"):
        render_prompt(spec, {})


def test_missing_required_variables_all_named_sorted(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "support_chat")
    with pytest.raises(ValidationError) as info:
        render_prompt(spec, {})
    assert str(info.value).startswith("Missing required variable")
    assert info.value.details["value"] == ["product", "question"]
    assert "product, question" in str(info.value)


def test_undeclared_variables_are_ignored(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "support_chat")
    messages = render_prompt(spec, {"product": "P", "question": "Q", "extra": 1})
    assert [m.role for m in messages] == ["system", "user"]


def test_allow_missing_without_default_is_none() -> None:
    spec = load_prompt(
        'prompt "p" {\n'
        "  variables = { name = string, note = string }\n"
        '  allow_missing = ["note"]\n'
        '  message "user" {\n'
        '    text = "Hi {{ name }}[{{ note }}]"\n'
        '    when note { text = "note: {{ note }}" }\n'
        "  }\n"
        "}"
    )
    assert _pairs(render_prompt(spec, {"name": "A"})) == [("user", "Hi A[]")]
    assert _pairs(render_prompt(spec, {"name": "A", "note": "n"})) == [("user", "Hi A[n]\nnote: n")]


# -- placeholder (P2) -----------------------------------------------------------------------------


def test_placeholder_from_history(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "support_chat")
    history = {
        "history": [UserMessage(content="first"), {"role": "assistant", "content": "second"}]
    }
    messages = render_prompt(spec, {"product": "P", "question": "Q"}, history=history)
    assert _pairs(messages) == [
        ("system", "You are the support agent of P. Answer in the user's language."),
        ("user", "first"),
        ("assistant", "second"),
        ("user", "Q"),
    ]
    assert isinstance(messages[2], AssistantMessage)


def test_placeholder_falls_back_to_variable(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "support_chat")
    messages = render_prompt(
        spec, {"product": "P", "question": "Q", "history": [{"role": "user", "content": "h"}]}
    )
    assert [m.content for m in messages][1] == "h"


def test_history_wins_over_variable(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "support_chat")
    messages = render_prompt(
        spec,
        {"product": "P", "question": "Q", "history": [{"role": "user", "content": "var"}]},
        history={"history": [{"role": "user", "content": "hist"}]},
    )
    assert [m.content for m in messages][1] == "hist"


def test_placeholder_absent_inserts_nothing(fixture_text: str) -> None:
    spec = load_prompt(fixture_text, "support_chat")
    assert len(render_prompt(spec, {"product": "P", "question": "Q"})) == 2


def test_placeholder_bad_entry() -> None:
    spec = load_prompt('prompt "p" { placeholder "h" }')
    with pytest.raises(ValidationError):
        render_prompt(spec, {}, history={"h": ["not a message"]})  # type: ignore[list-item]


# -- structure ------------------------------------------------------------------------------------


def test_top_level_when_and_each_hold_messages() -> None:
    spec = load_prompt(
        'prompt "p" {\n'
        "  variables = { greet = bool(false), items = list }\n"
        '  when greet { message "system" { text = "hello" } }\n'
        '  each it in items { message "user" { text = "{{ it.name }}" } }\n'
        "}"
    )
    assert _pairs(render_prompt(spec, {"items": [{"name": "a"}, {"name": "b"}]})) == [
        ("user", "a"),
        ("user", "b"),
    ]
    assert _pairs(render_prompt(spec, {"greet": True, "items": []})) == [("system", "hello")]


def test_empty_message_is_skipped() -> None:
    spec = load_prompt(
        'prompt "p" {\n'
        '  variables = { x = string("") }\n'
        '  message "system" { when x { text = "{{ x }}" } }\n'
        '  message "user" { text = "{{ x }}" }\n'
        '  message "assistant" { text = "ok" }\n'
        "}"
    )
    assert _pairs(render_prompt(spec, {})) == [("assistant", "ok")]


def test_missing_key_in_mapping_reads_as_none() -> None:
    spec = load_prompt(
        'prompt "p" {\n'
        "  variables = { examples = list }\n"
        '  message "user" {\n'
        "    each ex in examples {\n"
        '      text = "{{ ex.text }}"\n'
        '      when ex.reasoning { text = "why: {{ ex.reasoning }}" }\n'
        '      when ex.meta.score { text = "score" }\n'
        "    }\n"
        "  }\n"
        "}"
    )
    examples = [{"text": "a", "reasoning": "r"}, {"text": "b"}]
    assert _pairs(render_prompt(spec, {"examples": examples})) == [("user", "a\nwhy: r\nb")]
    assert examples[1] == {"text": "b"}  # the caller's data is not changed


def test_each_over_non_list_raises() -> None:
    spec = load_prompt(
        'prompt "p" {\n'
        "  variables = { n = number }\n"
        '  message "user" { each i in n { text = "{{ i }}" } }\n'
        "}"
    )
    with pytest.raises(ValidationError):
        render_prompt(spec, {"n": 3})


def test_custom_filters() -> None:
    spec = load_prompt(
        'prompt "p" {\n  variables = { name = string }\n'
        '  message "user" { text = "{{ name | shout }}" }\n}'
    )
    messages = render_prompt(
        spec, {"name": "hi"}, filters={"shout": lambda v: str(v).upper() + "!"}
    )
    assert _pairs(messages) == [("user", "HI!")]


def test_condition_expression() -> None:
    spec = load_prompt(
        'prompt "p" {\n'
        '  variables = { mode = string("short") }\n'
        '  message "user" {\n'
        '    text = "go"\n'
        '    when mode == "detailed" { text = "in detail" }\n'
        "  }\n"
        "}"
    )
    assert _pairs(render_prompt(spec, {})) == [("user", "go")]
    assert _pairs(render_prompt(spec, {"mode": "detailed"})) == [("user", "go\nin detail")]


# -- Runnable adapter --------------------------------------------------------------------------


def test_prompt_runnable(fixture_text: str) -> None:
    runnable = PromptRunnable(load_prompt(fixture_text, "support_chat"))
    assert isinstance(runnable, Runnable)
    assert runnable.name == "support_chat"
    messages = asyncio.run(runnable.invoke({"product": "P", "question": "Q"}))
    assert [m.role for m in messages] == ["system", "user"]
    assert asyncio.run(runnable.ainvoke({"product": "P", "question": "Q"}))[1].content == "Q"
