"""The nesting limit: a file nested more than MAX_DEPTH levels is a
diagnostic, never an exception.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from skye.base.dsl import build, check_expression, check_text, to_text
from skye.base.dsl.errors import MAX_DEPTH
from skye.utils.cli import main

MESSAGE = f"nesting is too deep (more than {MAX_DEPTH} levels)"
HUGE = 5000


def flow_maps(n: int) -> str:
    inner = "{a = " * n + "1" + "}" * n
    return (
        f'flow "f" {{\n  step "a" {{\n    run = registry.x\n    input = {inner}\n    next = end\n'
        f"  }}\n}}\n"
    )


def flow_lists(n: int) -> str:
    inner = "[" * n + "1" + "]" * n
    return (
        f'flow "f" {{\n  step "a" {{\n    run = registry.x\n    input = {{ a = {inner} }}\n'
        f"    next = end\n  }}\n}}\n"
    )


def prompt_whens(n: int) -> str:
    return (
        'prompt "p" {\n variables = {x = string}\n message "user" {\n'
        + "when x {\n" * n
        + 'text = "a"\n'
        + "}\n" * n
        + "}}\n"
    )


def prompt_eachs(n: int) -> str:
    return (
        'prompt "p" {\n variables = {xs = list}\n message "user" {\n'
        + "each i in xs {\n" * n
        + 'text = "a"\n'
        + "}\n" * n
        + "}}\n"
    )


def prompt_parens(n: int) -> str:
    cond = "(" * n + "x" + ")" * n
    return (
        f'prompt "p" {{\n variables = {{x = string}}\n message "user" {{\n'
        f' when {cond} {{ text = "a" }}\n}}}}\n'
    )


def plain_blocks(n: int) -> str:
    return 'flow "f" {\n' + "x {\n" * n + "}\n" * n + "}\n"


# the number of levels already open around the nested part
CASES: list[tuple[str, Callable[[int], str], int]] = [
    ("flow maps", flow_maps, 2),
    ("flow lists", flow_lists, 3),
    ("prompt when", prompt_whens, 2),
    ("prompt each", prompt_eachs, 2),
]


@pytest.mark.parametrize(("name", "make", "outer"), CASES, ids=[c[0] for c in CASES])
def test_a_file_at_the_limit_passes(name: str, make: Callable[[int], str], outer: int) -> None:
    text = make(MAX_DEPTH - outer)
    document = build(text)
    assert document.diagnostics == []
    assert to_text(document)  # the emitter survives it too


@pytest.mark.parametrize(("name", "make", "outer"), CASES, ids=[c[0] for c in CASES])
def test_a_file_one_level_over_the_limit_gives_the_message(
    name: str, make: Callable[[int], str], outer: int
) -> None:
    diagnostics = check_text(make(MAX_DEPTH - outer + 1), "deep.skye")
    assert len(diagnostics) == 1
    item = diagnostics[0]
    assert item.reason == MESSAGE
    assert item.file == "deep.skye"
    assert item.line >= 1 and item.column >= 1
    assert "own flow or prompt" in item.fix


@pytest.mark.parametrize(
    "make",
    [flow_maps, flow_lists, prompt_whens, prompt_eachs, plain_blocks, prompt_parens],
    ids=["maps", "lists", "when", "each", "blocks", "parens"],
)
def test_five_thousand_levels_give_the_message_and_no_exception(make: Callable[[int], str]) -> None:
    diagnostics = check_text(make(HUGE), "deep.skye")
    assert [d.reason for d in diagnostics] == [MESSAGE]


def test_the_parentheses_of_an_expression_have_the_same_limit() -> None:
    assert check_expression("(" * MAX_DEPTH + "x" + ")" * MAX_DEPTH) == []
    over = check_expression(
        "(" * (MAX_DEPTH + 1) + "x" + ")" * (MAX_DEPTH + 1), filename="e.skye", line=4, column=7
    )
    assert [d.reason for d in over] == [MESSAGE]
    assert (over[0].file, over[0].line, over[0].column) == ("e.skye", 4, 7)
    assert [d.reason for d in check_expression("[" * HUGE + "x" + "]" * HUGE)] == [MESSAGE]


def test_brackets_inside_a_string_do_not_count() -> None:
    assert check_expression('"' + "(" * 500 + '" == x') == []


def test_a_long_chain_in_an_expression_is_a_diagnostic_not_a_recursion_error() -> None:
    for source in ("not " * HUGE + "x", "x" + ".a" * HUGE, "+".join(["x"] * HUGE)):
        assert [d.reason for d in check_expression(source)] == [MESSAGE]


def test_a_recursion_error_inside_the_builder_becomes_one_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = sys.modules["skye.base.dsl.build"]

    def boom(*_args: object, **_kwargs: object) -> None:
        raise RecursionError

    monkeypatch.setattr(module._Builder, "build", boom)
    diagnostics = check_text('prompt "p" {\n}\n', "x.skye")
    assert [d.reason for d in diagnostics] == [MESSAGE]
    assert diagnostics[0].file == "x.skye"


def test_skye_check_prints_the_message_and_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for make in (flow_maps, prompt_whens, plain_blocks):
        file = tmp_path / "deep.skye"
        file.write_text(make(HUGE), encoding="utf-8")
        assert main(["check", str(file)]) == 1
        out = capsys.readouterr()
        assert MESSAGE in out.out
        assert "Traceback" not in out.out + out.err
