"""Lexer and parser of the ``.skye`` language: tokens, positions, tree
shape, round-trip properties.
"""

from __future__ import annotations

import random

import pytest

from skye.base.dsl import SkyeSyntaxError, parse, parse_collect, tokenize
from skye.base.dsl.tree import (
    Attribute,
    Bool,
    Expr,
    ListNode,
    MapNode,
    Name,
    Num,
    Str,
    TypeCall,
)


def kinds(text: str) -> list[str]:
    tokens, errors = tokenize(text, "t")
    assert not errors
    return [t.kind for t in tokens]


def test_tokens_have_line_and_column() -> None:
    tokens, _ = tokenize('flow "x" {\n  a = 1\n}\n', "t")
    by_text = {t.text: t for t in tokens if t.text.strip()}
    assert (by_text["flow"].line, by_text["flow"].column) == (1, 1)
    assert (by_text['"x"'].line, by_text['"x"'].column) == (1, 6)
    assert (by_text["a"].line, by_text["a"].column) == (2, 3)
    assert (by_text["}"].line, by_text["}"].column) == (3, 1)


def test_comments_are_dropped_and_hash_in_a_string_is_kept() -> None:
    tokens, _ = tokenize('a = "x # not a comment" # a comment\n', "t")
    assert [t.text for t in tokens if t.kind == "string"] == ['"x # not a comment"']
    assert all("comment" not in t.text for t in tokens if t.kind != "string")


def test_string_escapes_and_multiline_string() -> None:
    tokens, _ = tokenize('a = "x\\ny\\"z"\nb = """\n  one\n    two\n  """\n', "t")
    strings = [t.value for t in tokens if t.kind == "string"]
    assert strings == ['x\ny"z', "one\n  two"]
    last = [t for t in tokens if t.kind == "ident"][-1]
    assert last.text == "b" and last.line == 2


def test_numbers() -> None:
    tokens, errors = tokenize("a = 12 b = 3.5 c = 1e3", "t")
    assert not errors
    assert [t.value for t in tokens if t.kind == "number"] == [12, 3.5, 1000.0]


def test_lexer_reports_a_bad_number_and_unexpected_character() -> None:
    _, errors = tokenize("timeout = 30s\nx = @\n", "t")
    assert [(e.line, e.column) for e in errors] == [(1, 11), (2, 5)]
    assert "not a valid number" in errors[0].reason


def test_unterminated_triple_quote() -> None:
    _, errors = tokenize('a = """never closed', "t")
    assert errors and "unterminated" in errors[0].reason


def test_lexer_never_crashes_on_random_text() -> None:
    rng = random.Random(7)
    alphabet = list('abc =.,{}[]()"\n#\\ 0129+-*/<>!:\t@$')
    for _ in range(300):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60)))
        tokens, _ = tokenize(text, "t")
        assert tokens[-1].kind == "eof"
        for tok in tokens:
            assert 0 <= tok.start <= tok.end <= len(text)
            assert tok.line >= 1 and tok.column >= 1


def test_parser_never_crashes_on_random_text() -> None:
    rng = random.Random(11)
    words = [
        "flow",
        "step",
        "next",
        "=",
        "{",
        "}",
        '"a"',
        "[",
        "]",
        ",",
        "\n",
        "end",
        "1",
        "when",
        "else",
    ]
    for _ in range(300):
        text = " ".join(rng.choice(words) for _ in range(rng.randint(0, 25)))
        parse_collect(text, "t")


def test_non_comment_tokens_reproduce_the_text() -> None:
    text = 'router "m" {\n  route "a" = ["x/y"]  # c\n  n = 1.5\n}\n'
    tokens, _ = tokenize(text, "t")
    rebuilt = "".join(t.text for t in tokens if t.kind not in ("newline", "eof"))
    assert rebuilt == "".join(text.replace("  # c", "").split())


def test_block_with_label_attributes_and_nested_blocks() -> None:
    tree = parse('flow "f" {\n  step "A" { run = registry.a, next = end }\n}\n', "f.skye")
    (flow,) = tree.blocks
    assert flow.kind == "flow" and flow.label_text == "f" and (flow.line, flow.column) == (1, 1)
    (step,) = flow.blocks()
    assert step.kind == "step" and (step.line, step.column) == (2, 3)
    run, nxt = step.attributes()
    assert isinstance(run.value, Name) and run.value.path == ("registry", "a")
    assert isinstance(nxt.value, Name) and nxt.value.path == ("end",)
    assert (run.name_line, run.name_column) == (2, 14)


def test_value_kinds() -> None:
    tree = parse(
        'x {\n  a = "s"\n  b = 4\n  c = -2\n  d = true\n  e = [1, "two"]\n'
        "  f = { k = 1, j = env.X }\n  g = context.n + 1\n  h = number(0)\n  i = step.A.output\n}\n"
    )
    values = {a.name: a.value for a in tree.blocks[0].attributes()}
    assert isinstance(values["a"], Str) and values["a"].value == "s"
    assert isinstance(values["b"], Num) and values["b"].value == 4
    assert isinstance(values["c"], Num) and values["c"].value == -2
    assert isinstance(values["d"], Bool) and values["d"].value is True
    assert isinstance(values["e"], ListNode) and len(values["e"].items) == 2
    assert isinstance(values["f"], MapNode) and [e.key for e in values["f"].entries] == ["k", "j"]
    assert isinstance(values["g"], Expr) and values["g"].text == "context.n + 1"
    assert isinstance(values["h"], TypeCall) and values["h"].name == "number"
    assert isinstance(values["i"], Name) and values["i"].text == "step.A.output"


def test_multiline_lists_and_maps_and_trailing_commas() -> None:
    tree = parse("x {\n  a = [\n    1,\n    2,\n  ]\n  b = {\n    k = 1,\n    j = 2\n  }\n}\n")
    a, b = tree.blocks[0].attributes()
    assert isinstance(a.value, ListNode) and len(a.value.items) == 2
    assert isinstance(b.value, MapNode) and len(b.value.entries) == 2


def test_set_emit_when_else_each_forms() -> None:
    tree = parse(
        'choice "C" {\n  when a.b >= 3 { set x = 1\n next = "A" }\n'
        '  else { emit "e", next = end }\n}\n'
        'm { each t in items { message t.role { text = "x" } } }\n'
    )
    choice, outer = tree.blocks
    when, other = choice.blocks()
    assert when.kind == "when" and isinstance(when.head, Expr) and when.head.text == "a.b >= 3"
    (setter, nxt) = when.body
    assert isinstance(setter, Attribute) and setter.keyword == "set" and setter.name == "x"
    assert other.kind == "else"
    emit = other.attributes()[0]
    assert emit.keyword == "emit" and isinstance(emit.value, Str)
    each = outer.blocks()[0]
    assert each.kind == "each" and each.var == "t"
    msg = each.blocks()[0]
    assert isinstance(msg.label, Name) and msg.label.text == "t.role"


def test_shorthand_route_and_braceless_block() -> None:
    tree = parse('router {\n  route "fast" = ["a/b", "c/d"]\n  placeholder "history"\n}\n')
    route, placeholder = tree.blocks[0].blocks()
    assert route.kind == "route" and isinstance(route.value, ListNode) and route.braces is False
    assert placeholder.kind == "placeholder" and placeholder.braces is False


def test_expression_is_kept_as_text_with_position() -> None:
    tree = parse("x {\n  a = len(step.A.output) + 1\n}\n")
    value = tree.blocks[0].attributes()[0].value
    assert isinstance(value, Expr) and (value.line, value.column) == (2, 7)


def test_triple_quoted_value_in_an_attribute() -> None:
    tree = parse('x {\n  body = """\n    Hello\n    {{ name }}\n  """\n  next = 1\n}\n')
    body, nxt = tree.blocks[0].attributes()
    assert isinstance(body.value, Str) and body.value.value == "Hello\n{{ name }}"
    assert nxt.line == 6


def test_empty_file_and_only_comments() -> None:
    assert parse("", "e.skye").blocks == []
    assert parse("# nothing\n\n", "e.skye").blocks == []


@pytest.mark.parametrize(
    "text,fragment",
    [
        ('flow "a" {', "never closed"),
        ("a = 1", "is an attribute"),
        ('flow "a" { x = [1, }', "expected"),
        ('flow "a" { x = {k 1} }', 'expected "="'),
        ("}", "expected a block"),
    ],
)
def test_syntax_error_messages(text: str, fragment: str) -> None:
    with pytest.raises(SkyeSyntaxError) as info:
        parse(text, "t.skye")
    assert fragment in info.value.diagnostics[0].reason or any(
        fragment in d.reason for d in info.value.diagnostics
    )
