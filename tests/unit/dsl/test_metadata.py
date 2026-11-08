"""Front matter of `.skye` files: `---` ... `---` at the top, TOML, kept in `Document.metadata`."""

from __future__ import annotations

from skye.base.dsl import build, check_text, format_metadata, parse, split_metadata, to_text

TEXT = """\
---
title       = "Support router"
version     = "1.2"
tags        = ["support", "prod"]
reviewed    = true

[owner]
team = "platform"
---
router "support" {
  route "fast" = ["openai/gpt-4o-mini"]
}
"""


def test_the_metadata_is_read_into_the_document() -> None:
    document = build(TEXT)
    assert document.ok
    assert document.metadata == {
        "title": "Support router",
        "version": "1.2",
        "tags": ["support", "prod"],
        "reviewed": True,
        "owner": {"team": "platform"},
    }
    assert parse(TEXT).metadata == document.metadata


def test_line_numbers_after_the_front_matter_do_not_change() -> None:
    (problem,) = check_text(TEXT.replace('  route "fast"', '  nope = 1\n  route "fast"'))
    assert (problem.line, problem.column) == (11, 3)


def test_a_file_without_front_matter_has_empty_metadata() -> None:
    assert build('router "r" {\n  route "a" = ["x/y"]\n}\n').metadata == {}


def test_to_text_writes_the_front_matter_back() -> None:
    document = build(TEXT)
    again = build(to_text(document))
    assert again.metadata == document.metadata
    assert to_text(document).startswith('---\ntitle = "Support router"\n')


def test_yaml_is_refused_with_the_fix() -> None:
    (problem,) = check_text('---\ntitle: Main\n---\nrouter "r" {\n  route "a" = ["x/y"]\n}\n')
    assert (problem.line, problem.reason) == (2, "front matter is TOML, not YAML")
    assert "title = " in problem.fix


def test_bad_toml_is_reported_on_its_line() -> None:
    (problem,) = check_text('---\ntitle = "a"\nversion = \n---\nrouter "r" {\n  route "a" = ["x/y"]\n}\n')
    assert problem.line == 3
    assert problem.reason.startswith("front matter:")


def test_an_unclosed_front_matter_is_reported() -> None:
    problems = check_text('---\ntitle = "a"\nrouter "r" {\n  route "a" = ["x/y"]\n}\n')
    assert any("never closed" in p.reason for p in problems)


def test_dashes_later_in_the_file_are_not_front_matter() -> None:
    metadata, text, errors = split_metadata('router "r" {\n  route "a" = ["x/y"]\n}\n---\n', "f")
    assert (metadata, errors) == ({}, [])
    assert text.endswith("---\n")


def test_format_metadata_round_trips_through_split() -> None:
    metadata = {"title": 'He said "hi"', "n": 3, "ratio": 0.5, "ok": False, "tags": ["a", "b"]}
    text = format_metadata(metadata) + 'router "r" {\n  route "a" = ["x/y"]\n}\n'
    assert split_metadata(text, "f")[0] == metadata
    assert format_metadata({}) == ""


def test_the_prompt_loader_registers_the_front_matter_version(tmp_path) -> None:  # noqa: ANN001
    from skye.prompts import BasePromptBuilder
    from skye.prompts.loaders import load_default_templates

    (tmp_path / "greet.skye").write_text(
        '---\nversion = "2.1"\n---\nprompt "greet" {\n'
        '  variables = { name = string }\n  message "user" { text = "Hi {{ name }}" }\n}\n'
    )
    builder = BasePromptBuilder()
    load_default_templates(builder, tmp_path)
    assert "Hi {{ name }}" in builder.get_template("greet", "2.1")
    assert builder.render("greet", {"name": "Ada"})[0].content == "Hi Ada"
