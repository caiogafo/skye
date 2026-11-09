"""``base`` does no file I/O except ``base/http.py`` (Requirement 3.2, decision D91).

The configuration loader and the ``.skye`` parser take text; the files are opened in ``skye.utils``
(``load_config``, ``load_document``). The test reads the source of every module of ``src/skye/base``
and fails on a call that opens, reads, writes, lists or removes a file.
"""

from __future__ import annotations

import ast
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / "src" / "skye" / "base"
#: The one module of ``base`` allowed to do I/O: the standard-library HTTP transport (decision D32).
ALLOWED = {BASE / "http.py"}
#: Functions that touch the file system when called by name.
FORBIDDEN_NAMES = {"open"}
#: Methods that touch the file system (``Path`` and ``os``), whatever the object.
FORBIDDEN_METHODS = {
    "read_text",
    "read_bytes",
    "write_text",
    "write_bytes",
    "open",
    "exists",
    "is_file",
    "is_dir",
    "iterdir",
    "glob",
    "rglob",
    "unlink",
    "mkdir",
    "rmdir",
    "touch",
    "listdir",
    "remove",
    "scandir",
    "walk",
    "stat",
}


def _file_io_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in FORBIDDEN_NAMES:
            found.append(f"{path.relative_to(BASE.parent)}:{node.lineno} {func.id}()")
        elif isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_METHODS:
            found.append(f"{path.relative_to(BASE.parent)}:{node.lineno} .{func.attr}()")
    return found


def test_base_does_no_file_io_except_http():
    """No module of ``base`` but ``http.py`` opens, reads, writes or lists a file (R3.2, D91)."""
    offenders = [
        call
        for path in sorted(BASE.rglob("*.py"))
        if path not in ALLOWED
        for call in _file_io_calls(path)
    ]
    assert offenders == [], (
        "base does no file I/O (Requirement 3.2, D91); take text and read the file in skye.utils: "
        + "; ".join(offenders)
    )


def test_the_check_sees_a_file_read(tmp_path):
    """The check is not blind: a module that opens a file is reported."""
    module = tmp_path / "reader.py"
    module.write_text(
        "def f(p):\n    with open(p) as fh:\n        return p.read_text()\n", encoding="utf-8"
    )
    global BASE
    saved = BASE
    BASE = tmp_path
    try:
        assert len(_file_io_calls(module)) == 2
    finally:
        BASE = saved
