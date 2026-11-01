"""Fast checks on how pyproject.toml declares dependencies. No network, no install."""

from __future__ import annotations

from tests.budget.measure import load_budgets, normalize, pyproject, requirement_name


def _core_dependencies() -> set[str]:
    return {requirement_name(r) for r in pyproject()["project"]["dependencies"]}


def test_core_dependencies_are_the_allowed_ones() -> None:
    allowed = {normalize(n) for n in load_budgets()["core"]["allowed_dependencies"]}
    assert _core_dependencies() == allowed, (
        "The core dependency list changed. Every core dependency is installed by everyone and "
        "loaded on every cold start. If the change is intended, update budgets.toml in the same "
        "pull request and say why."
    )


def _extra_requirements(name: str) -> set[str]:
    reqs = {requirement_name(r) for r in pyproject()["project"]["optional-dependencies"][name]}
    return reqs - _core_dependencies()


def test_every_extra_is_budgeted_empty_or_a_bundle() -> None:
    budgets = load_budgets()
    extras = set(pyproject()["project"]["optional-dependencies"])
    budgeted = set(budgets["extras"]) - {"policy"}
    budgeted.discard("extras_policy")
    policy = budgets["extras_policy"]
    known_empty, bundles = set(policy["known_empty"]), set(policy["bundles"])

    missing = extras - budgeted - known_empty - bundles
    assert not missing, f"Extras with no budget in budgets.toml: {sorted(missing)}"

    stale = (budgeted | known_empty | bundles) - extras
    assert not stale, f"budgets.toml names extras that no longer exist: {sorted(stale)}"


def test_empty_extras_are_listed_and_the_list_is_exact() -> None:
    policy = load_budgets()["extras_policy"]
    known_empty = set(policy["known_empty"])
    bundles = set(policy["bundles"])
    extras = pyproject()["project"]["optional-dependencies"]

    empty = {n for n in extras if n not in bundles and not _extra_requirements(n)}
    assert empty == known_empty, (
        f"Extras without dependencies of their own: {sorted(empty)}. They are modules, not "
        "extras. Remove them from pyproject.toml and from known_empty in budgets.toml."
    )


def test_module_level_imports_are_standard_lambda_or_listed() -> None:
    """Standard library and Lambda libraries are free; anything else is counted and can only shrink."""
    from tests.budget.measure import module_level_third_party_imports

    budgets = load_budgets()
    found = module_level_third_party_imports(budgets["lambda"]["preinstalled"])
    listed = dict(budgets["imports"]["max_files"])

    unlisted = {pkg: files for pkg, files in found.items() if pkg not in listed}
    assert not unlisted, (
        "New third-party imports at module level: "
        + "; ".join(f"{pkg} in {files}" for pkg, files in unlisted.items())
        + ". Use the standard library or a library the AWS Lambda runtime already has. If an optional "
        "library is really needed, import it inside the function that uses it (LazyImporter)."
    )

    changed = {
        pkg: (len(found.get(pkg, [])), n) for pkg, n in listed.items() if len(found.get(pkg, [])) != n
    }
    assert not changed, (
        "Third-party import counts differ from budgets.toml (found, listed): "
        f"{changed}. Update [imports.max_files]; when a library reaches zero, remove it and its dependency."
    )
