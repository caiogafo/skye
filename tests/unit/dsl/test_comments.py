"""Comments in `.skye` files: `#` to the end of the line, `/* ... */` and `/** ... **/` over lines."""

from __future__ import annotations

from skye.base.dsl import build, check_text, tokenize

ROUTER = """\
/**
 * The main router.
 * Owner: platform team
 **/
router "main" {   # trailing line comment
  /* one route */ route "fast" = ["openai/gpt-4o-mini"]
  route "smart" = [
    "anthropic/claude-sonnet",   /* inside a list */
  ]
}
"""


def test_block_comments_line_comments_and_doc_comments_are_dropped() -> None:
    assert not check_text(ROUTER)
    routes = [route.alias for route in build(ROUTER).router("main").routes]
    assert routes == ["fast", "smart"]


def test_line_numbers_after_a_multi_line_comment_stay_right() -> None:
    text = '/*\n\n\n*/\nrouter "r" {\n  route "a" = ["x/y"]\n  nope = 1\n}\n'
    (problem,) = check_text(text)
    assert (problem.line, problem.column) == (7, 3)


def test_a_comment_inside_an_expression_is_a_space() -> None:
    text = """\
flow "f" {
  context { n = number(0) }
  step "A" { run = registry.x, next = "B" }
  choice "B" {
    when context.n /* the count */ >= 3 { next = end }
    else { next = end }
  }
}
"""
    assert not check_text(text, registry_names=["x"])
    choice = build(text, registry_names=["x"]).flow("f").node("B")
    assert choice.branches[0].when.text == "context.n >= 3"


def test_comment_markers_inside_strings_are_text() -> None:
    text = 'router "r" {\n  route "a" = ["x/y"]\n}\nprompt "p" {\n  message "user" { text = "a /* b */ c # d" }\n}\n'
    assert not check_text(text)
    part = build(text).prompt("p").parts[0].children[0]
    assert part.text == "a /* b */ c # d"


def test_an_unterminated_block_comment_is_reported_where_it_starts() -> None:
    _, errors = tokenize('router "r" {\n  /* open\n}\n', "f.skye")
    assert [(e.line, e.column, e.reason) for e in errors] == [(2, 3, 'unterminated "/*" comment')]


def test_floor_division_is_not_a_comment() -> None:
    text = """\
flow "f" {
  context { n = number(0) }
  step "A" { run = registry.x, next = "B" }
  choice "B" {
    when context.n // 2 >= 1 { next = end }
    else { next = end }
  }
}
"""
    assert not check_text(text, registry_names=["x"])
