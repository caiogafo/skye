"""Helpers that measure what Skye costs to install and to load.

Used by the budget tests. Nothing here imports skye in the current process.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import tomllib  # standard library since Python 3.11, the minimum (D49)

ROOT = Path(__file__).resolve().parents[2]


def load_budgets() -> dict:
    with open(ROOT / "budgets.toml", "rb") as fh:
        return tomllib.load(fh)


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def pyproject() -> dict:
    with open(ROOT / "pyproject.toml", "rb") as fh:
        return tomllib.load(fh)


def requirement_name(requirement: str) -> str:
    return normalize(re.split(r"[\s\[<>=!~;]", requirement.strip(), maxsplit=1)[0])


def _size_bytes(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def site_packages(python: Path) -> Path:
    out = subprocess.check_output(
        [str(python), "-c", "import site; print(site.getsitepackages()[0])"], text=True
    )
    return Path(out.strip())


def installed_distributions(site: Path) -> list[str]:
    return sorted(
        normalize(re.sub(r"-[0-9].*\.dist-info$", "", p.name))
        for p in site.iterdir()
        if p.name.endswith(".dist-info")
    )


def compiled_distributions(site: Path) -> list[str]:
    """Installed distributions that are not pure Python (their wheel is platform specific)."""
    out = []
    for dist in site.glob("*.dist-info"):
        wheel = dist / "WHEEL"
        if not wheel.exists():
            continue
        text = wheel.read_text(errors="ignore")
        if not ("Root-Is-Purelib: true" in text and "-none-any" in text):
            out.append(normalize(re.sub(r"-[0-9].*\.dist-info$", "", dist.name)))
    return sorted(out)


def installed_mb(site: Path, preinstalled: list[str]) -> float:
    """Size of site-packages without the libraries that Lambda already ships."""
    skip = {normalize(n).replace("-", "_") for n in preinstalled}
    total = 0
    for entry in site.iterdir():
        stem = normalize(entry.name.split(".")[0]).replace("-", "_")
        stem = re.sub(r"_[0-9].*$", "", stem)
        if stem in skip:
            continue
        total += _size_bytes(entry) if entry.is_dir() else entry.stat().st_size
    return total / 1e6


def build_wheel(dest: Path) -> Path:
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dest)],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return next(dest.glob("skyeai-*.whl"))


def make_env(wheel: Path, extra: str | None, workdir: Path) -> Path:
    """Create a clean venv with the wheel (and one extra). Returns its python."""
    venv = workdir / (f"env-{extra}" if extra else "env-core")
    py = f"{sys.version_info.major}.{sys.version_info.minor}"
    python = venv / ("Scripts" if os.name == "nt" else "bin") / "python"
    if python.exists():
        return python  # already built in this run
    subprocess.run(["uv", "venv", "--python", py, "-q", str(venv)], check=True, capture_output=True)
    spec = f"skyeai[{extra}] @ {wheel.as_uri()}" if extra else f"skyeai @ {wheel.as_uri()}"
    subprocess.run(
        ["uv", "pip", "install", "-q", "--python", str(python), spec],
        check=True,
        capture_output=True,
    )
    return python


LOAD_PROBE = """
import json, resource, sys, time
before = set(sys.modules)
r0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
t = time.perf_counter()
import skye
elapsed = time.perf_counter() - t
r1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
scale = 1024 * 1024 if sys.platform == "darwin" else 1024
new = set(sys.modules) - before
print(json.dumps({
    "modules": len(new),
    "ms": elapsed * 1000,
    "rss_mb": (r1 - r0) / scale,
    # only what `import skye` itself loaded: a .pth file of an installed SDK (e.g. the
    # google-cloud-aiplatform nspkg.pth) pre-imports `google` at interpreter start-up
    "loaded": sorted({m.split(".")[0] for m in new}),
}))
"""


def load_metrics(python: str | Path, runs: int = 5) -> dict:
    """Best of several fresh interpreters: import skye and report cost."""
    results = [
        json.loads(
            subprocess.check_output([str(python), "-c", LOAD_PROBE], text=True, cwd=tempfile.gettempdir())
        )
        for _ in range(runs)
    ]
    best = min(results, key=lambda r: r["ms"])
    best["modules"] = max(r["modules"] for r in results)
    best["rss_mb"] = max(r["rss_mb"] for r in results)
    return best


def importable(python: str | Path, module: str) -> bool:
    proc = subprocess.run(
        [str(python), "-c", f"import {module}"], capture_output=True, cwd=tempfile.gettempdir()
    )
    return proc.returncode == 0


def skye_subpackages() -> list[str]:
    src = ROOT / "src" / "skye"
    return sorted(
        f"skye.{p.name}" for p in src.iterdir() if p.is_dir() and (p / "__init__.py").exists()
    )


def module_level_third_party_imports(lambda_libs: list[str]) -> dict[str, list[str]]:
    """Third-party packages imported when a module loads, mapped to the files that do it.

    Counts imports at module level, including inside top-level try/if blocks, but not
    inside functions or `if TYPE_CHECKING:` blocks (those are lazy or type-only).
    """
    import ast

    stdlib = set(sys.stdlib_module_names) | {"skye"}
    allowed = {normalize(n).replace("-", "_") for n in lambda_libs} | {"dateutil"}
    found: dict[str, set[str]] = {}

    def tops(node: ast.AST) -> list[str]:
        if isinstance(node, ast.Import):
            return [a.name.split(".")[0] for a in node.names]
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            return [node.module.split(".")[0]]
        return []

    def is_type_checking(node: ast.AST) -> bool:
        test = getattr(node, "test", None)
        return isinstance(test, ast.Name) and test.id == "TYPE_CHECKING" or (
            isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
        )

    def walk(body: list[ast.stmt], path: str) -> None:
        for node in body:
            for top in tops(node):
                if top not in stdlib and top not in allowed:
                    found.setdefault(top, set()).add(path)
            if isinstance(node, ast.If) and not is_type_checking(node):
                walk(node.body, path)
                walk(node.orelse, path)
            elif isinstance(node, ast.Try):
                for block in (node.body, node.orelse, node.finalbody, *[h.body for h in node.handlers]):
                    walk(block, path)

    src = ROOT / "src"
    for file in sorted((src / "skye").rglob("*.py")):
        walk(ast.parse(file.read_text(encoding="utf-8")).body, str(file.relative_to(src)))
    return {k: sorted(v) for k, v in sorted(found.items())}


def report(line: str) -> None:
    """Append a markdown line to the file named by SKYE_BUDGET_REPORT (CI summary)."""
    target = os.environ.get("SKYE_BUDGET_REPORT")
    if target:
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def cleanup(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
