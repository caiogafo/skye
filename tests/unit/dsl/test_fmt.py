"""`skye fmt`: one layout, comments, strings and front matter kept, meaning never changed."""

from __future__ import annotations

from pathlib import Path

import pytest

from skye.base.dsl import TEMPLATES, FormatError, format_text, skeleton
from skye.utils.cli import main

ROOT = Path(__file__).resolve().parents[3]

MESSY = """\
---
title = "Main"
---
/** The router.
    Two lines. **/
router "main" {
      strategy = "round_robin"     # a comment


    route "fast" = [
"openai/gpt-4o-mini",
          ]
}
prompt "p" {
\tmessage "user" {
        text = \"\"\"
           kept    as is
        \"\"\"
   }
}"""

CLEAN = """\
---
title = "Main"
---

/** The router.
    Two lines. **/
router "main" {
  strategy = "round_robin"     # a comment

  route "fast" = [
    "openai/gpt-4o-mini",
  ]
}
prompt "p" {
  message "user" {
    text = \"\"\"
           kept    as is
        \"\"\"
  }
}
"""


def test_the_layout_is_normalised_and_comments_strings_front_matter_kept() -> None:
    assert format_text(MESSY) == CLEAN


def test_formatting_is_idempotent() -> None:
    assert format_text(CLEAN) == CLEAN


def test_one_blank_line_after_the_front_matter() -> None:
    text = '---\ntitle = "a"\n---\n\n\n\nrouter "r" {\n  route "a" = ["x/y"]\n}\n'
    assert format_text(text) == '---\ntitle = "a"\n---\n\nrouter "r" {\n  route "a" = ["x/y"]\n}\n'


def test_a_text_with_mistakes_is_refused() -> None:
    with pytest.raises(FormatError) as info:
        format_text('router "r" {\n  nope = 1\n}\n')
    assert info.value.diagnostics


@pytest.mark.parametrize(
    "path",
    sorted(
        [
            *(ROOT / "src/skye/prompts/templates").glob("*.skye"),
            *(ROOT / "examples").rglob("*.skye"),
        ]
    ),
    ids=lambda p: p.name,
)
def test_the_bundled_files_are_formatted(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert format_text(text, str(path)) == text, f"run: skye fmt {path.relative_to(ROOT)}"


@pytest.mark.parametrize("kind, template", [(k, t) for k, ts in TEMPLATES.items() for t in ts])
def test_skeletons_come_out_formatted(kind: str, template: str) -> None:
    text = skeleton(kind, None, template)
    assert format_text(text) == text


def test_cli_fmt_check_and_write(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "a.skye"
    path.write_text(MESSY, encoding="utf-8")
    assert main(["fmt", "--check", str(path)]) == 1
    assert "would be reformatted" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == MESSY
    assert main(["fmt", str(path)]) == 0
    assert path.read_text(encoding="utf-8") == CLEAN
    assert main(["fmt", "--check", str(path)]) == 0


def test_cli_fmt_reports_mistakes_and_leaves_the_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bad.skye"
    path.write_text('router "r" {\n    nope = 1\n}\n', encoding="utf-8")
    assert main(["fmt", str(path)]) == 1
    assert "nope" in capsys.readouterr().err
    assert path.read_text(encoding="utf-8") == 'router "r" {\n    nope = 1\n}\n'


def test_cli_fmt_searches_the_current_folder_recursively(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "fixtures").mkdir()
    messy = 'router "r" {\n        route "a" = ["x/y"]\n}\n'
    for path in (
        "top.skye",
        "a/b/deep.skye",
        ".hidden/h.skye",
        "node_modules/n.skye",
        "fixtures/f.skye",
    ):
        (tmp_path / path).write_text(messy, encoding="utf-8")
    (tmp_path / "a" / "notes.txt").write_text(messy, encoding="utf-8")
    (tmp_path / ".skyeignore").write_text("# test data\nfixtures/*\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main(["fmt", "--check"]) == 1
    out = capsys.readouterr().out
    assert "top.skye" in out and "deep.skye" in out
    assert "h.skye" not in out and "n.skye" not in out and "f.skye" not in out

    assert main(["fmt"]) == 0
    clean = 'router "r" {\n  route "a" = ["x/y"]\n}\n'
    assert (tmp_path / "a" / "b" / "deep.skye").read_text(encoding="utf-8") == clean
    assert (tmp_path / "fixtures" / "f.skye").read_text(encoding="utf-8") == messy
    assert (tmp_path / "a" / "notes.txt").read_text(encoding="utf-8") == messy
    assert main(["fmt", "--check", "--exclude", "*.skye"]) == 0


def test_cli_fmt_takes_a_folder_argument(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "x.skye").write_text(
        'router "r" {\n route "a" = ["x/y"]\n}\n', encoding="utf-8"
    )
    assert main(["fmt", str(tmp_path)]) == 0
    assert (
        (tmp_path / "sub" / "x.skye")
        .read_text(encoding="utf-8")
        .startswith('router "r" {\n  route')
    )
