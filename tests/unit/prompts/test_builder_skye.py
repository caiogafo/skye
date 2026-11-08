"""`.skye` prompts in the builder registry and the loader (task 4.6, builder side)."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import pytest

from skye.base.exceptions import ValidationError
from skye.base.messages import SkyeMessage, UserMessage
from skye.prompts import BasePromptBuilder
from skye.prompts.loaders import load_default_templates

PROMPT = """# greeting prompt
prompt "greet" {
  variables = { name = string, tone = string("warm") }
  message "system" { text = "Be {{ tone }}." }
  placeholder "history"
  message "user" { text = "Hello {{ name | shout }}" }
}
"""


@pytest.fixture(scope="module")
def shared() -> BasePromptBuilder:
    return BasePromptBuilder()


@pytest.fixture
def builder(shared: BasePromptBuilder) -> BasePromptBuilder:
    return shared.partial()


def test_skye_text_is_registered_as_a_prompt(builder: BasePromptBuilder) -> None:
    builder.register_template("greet", PROMPT)
    assert builder.get_template("greet") == PROMPT
    assert builder.get_template_variables("greet") == ["name", "tone"]
    meta = builder.get_template_metadata("greet")
    assert (meta["format"], meta["variables"], meta["optional_variables"]) == (
        "skye",
        ["name"],
        ["tone"],
    )
    assert builder.validate_template("greet")["valid"] is True


def test_skye_file_is_registered(builder: BasePromptBuilder, tmp_path: Path) -> None:
    path = tmp_path / "other_name.skye"
    path.write_text(PROMPT)
    builder.register_template("hello", str(path), from_string=False)
    assert builder.get_template("hello") == PROMPT


def test_invalid_skye_raises_with_diagnostics(builder: BasePromptBuilder) -> None:
    with pytest.raises(ValidationError, match="Invalid .skye prompt 'bad'") as info:
        builder.register_template("bad", 'prompt "bad" {\n  message "user" { nope = 1 }\n}\n')
    assert info.value.details["diagnostics"]


def test_render_dispatches_to_render_prompt(
    builder: BasePromptBuilder, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, Any] = {}

    def render_prompt(spec: Any, variables: Any, *, history: Any = None, filters: Any = None):
        seen.update(spec=spec, variables=dict(variables), history=history, filters=filters)
        return [UserMessage(content="rendered")]

    fake = types.ModuleType("skye.prompts.skye_prompts")
    fake.render_prompt = render_prompt  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "skye.prompts.skye_prompts", fake)

    builder.register_template("greet", PROMPT)
    builder.register_jinja_filter("shout", str.upper)
    builder.set_default_values({"tone": "dry", "unused": "u"})
    child = builder.partial(name="partial")
    history = [{"role": "user", "content": "before"}]
    messages = child.render("greet", {"name": "Ada", "history": history})
    assert [m.content for m in messages] == ["rendered"]
    assert seen["spec"].name == "greet"
    assert seen["variables"]["name"] == "Ada"  # provided wins over partial
    assert seen["variables"]["tone"] == "dry"  # builder default
    assert "history" not in seen["variables"]
    assert [m.content for m in seen["history"]["history"]] == ["before"]
    assert set(seen["filters"]) == {"shout"}


def test_render_with_the_real_renderer(builder: BasePromptBuilder) -> None:
    pytest.importorskip("skye.prompts.skye_prompts")
    builder.register_template("greet", PROMPT)
    builder.register_jinja_filter("shout", lambda v: f"{v}!")
    messages = builder.render(
        "greet", {"name": "Ada", "history": [{"role": "assistant", "content": "hi"}]}
    )
    assert [(m.role, m.content) for m in messages] == [
        ("system", "Be warm."),
        ("assistant", "hi"),
        ("user", "Hello Ada!"),
    ]
    assert all(isinstance(m, SkyeMessage) for m in messages)
    with pytest.raises(ValueError, match="Missing required variable"):
        builder.render("greet", {})


def test_compose_rejects_skye_parts(builder: BasePromptBuilder) -> None:
    builder.register_template("greet", PROMPT)
    builder.register_template("text", "x")
    with pytest.raises(ValidationError, match="Cannot compose"):
        builder.compose_templates("both", ["text", "greet"])


def test_loader_registers_skye_over_jinja(tmp_path: Path, builder: BasePromptBuilder) -> None:
    (tmp_path / "greet.jinja").write_text("old {{ name }}")
    (tmp_path / "greet.skye").write_text(PROMPT)
    (tmp_path / "plain.jinja").write_text("plain {{ x }}")
    assert load_default_templates(builder, tmp_path) == 2
    assert builder.get_template("greet") == PROMPT
    assert builder.get_template("plain") == "plain {{ x }}"
