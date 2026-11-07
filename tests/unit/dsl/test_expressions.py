"""The expression checker and evaluator: whitelist of nodes and functions, no eval, no exec."""

from __future__ import annotations

import pytest

from skye.base.dsl import (
    ALLOWED_FUNCTIONS,
    Expression,
    SkyeExpressionError,
    check_expression,
    evaluate,
)
from skye.base.dsl.expressions import references


@pytest.mark.parametrize(
    "text",
    [
        "context.quality >= 0.8",
        "context.a > 1 and context.b < 2 or not context.c",
        "len(step.A.output.items) + 1",
        "min(1, 2) + max(3, 4) - abs(-1) * round(2.5) / 2 // 1 % 3",
        'str(1) + "x"',
        "int('3') + float('1.5')",
        "context.x in [1, 2, 3]",
        "context.x not in (1, 2)",
        "{'a': 1}['a']",
        "context.items[0]",
        "context.items[1:2]",
        "1 if context.ok else 2",
        "context.x is None",
        "[step.A.output, step.B.output]",
    ],
)
def test_allowed_expressions(text: str) -> None:
    assert check_expression(text) == []


@pytest.mark.parametrize(
    "text,fragment",
    [
        ('open("f")', 'call "open(...)" is not allowed'),
        ('__import__("os")', 'call "__import__(...)" is not allowed'),
        ('eval("1")', 'call "eval(...)" is not allowed'),
        ('exec("1")', 'call "exec(...)" is not allowed'),
        ("context.x.upper()", 'call "context.x.upper(...)" is not allowed'),
        ("print(1)", "is not allowed"),
        ("len.__call__([])", "is not allowed"),
        ("context.__class__", 'attribute "__class__" is not allowed'),
        ("().__class__.__bases__", 'attribute "__class__" is not allowed'),
        ("context._private", 'attribute "_private" is not allowed'),
        ("__builtins__", 'name "__builtins__" is not allowed'),
        ("lambda: 1", "a lambda is not allowed"),
        ("[x for x in context.a]", "a comprehension is not allowed"),
        ('f"{context.a}"', "an f-string is not allowed"),
        ("(y := 1)", "walrus"),
        ("2 ** 10", 'operator "Pow" is not allowed'),
        ("~1", 'operator "Invert" is not allowed'),
        ("1 << 2", 'operator "LShift" is not allowed'),
        ("len(*a)", "unpacking"),
        ("{**a}", "unpacking"),
        ("b'x'", "is not allowed"),
        ("await x", "is not allowed"),
        ("1 +", "is not a valid expression"),
    ],
)
def test_rejected_expressions(text: str, fragment: str) -> None:
    problems = check_expression(text, filename="f.skye", line=3, column=5)
    assert problems, text
    assert any(fragment in p.message for p in problems), [p.message for p in problems]
    assert all(p.file == "f.skye" and p.line >= 3 for p in problems)


def test_call_error_lists_the_allowed_functions() -> None:
    (problem,) = check_expression('open("f")', line=31, column=12)
    assert (problem.line, problem.column) == (31, 12)
    assert problem.message == (
        'call "open(...)" is not allowed in an expression. '
        "Allowed: len, min, max, abs, round, str, int, float"
    )
    assert ALLOWED_FUNCTIONS == ("len", "min", "max", "abs", "round", "str", "int", "float")


def test_position_inside_a_longer_expression() -> None:
    (problem,) = check_expression("1 + open('x')", line=2, column=10)
    assert (problem.line, problem.column) == (2, 14)


def test_references_skip_called_function_names() -> None:
    chains = [c for c, _ in references("len(step.A.output.items) + context.n + item")]
    assert chains == [("step", "A", "output", "items"), ("context", "n"), ("item",)]


def test_evaluate() -> None:
    scope = {
        "context": {"quality": 0.9, "n": 2, "tags": ["a", "b"]},
        "step": {"A": {"output": {"items": [1, 2, 3], "score": 7}}},
    }
    assert evaluate("context.quality >= 0.8", scope) is True
    assert evaluate("len(step.A.output.items) + context.n", scope) == 5
    assert evaluate(Expression(text="step.A.output.score * 2"), scope) == 14
    assert evaluate("'a' in context.tags and not False", scope) is True
    assert evaluate("1 if context.n > 5 else 2", scope) == 2
    assert evaluate("max(context.n, 10)", scope) == 10
    assert evaluate("step.A.output.items[1:]", scope) == [2, 3]
    assert evaluate("1 < context.n < 3", scope) is True
    assert evaluate("{'k': context.n}", scope) == {"k": 2}


@pytest.mark.parametrize(
    "text",
    ["missing + 1", "context.nope", "1 / 0", "open('x')", "'a' * 100000", "context.__class__"],
)
def test_evaluate_refuses_and_reports(text: str) -> None:
    with pytest.raises(SkyeExpressionError):
        evaluate(text, {"context": {"n": 1}})


def test_evaluate_reads_public_attributes_of_objects_only() -> None:
    class Box:
        value = 3
        _secret = 4

    assert evaluate("box.value", {"box": Box()}) == 3
    with pytest.raises(SkyeExpressionError):
        evaluate("box._secret", {"box": Box()})


def test_module_does_not_use_eval_or_exec() -> None:
    import ast
    from pathlib import Path

    import skye.base.dsl as package

    for path in Path(package.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "compile", "__import__"}, path
