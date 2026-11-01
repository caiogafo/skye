"""Import-direction checks over src/nimbus: Layer ceiling, allowed sets, orchestrator isolation.

Pure static analysis with `ast`: no network, no install, same result for the same tree.
Spec: .kiro/specs/structure/design.md (Allowed_Imports_Matrix), Requirements 2.3, 2.5, 2.6,
2.7, 12.3, 12.6, 12.8, 12.9.

Every top-level name below nimbus is mapped to its Component before the matrix is applied.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "nimbus"

LAYERS = {"base": 0, "adapters": 1, "services": 2, "runtime": 3}
COMPONENT_LAYER = {
    "base": "base",
    "models": "adapters",
    "store": "adapters",
    "router": "services",
    "tools": "services",
    "prompts": "services",
    "memory": "services",
    "guard": "services",
    "observe": "services",
    "policy": "runtime",
    "gateway": "runtime",
    "agents": "runtime",
    "teams": "runtime",
    "flows": "runtime",
}

# Maximum set each Component may import (required + optional entries of the design table).
ALLOWED: dict[str, set[str]] = {
    "base": set(),
    "models": {"base"},
    "store": {"base"},
    "router": {"base", "models", "store"},
    "tools": {"base", "prompts"},  # prompts: peer, for the MCP client prompt facet (Req 19.2)
    "prompts": {"base"},
    "memory": {"base", "store"},
    "guard": {"base", "models"},
    "observe": {"base"},
    "policy": {"base", "models"},
    "gateway": {"base", "tools", "models", "policy"},
    "agents": {"base", "models", "tools", "prompts", "memory", "guard", "observe", "policy"},
    "teams": {"base", "prompts", "memory", "guard", "observe", "policy"},
    "flows": {"base", "prompts", "memory", "guard", "observe", "policy"},
}
ORCHESTRATORS = {"agents", "teams", "flows"}

# Top-level modules that are not Components: they belong to the Layer 0 foundation.
# `utils` is a stdlib-only helper package that lives alongside `base` in Layer 0.
NON_COMPONENT_TO_COMPONENT = {
    "utils": "base",
}


def component_of(parts: tuple[str, ...]) -> str | None:
    """Component owning a module path below nimbus (('models', 'base') -> 'models')."""
    if not parts:
        return None
    head = parts[0]
    if head in COMPONENT_LAYER:
        return head
    return NON_COMPONENT_TO_COMPONENT.get(head)


def _module_parts(path: Path) -> tuple[str, ...]:
    rel = path.relative_to(SRC).with_suffix("")
    parts = rel.parts
    return parts[:-1] if parts[-1] == "__init__" else parts


def _imports(path: Path) -> list[tuple[str, ...]]:
    """Every nimbus-internal import in the file, as a path below nimbus."""
    package = _module_parts(path)
    if path.name != "__init__.py":
        package = package[:-1]
    found: list[tuple[str, ...]] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            for alias in node.names:
                p = alias.name.split(".")
                if p[0] == "nimbus":
                    found.append(tuple(p[1:]))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - (node.level - 1)] if node.level > 1 else package
                mod = tuple(node.module.split(".")) if node.module else ()
                target = tuple(base) + mod
            elif node.module and node.module.split(".")[0] == "nimbus":
                target = tuple(node.module.split(".")[1:])
            else:
                continue
            if target:
                found.append(target)
            else:  # `from nimbus import x, y`: each name may be a Component
                found.extend((a.name,) for a in node.names)
    return found


def _label(component: str) -> str:
    return f"{component} (Layer {LAYERS[COMPONENT_LAYER[component]]} {COMPONENT_LAYER[component]})"


def collect_violations() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for path in sorted(SRC.rglob("*.py")):
        parts = _module_parts(path)
        importer = component_of(parts)
        if importer is None:  # nimbus/__init__.py: the public façade, not a Component
            continue
        for target in _imports(path):
            imported = component_of(target)
            if imported is None or imported == importer:
                continue
            where = f"{path.relative_to(SRC.parent.parent)}"
            who = f"{_label(importer)} imports {_label(imported)} [{where}]"
            kinds = []
            if LAYERS[COMPONENT_LAYER[imported]] > LAYERS[COMPONENT_LAYER[importer]]:
                kinds.append("upward import")
            if imported not in ALLOWED[importer]:
                kinds.append("out-of-set import")
            if importer in ORCHESTRATORS and imported in ORCHESTRATORS:
                kinds.append("orchestrator cross-import")
            for kind in kinds:
                out.append(
                    {
                        "message": f"{kind}: {who}",
                        "key_importer": parts[0],
                        "key_imported": target[0],
                    }
                )
    return out


def test_matrix_is_well_formed() -> None:
    assert set(ALLOWED) == set(COMPONENT_LAYER)
    for comp, allowed in ALLOWED.items():
        assert comp not in allowed
        assert allowed <= set(COMPONENT_LAYER)
    assert not (ALLOWED["teams"] | ALLOWED["flows"]) & ({"models"} | ORCHESTRATORS)


def test_every_module_resolves_to_a_component() -> None:
    unmapped = [
        str(p.relative_to(SRC))
        for p in SRC.rglob("*.py")
        if len(_module_parts(p)) > 0 and component_of(_module_parts(p)) is None
    ]
    assert not unmapped, f"Modules under src/nimbus owned by no Component: {unmapped}"


def test_no_import_violates_the_matrix() -> None:
    violations = [v["message"] for v in collect_violations()]
    assert not violations, "Import-matrix violations:\n  " + "\n  ".join(violations)
