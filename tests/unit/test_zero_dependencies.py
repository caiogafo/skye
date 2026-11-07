"""The core imports no third-party package (decision D49)."""

import subprocess
import sys


def test_importing_the_core_loads_neither_pydantic_nor_tenacity():
    code = (
        "import sys, skye, skye.router, skye.tools, skye.memory, skye.utils.validation, "
        "skye.models; "
        "sys.exit(1 if ('pydantic' in sys.modules or 'tenacity' in sys.modules) else 0)"
    )
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0


def test_model_target_keeps_extra_fields_and_substitutes_variables(monkeypatch):
    from skye.router.config_models import ModelTarget

    monkeypatch.setenv("SKYE_TEST_KEY", "secret")
    target = ModelTarget(model="m", provider="p", api_key="${SKYE_TEST_KEY}", custom_flag=7)
    assert target.api_key == "secret"
    assert target.custom_flag == 7
    assert target.to_dict()["custom_flag"] == 7
    assert ModelTarget.from_dict({"model": "m", "provider": "p", "x": 1}).x == 1


def test_memory_entry_defaults():
    from skye.memory import MemoryEntry

    entry = MemoryEntry(content="c", memory_type="persona")
    assert entry.id and entry.metadata == {} and entry.created_at.tzinfo is not None
