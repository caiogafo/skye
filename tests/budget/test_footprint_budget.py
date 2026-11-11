"""What Skye weighs when it is installed.

Builds the wheel, installs it in clean virtual environments (core alone, then one extra
at a time) and compares package count and size with budgets.toml. Needs `uv` and network
access, so it is marked `budget` and runs in the "budgets" workflow, or locally with:

    uv run pytest tests/budget -m budget
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from tests.budget import measure
from tests.budget.measure import load_budgets, report

pytestmark = pytest.mark.budget

BUDGETS = load_budgets()
EXTRAS = sorted(e for e in BUDGETS["extras"])


@pytest.fixture(scope="session")
def workdir():
    if shutil.which("uv") is None:
        pytest.skip("uv is required for footprint budgets")
    path = Path(tempfile.mkdtemp(prefix="skye-budget-"))
    yield path
    measure.cleanup(path)


@pytest.fixture(scope="session")
def wheel(workdir: Path) -> Path:
    return measure.build_wheel(workdir)


@pytest.fixture(scope="session")
def core_env(wheel: Path, workdir: Path):
    python = measure.make_env(wheel, None, workdir)
    site = measure.site_packages(python)
    pre = BUDGETS["lambda"]["preinstalled"]
    return python, site, measure.installed_mb(site, pre)


def test_core_footprint(core_env) -> None:
    _python, site, size = core_env
    dists = measure.installed_distributions(site)
    budget = BUDGETS["core"]
    report(f"| core | {len(dists)} packages (max {budget['max_distributions']}) | {size:.1f} MB (max {budget['max_installed_mb']}) | |")
    assert len(dists) <= budget["max_distributions"], f"core installs {len(dists)} packages: {dists}"
    assert size <= budget["max_installed_mb"], f"core is {size:.1f} MB, limit {budget['max_installed_mb']} MB"


def test_core_has_only_the_listed_compiled_distributions(core_env) -> None:
    _python, site, _size = core_env
    found = measure.compiled_distributions(site)
    known = sorted(BUDGETS["core"]["known_compiled"])
    assert found == known, (
        f"Compiled distributions in the core install: {found}, listed: {known}. A compiled wheel "
        "needs a container build for the right architecture and Python. Do not add one; when one "
        "is removed, delete it from known_compiled in budgets.toml."
    )


def test_core_modules_import_without_extras(core_env) -> None:
    """Every subpackage must import on a core-only install, except the listed ones."""
    python, _site, _size = core_env
    known = set(BUDGETS["core"]["known_import_failures"])
    broken, fixed = [], []
    for module in measure.skye_subpackages():
        ok = measure.importable(python, module)
        if not ok and module not in known:
            broken.append(module)
        if ok and module in known:
            fixed.append(module)
    assert not broken, (
        f"These modules fail to import on a core-only install: {broken}. Move the import of the "
        "optional library behind LazyImporter, or declare the dependency."
    )
    assert not fixed, f"{fixed} now import fine. Remove them from known_import_failures in budgets.toml."


def test_core_load_in_clean_environment(core_env) -> None:
    python, _site, _size = core_env
    data = measure.load_metrics(python)
    budget = BUDGETS["load"]
    assert not (set(budget["forbidden_at_import"]) & set(data["loaded"]))
    assert data["modules"] <= budget["max_modules_loaded"], f"`import skye` loads {data['modules']} modules"
    assert data["ms"] <= budget["max_import_ms"], f"`import skye` takes {data['ms']:.0f} ms"
    assert data["rss_mb"] <= budget["max_rss_delta_mb"], f"`import skye` adds {data['rss_mb']:.0f} MB"
    report(
        f"| import skye (clean core) | {data['modules']} modules (max {budget['max_modules_loaded']}) | "
        f"{data['ms']:.0f} ms (max {budget['max_import_ms']}) | {data['rss_mb']:.0f} MB RSS (max {budget['max_rss_delta_mb']}) |"
    )


@pytest.mark.parametrize("extra", EXTRAS)
def test_extra_footprint(extra: str, wheel: Path, workdir: Path, core_env) -> None:
    _python, _site, core_mb = core_env
    python = measure.make_env(wheel, extra, workdir)
    site = measure.site_packages(python)
    size = measure.installed_mb(site, BUDGETS["lambda"]["preinstalled"])
    over = size - core_mb
    budget = BUDGETS["extras"][extra]
    core_compiled = set(BUDGETS["core"]["known_compiled"])
    added_compiled = sorted(set(measure.compiled_distributions(site)) - core_compiled)
    report(
        f"| extra `{extra}` | {len(measure.installed_distributions(site))} packages installed | "
        f"+{over:.1f} MB (max {budget['max_over_core_mb']}, target {budget['target_over_core_mb']}) | "
        f"{len(added_compiled)} compiled (max {budget['max_compiled_over_core']}) |"
    )
    assert len(added_compiled) <= budget["max_compiled_over_core"], (
        f"extra '{extra}' adds compiled distributions {added_compiled} (limit {budget['max_compiled_over_core']})"
    )
    assert over <= budget["max_over_core_mb"], (
        f"extra '{extra}' adds {over:.1f} MB over the core, limit {budget['max_over_core_mb']} MB"
    )


def test_serverless_profile_fits_lambda(wheel: Path, workdir: Path) -> None:
    lam = BUDGETS["lambda"]
    python = measure.make_env(wheel, lam["profile_extra"], workdir)
    size = measure.installed_mb(measure.site_packages(python), lam["preinstalled"])
    report(f"| serverless profile (core + {lam['profile_extra']}) | | {size:.1f} MB (max {lam['max_profile_mb']}; Lambda limit {lam['unzipped_limit_mb']}) | |")
    assert size <= lam["max_profile_mb"], f"serverless profile is {size:.1f} MB, limit {lam['max_profile_mb']} MB"
    assert lam["max_profile_mb"] < lam["unzipped_limit_mb"]


def test_lambda_zip_fits(wheel: Path, workdir: Path) -> None:
    """The zip of examples/serverless/lambda_zip, built as its build.sh does.

    The wheel and handler.py, nothing else.
    """
    import subprocess
    import zipfile

    lam = BUDGETS["lambda"]
    target = workdir / "lambda-zip"
    shutil.rmtree(target, ignore_errors=True)
    subprocess.run(
        ["uv", "pip", "install", "--quiet", "--target", str(target), str(wheel)],
        check=True,
        capture_output=True,
    )
    for junk in [*target.glob("*.dist-info"), *target.rglob("__pycache__")]:
        shutil.rmtree(junk, ignore_errors=True)
    example = measure.ROOT / "examples" / "serverless" / "lambda_zip"
    shutil.copy(example / "handler.py", target / "handler.py")
    archive = workdir / "function.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(p for p in target.rglob("*") if p.is_file()):
            zf.write(path, path.relative_to(target))
    size = archive.stat().st_size / 1e6
    limits = f"max {lam['max_zip_mb']}; AWS limit {lam['zipped_limit_mb']}"
    report(f"| Lambda zip (lambda_zip example) | | {size:.2f} MB ({limits}) | |")
    assert size <= lam["max_zip_mb"], f"the Lambda zip is {size:.2f} MB ({limits})"
    assert lam["max_zip_mb"] < lam["zipped_limit_mb"]
