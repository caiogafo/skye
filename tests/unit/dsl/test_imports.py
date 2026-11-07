"""``base/dsl`` is standard library only, does no file I/O, and ``import skye`` does not load it."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import skye.base.dsl as package

DSL = Path(package.__file__).parent

SNIPPET = """
import sys
import skye
loaded = set(sys.modules)
assert not any(m.startswith("skye.base.dsl") for m in loaded), "import skye loads the dsl"
import skye.base.dsl
new = {m.split(".")[0] for m in set(sys.modules) - loaded}
foreign = sorted(
    n for n in new if n not in sys.stdlib_module_names and n != "skye" and not n.startswith("_")
)
assert not foreign, foreign
"""


def test_import_skye_stays_clean_and_dsl_adds_only_stdlib() -> None:
    result = subprocess.run(
        [sys.executable, "-c", SNIPPET], capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, result.stderr


def test_dsl_modules_import_only_stdlib_and_base() -> None:
    for path in DSL.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module]
            for name in names:
                top = name.split(".")[0]
                assert top in sys.stdlib_module_names or top in ("skye", "__future__"), (path, name)
                if top == "skye":
                    assert name.startswith(("skye.base", "skye.base.dsl")), (path, name)


def test_dsl_does_no_file_io() -> None:
    forbidden = {"open", "Path", "pathlib", "os", "shutil", "tempfile", "socket", "subprocess"}
    for path in DSL.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "open", path
            if isinstance(node, ast.Import):
                assert not forbidden & {a.name for a in node.names}, path
            if isinstance(node, ast.ImportFrom):
                assert node.module not in forbidden, path
