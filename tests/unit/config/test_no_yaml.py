"""The library reads no YAML: no module imports a YAML library and a YAML file is rejected plainly
(Requirement 54.12, D62).
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from skye.base.exceptions import ConfigurationError
from skye.utils.config_files import load_config

SRC = Path(__file__).resolve().parents[3] / "src" / "skye"


def _imports_yaml(path: Path) -> bool:
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] == "yaml" for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "yaml":
            return True
    return False


def test_no_module_of_the_library_imports_a_yaml_library():
    offenders = [str(p.relative_to(SRC)) for p in sorted(SRC.rglob("*.py")) if _imports_yaml(p)]
    assert not offenders, f"modules that import yaml: {offenders}"


def test_import_skye_does_not_import_pyyaml():
    code = "import sys, skye, skye.router, skye.base.config; assert 'yaml' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], check=True)


@pytest.mark.parametrize("name", ["skye.yaml", "skye.yml", "SKYE.YAML"])
def test_a_yaml_file_is_rejected_with_the_supported_formats(tmp_path, name):
    path = tmp_path / name
    path.write_text("log_level: INFO\n", encoding="utf-8")
    with pytest.raises(ConfigurationError) as caught:
        load_config(path)
    message = str(caught.value)
    assert ".skye" in message and "JSON" in message


def test_a_json_file_still_loads(tmp_path):
    path = tmp_path / "skye.json"
    path.write_text('{"log_level": "DEBUG"}', encoding="utf-8")
    assert load_config(path).log_level == "DEBUG"
