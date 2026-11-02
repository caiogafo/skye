"""Reading a YAML file needs the extra `yaml`; JSON needs nothing; `import skye` never imports PyYAML (Requirements 7.12 and 20.1)."""

from __future__ import annotations

import subprocess
import sys

import pytest

from skye.base.config import ConfigLoader
from skye.base.exceptions import MissingExtraError


def test_a_yaml_file_without_pyyaml_raises_missing_extra_naming_yaml(tmp_path, monkeypatch):
    path = tmp_path / "skye.yaml"
    path.write_text("log_level: INFO\n", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "yaml", None)  # `import yaml` now raises ImportError
    with pytest.raises(MissingExtraError) as caught:
        ConfigLoader.load(config_path=path)
    assert "yaml" in str(caught.value)


def test_a_json_file_needs_no_yaml(tmp_path, monkeypatch):
    path = tmp_path / "skye.json"
    path.write_text('{"log_level": "DEBUG"}', encoding="utf-8")
    monkeypatch.setitem(sys.modules, "yaml", None)
    assert ConfigLoader.load(config_path=path).log_level == "DEBUG"


def test_import_skye_does_not_import_pyyaml():
    code = "import sys, skye; import skye.base.config; assert 'yaml' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], check=True)
