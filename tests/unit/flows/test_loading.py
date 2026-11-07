"""The loading API: ``skye.load`` and ``skye.flows.Flow`` (task 8.4 of the uxui spec; Property 16;
decision D61).
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

import skye
from skye.base.dsl import FlowSpec
from skye.base.exceptions import ConfigurationError
from skye.flows import Flow
from skye.utils.skye_files import load

ONE = """
flow "research" {
  context { topic = string }
  step "Plan" {
    run = registry.planner
    input = { topic = context.topic }
    next = end
  }
}
"""
TWO = ONE + ONE.replace("research", "other")
BAD = """flow "f" {
  step "A" {
    run = registry.planner
    next = "Missing"
  }
}
"""


def write(tmp_path: Path, text: str, name: str = "app.skye") -> Path:
    file = tmp_path / name
    file.write_text(text, encoding="utf-8")
    return file


# -- skye.load ----------------------------------------------------------------------------------


def test_load_returns_the_document(tmp_path: Path) -> None:
    document = load(write(tmp_path, ONE))
    assert [f.name for f in document.flows] == ["research"]
    assert document.diagnostics == []


def test_load_is_the_function_of_skye_files() -> None:
    assert getattr(skye, "load") is load


def test_load_with_errors_lists_file_line_column_reason_and_fix(tmp_path: Path) -> None:
    file = write(tmp_path, BAD)
    with pytest.raises(ConfigurationError) as caught:
        load(file)
    assert f"{file}:4:" in caught.value.message
    assert "Missing" in caught.value.message
    assert caught.value.details["diagnostics"]


def test_load_a_missing_file_is_a_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        load(tmp_path / "nope.skye")


def test_load_checks_registry_names_when_given(tmp_path: Path) -> None:
    file = write(tmp_path, ONE)
    assert load(file, registry_names=["planner"]).ok
    with pytest.raises(ConfigurationError) as caught:
        load(file, registry_names=["other"])
    assert "planner" in caught.value.message


# -- Flow ---------------------------------------------------------------------------------------


def test_flow_from_file(tmp_path: Path) -> None:
    flow = Flow.from_file(write(tmp_path, ONE), registry={"planner": object()})
    assert flow.name == "research"
    assert isinstance(flow.spec, FlowSpec)
    assert list(flow.registry) == ["planner"]
    assert flow.check() == []
    assert "research" in repr(flow)


def test_flow_from_text_and_back_to_text() -> None:
    flow = Flow.from_text(ONE, filename="inline.skye")
    again = Flow.from_text(flow.to_text())
    assert again.to_text() == flow.to_text()
    assert getattr(skye, "Flow") is Flow


def test_name_is_optional_with_one_flow_and_required_with_several(tmp_path: Path) -> None:
    file = write(tmp_path, TWO)
    with pytest.raises(ConfigurationError, match="2 flow blocks"):
        Flow.from_file(file)
    assert Flow.from_file(file, name="other").name == "other"
    with pytest.raises(ConfigurationError, match="no flow"):
        Flow.from_file(file, name="absent")
    assert Flow.from_text(ONE, name="research").name == "research"


def test_a_file_with_errors_raises_with_every_diagnostic(tmp_path: Path) -> None:
    file = write(tmp_path, BAD)
    with pytest.raises(ConfigurationError) as caught:
        Flow.from_file(file)
    assert f"{file}:4:" in caught.value.message
    with pytest.raises(ConfigurationError):
        Flow.from_text(BAD)


def test_registry_names_are_checked_against_the_keys(tmp_path: Path) -> None:
    file = write(tmp_path, ONE)
    with pytest.raises(ConfigurationError) as caught:
        Flow.from_file(file, registry={"web": object()})
    assert "planner" in caught.value.message
    with pytest.raises(ConfigurationError):
        Flow.from_text(ONE, registry={})
    assert Flow.from_text(ONE).check() == []  # no registry: names are not checked


def test_check_sees_a_registry_that_changed() -> None:
    registry: dict[str, object] = {"planner": object()}
    flow = Flow.from_text(ONE, registry=registry)
    del registry["planner"]
    assert [d.reason for d in flow.check()]


def test_run_says_the_runtime_is_not_built_yet() -> None:
    flow = Flow.from_text(ONE)
    with pytest.raises(NotImplementedError) as caught:
        flow.run({"topic": "x"})
    assert "not built yet" in str(caught.value)
    assert "3-runtime-flows" in str(caught.value)


# -- imports ------------------------------------------------------------------------------------


def test_flows_imports_no_other_runtime_component() -> None:
    root = Path(skye.__file__).parent / "flows"
    forbidden = {
        "agents",
        "teams",
        "gateway",
        "models",
        "router",
        "tools",
        "memory",
        "guard",
        "observe",
        "store",
        "auth",
        "mcp",
        "prompts",
    }
    for file in root.glob("*.py"):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            modules = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            )
            for module in modules:
                parts = module.split(".")
                assert not (parts[0] == "skye" and len(parts) > 1 and parts[1] in forbidden), (
                    file.name,
                    module,
                )


def test_import_skye_does_not_load_flows_or_the_parser() -> None:
    code = (
        "import sys, skye; print(sorted(m for m in sys.modules "
        "if m in ('skye.flows', 'skye.base.dsl', 'skye.utils.skye_files')))"
    )
    out = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True
    ).stdout
    assert out.strip() == "[]"
    code2 = (
        "import sys, skye; skye.Flow; skye.load; "
        "print('skye.flows' in sys.modules, 'skye.models' in sys.modules, "
        "'skye.agents' in sys.modules)"
    )
    out2 = subprocess.run(
        [sys.executable, "-I", "-c", code2], capture_output=True, text=True, check=True
    ).stdout
    assert out2.strip() == "True False False"
