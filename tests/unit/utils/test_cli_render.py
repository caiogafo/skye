"""``skye render``: a flow or a router of a ``.skye`` file as a Mermaid diagram (R54.21, D88)."""

from __future__ import annotations

from pathlib import Path

import pytest

from skye.utils.cli import main

TWO = """\
flow "one" { step "a" { run = registry.a, next = end } }
router "r" { route "fast" = ["openai/gpt-4o-mini"] }
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "app.skye"
    path.write_text(text, encoding="utf-8")
    return path


def test_writes_file_mmd_next_to_the_file(tmp_path: Path) -> None:
    path = _write(tmp_path, 'flow "one" { step "a" { run = registry.a, next = end } }\n')
    assert main(["render", str(path)]) == 0
    assert (tmp_path / "app.mmd").read_text(encoding="utf-8").startswith("flowchart TD\n")


def test_stdout_prints_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _write(tmp_path, TWO)
    assert main(["render", str(path), "--name", "r", "--stdout"]) == 0
    assert capsys.readouterr().out.startswith("flowchart LR\n")
    assert not (tmp_path / "app.mmd").exists()


def test_several_blocks_need_a_name_or_fence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _write(tmp_path, TWO)
    assert main(["render", str(path), "--stdout"]) == 2
    assert "pass --name" in capsys.readouterr().err
    assert main(["render", str(path), "--stdout", "--fence"]) == 0
    out = capsys.readouterr().out
    assert out.count("```mermaid\n") == 2 and out.count("\n```\n") == 2


def test_fence_writes_markdown_and_output_and_direction(tmp_path: Path) -> None:
    path = _write(tmp_path, TWO)
    assert main(["render", str(path), "--fence"]) == 0
    assert (tmp_path / "app.mmd.md").read_text(encoding="utf-8").startswith("```mermaid\n")
    out = tmp_path / "one.mmd"
    assert main(["render", str(path), "--name", "one", "-o", str(out), "--direction", "LR"]) == 0
    assert out.read_text(encoding="utf-8").startswith("flowchart LR\n")


def test_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = _write(tmp_path, 'flow "one" { step "a" { run = registry.a } }\n')
    assert main(["render", str(bad), "--stdout"]) == 1
    assert "app.skye:" in capsys.readouterr().out
    prompt = _write(tmp_path, 'prompt "p" { message "user" { text = "hi" } }\n')
    assert main(["render", str(prompt), "--stdout"]) == 2
    assert "no flow or router" in capsys.readouterr().err
    assert main(["render", str(tmp_path / "missing.skye")]) == 2
    path = _write(tmp_path, TWO)
    assert main(["render", str(path), "--name", "nope"]) == 2
