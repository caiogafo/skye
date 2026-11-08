"""Few-shot examples: injection, default limit, selectors (tasks 3.1, 3.2; property 4)."""

from __future__ import annotations

import pytest

from skye.base.exceptions import ValidationError
from skye.prompts import BasePromptBuilder
from skye.prompts.messages import DEFAULT_MAX_EXAMPLES


@pytest.fixture(scope="module")
def shared() -> BasePromptBuilder:
    return BasePromptBuilder()


@pytest.fixture
def builder(shared: BasePromptBuilder) -> BasePromptBuilder:
    return shared.partial()


EXAMPLES = [{"input": f"in{i}", "output": f"out{i}"} for i in range(12)]


def test_one_default_limit_for_no_selector_and_selector(builder: BasePromptBuilder) -> None:
    builder.add_examples("t", EXAMPLES)
    assert len(builder._select_examples("t", {})) == DEFAULT_MAX_EXAMPLES
    builder.set_example_selector("t", "fixed")
    assert len(builder._select_examples("t", {})) == DEFAULT_MAX_EXAMPLES


@pytest.mark.parametrize(
    ("template", "example_template"),
    [
        ("Task\n{examples}Now: {q}", "Q={input} A={output}"),
        ("Task\n{{ examples }}Now: {{ q }}", "Q={{ input }} A={{ output }}"),
        ("Task\n{{ examples }}Now: {{ q }}", "Q={input} A={output}"),
        ("Task\n{examples}Now: {q}", "Q={{ input }} A={{ output }}"),
    ],
)
def test_examples_are_injected_for_both_template_kinds(
    builder: BasePromptBuilder, template: str, example_template: str
) -> None:
    builder.register_template("t", template)
    builder.add_examples("t", EXAMPLES[:2], example_template)
    content = builder.render("t", {"q": "x"})[0].content
    assert content == "Task\nQ=in0 A=out0\n\nQ=in1 A=out1\n\nNow: x"


def test_example_missing_a_field_is_skipped(builder: BasePromptBuilder) -> None:
    builder.register_template("t", "{{ examples }}")
    builder.add_examples("t", [{"input": "a"}, {"input": "b", "output": "c"}])
    assert builder.render("t", {})[0].content.strip() == "Input: b\nOutput: c"


def test_unknown_selector_type_lists_the_supported_ones(builder: BasePromptBuilder) -> None:
    with pytest.raises(ValidationError, match="fixed, random, semantic"):
        builder.set_example_selector("t", "length_based")


def test_semantic_selector_needs_an_embedder(builder: BasePromptBuilder) -> None:
    with pytest.raises(ValidationError, match="embedder"):
        builder.set_example_selector("t", "semantic")


def _embed(text: str) -> list[float]:
    """Tiny bag of letters: a, b, c counts."""
    return [float(text.count(ch)) for ch in "abc"]


def test_semantic_selector_picks_the_most_similar(builder: BasePromptBuilder) -> None:
    examples = [
        {"input": "ccc", "output": "1"},
        {"input": "aaa", "output": "2"},
        {"input": "aab", "output": "3"},
        {"input": "bbb", "output": "4"},
    ]
    calls: list[str] = []

    def embedder(text: str) -> list[float]:
        calls.append(text)
        return _embed(text)

    builder.add_examples("t", examples)
    builder.set_example_selector("t", "semantic", max_examples=2, embedder=embedder)
    chosen = builder._select_examples("t", {"input": "aaaa"})
    assert [e["output"] for e in chosen] == ["2", "3"]
    chosen = builder._select_examples("t", {"input": "bbbb"})
    assert [e["output"] for e in chosen] == ["4", "3"]
    assert len(calls) == len(examples) + 2  # example vectors are computed once


def test_semantic_selector_input_and_example_keys(builder: BasePromptBuilder) -> None:
    examples = [{"q": "ccc", "a": "1"}, {"q": "aaa", "a": "2"}]
    builder.add_examples("t", examples, "{q}->{a}")
    builder.set_example_selector(
        "t", "semantic", max_examples=1, embedder=_embed, input_key="question", example_key="q"
    )
    builder.register_template("t", "{{ examples }}{{ question }}")
    assert builder.render("t", {"question": "a"})[0].content == "aaa->2\n\na"


# -- property 4 ------------------------------------------------------------------------------------


@pytest.mark.parametrize("count", [0, 1, 3, 12])
@pytest.mark.parametrize("limit", [0, 1, 2, 5, 20])
def test_property_4_fixed_is_stable_random_is_bounded(
    builder: BasePromptBuilder, count: int, limit: int
) -> None:
    builder.add_examples("t", EXAMPLES[:count])
    builder.set_example_selector("t", "fixed", max_examples=limit)
    first = builder._select_examples("t", {})
    assert first == builder._select_examples("t", {}) == EXAMPLES[: min(count, limit)]
    builder.set_example_selector("t", "random", max_examples=limit)
    for _ in range(5):
        chosen = builder._select_examples("t", {})
        assert len(chosen) == min(count, limit)
        assert all(e in EXAMPLES[:count] for e in chosen)


_SKYE_LIST = """prompt "fs" {
  variables = {
    examples = list({
                 input  = string
                 output = string
               }, [])  "Worked examples"
    q        = string  "The question"
  }
  message "user" {
    each ex in examples { text = "Q={{ ex.input }} A={{ ex.output }}" }
    text = "Now: {{ q }}"
  }
}
"""

_SKYE_TEXT = """prompt "fs" {
  variables = {
    examples = string("")  "Examples, as text"
    q        = string      "The question"
  }
  message "user" { text = "{{ examples }}Now: {{ q }}" }
}
"""


def test_skye_list_examples_get_the_selected_dicts(builder: BasePromptBuilder) -> None:
    builder.register_template("fs", _SKYE_LIST)
    builder.add_examples("fs", EXAMPLES[:4], "ignored {input}")
    builder.set_example_selector("fs", "fixed", max_examples=2)
    content = builder.format("fs", {"q": "x"})
    assert "Q=in0 A=out0" in content
    assert "Q=in1 A=out1" in content
    assert "in2" not in content
    assert "ignored" not in content
    assert content.rstrip().endswith("Now: x")


def test_skye_list_examples_use_the_semantic_selector(builder: BasePromptBuilder) -> None:
    builder.register_template("fs", _SKYE_LIST)
    builder.add_examples(
        "fs", [{"input": "ccc", "output": "1"}, {"input": "aaa", "output": "2"}]
    )
    builder.set_example_selector("fs", "semantic", max_examples=1, embedder=_embed, input_key="q")
    content = builder.format("fs", {"q": "aa"})
    assert "Q=aaa A=2" in content
    assert "ccc" not in content


def test_skye_string_examples_are_still_formatted(builder: BasePromptBuilder) -> None:
    builder.register_template("fs", _SKYE_TEXT)
    builder.add_examples("fs", EXAMPLES[:1], "Q={input} A={output}")
    assert builder.format("fs", {"q": "x"}) == "Q=in0 A=out0\n\nNow: x"


def test_explicit_examples_win_over_added_ones(builder: BasePromptBuilder) -> None:
    builder.register_template("fs", _SKYE_LIST)
    builder.add_examples("fs", EXAMPLES[:2])
    content = builder.format("fs", {"q": "x", "examples": [{"input": "mine", "output": "y"}]})
    assert "Q=mine A=y" in content
    assert "in0" not in content
