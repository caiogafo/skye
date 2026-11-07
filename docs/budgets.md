---
title: "Size and load budgets"
status: current
last_updated: 2026-11-02
---

# Size and load budgets

Skye is meant for serverless, where every dependency is paid at install time (package size), at cold start (import time and memory) and at build time (a compiled wheel needs a container for the right architecture). The limits live in `budgets.toml` and are checked by tests and by the `budgets` workflow on every pull request.

## Principles

For everything Skye imports, in this order:

1. the Python standard library;
2. libraries the AWS Lambda Python runtime already contains (`boto3`, `botocore`, `s3transfer`, `jmespath`, `python-dateutil`, `six`, `urllib3`; listed in `[lambda]`);
3. pure-Python packages (wheel tagged `py3-none-any`), only when 1 and 2 cannot do the job;
4. never a compiled package (C or Rust extension) in the core. The library is I/O bound, so speed is not a reason to accept one.

Provider SDKs and optional libraries are imported inside the function that uses them (`LazyImporter`), never at module level.

## What is checked

| Check | Where | Needs |
|---|---|---|
| Core dependency list equals `[core] allowed_dependencies` | `tests/budget/test_policy.py` | nothing |
| Every extra has a budget, an empty extra is listed, bundles are listed | `test_policy.py` | nothing |
| Third-party imports at module level in `src/skye` match `[imports.max_files]` | `test_policy.py` | nothing |
| `import skye` imports no provider SDK or optional library (known leaks are listed) | `test_load_budget.py` | nothing |
| Core install: packages, size, compiled packages, every subpackage imports | `test_footprint_budget.py` | `uv`, network |
| `import skye` in a clean core install: modules, time, memory | `test_footprint_budget.py` | `uv`, network |
| Each extra: size added over the core, compiled packages added | `test_footprint_budget.py` | `uv`, network |
| Serverless profile (core + `bedrock`) stays far below the 250 MB Lambda limit | `test_footprint_budget.py` | `uv`, network |

Run them:

```bash
make budget-fast    # policy and import checks, a second
make budget         # installs Skye in clean environments, about a minute
```

Sizes exclude the libraries Lambda already ships. Time is the best of five fresh interpreters. Measurements were taken on Python 3.13; the workflow runs the fast checks on 3.10 and 3.13 and the footprint checks on 3.13.

**Sizes are Linux sizes.** The footprint jobs run on a Linux x86_64 runner, which is also the serverless target, and the compiled wheels (`pydantic-core`, `asyncpg`, ...) are larger there than on macOS: the core is 11.3 MB on Linux and 8.5 MB on macOS. The limits in `budgets.toml` are the Linux ones. To check the sizes from any machine, without a Linux runner:

```bash
uv pip install --target /tmp/skye-linux --python-platform x86_64-manylinux_2_28 --python-version 3.13 "skyeai[memory] @ file:///path/to/skyeai.whl"
```

and measure the folder as `tests/budget/measure.py` does. The footprint jobs of the workflow are one per extra that has a budget; `tests/budget/test_workflow_matrix.py` keeps that list in step with `budgets.toml`.

## No external-library type outside its Component

`tests/budget/test_boundary_rule.py` (part of `make budget-fast`) checks the boundary rule (Requirement 9.5 in `.kiro/steering/10-requirements.md`): provider SDKs (`openai`, `anthropic`, `boto3`, `vertexai`/`google.cloud.aiplatform`, `cohere`) and `fastmcp`/`mcp` are imported only by the files that own them, only inside a function, `tools/mcp_boundary.py` imports no third-party library, no public annotation in `models`/`tools` names an external type, and the provider and MCP conversions return Skye types only. A new external backend (for `observe`, `store`, `prompts`, `agents`) adds its owning file to `SDK_OWNERS` in that test; no new Component or Port. `tests/differential/test_boundary_leak.py` runs the same check on both MCP clients (needs `fastmcp`, dev group).

## Changing a budget

A budget only goes down. When a PR fixes something (removes a dependency, moves an import behind `LazyImporter`), the matching test fails until the list in `budgets.toml` is updated, so the number follows the code. Raising a number needs a reason in the PR and a review from the owner of `budgets.toml` (`.github/CODEOWNERS`).

To make the check blocking, require the `budgets / fast checks` and `budgets / footprint` jobs in the repository's branch protection rules. This is a GitHub setting, not part of the repository.

## Debt recorded today (2026-11-02)

Checked against `budgets.toml` and `pyproject.toml`.

| Item | Why it matters | Target |
|---|---|---|
| Core depends on `pydantic` and `tenacity` (neither in Lambda nor in the standard library) | 8.4 MB on Linux (limit 11), 7 packages; `pydantic-core` is most of it | standard library only (pydantic goes with the dataclass migration, open decision O4) |
| Compiled in the core: `pydantic-core` (Rust) | needs a container build | none |
| Extras with no dependency of their own: `agents`, `guard`, `prompts`, `tools`, `teams`, `flows`, `observe`, and the provider extras `anthropic`, `bedrock`, `google`, `cohere` | they are modules, not extras (the provider extras stay so `pip install skyeai[...]` keeps working) | remove the ones that are not provider extras from `pyproject.toml` |
| Extra sizes over the core, on Linux: `auth` 0.5 MB (`rsa`), `memory` 2.6 MB (`redis`), `yaml` 2.9 MB (`pyyaml`, compiled), `tokens` 8.4 MB (`tiktoken`, compiled; decision D33), `postgres` 14.0 MB (`asyncpg`, compiled), `mcp` 50.6 MB (`fastmcp`, 7 compiled distributions, over its limit of 48: `fastmcp` itself depends on `pyyaml`, so what left the core now counts as added by this extra, while the whole `mcp` environment is unchanged at 59.0 MB; open until the owner decides how the `mcp` extra is measured) | the compiled ones | only who installs an extra pays for it |
| `skyeai[all]` size | it includes `mcp` and `memory` | not advertised for Lambda |

### What the core weighs (Linux x86_64, Python 3.13, 2026-11-02)

The 11 MB in `budgets.toml` is a ceiling, not a measurement. The installed core is 8.9 MB (`du`):

| Component | MB |
|---|---|
| `pydantic_core` (one compiled `.so`, 5.0 MB) | 5.1 |
| `pydantic` | 2.0 |
| `typing_extensions`, `typing_inspection`, `annotated_types`, `dist-info` folders | about 0.5 |
| `skye` (676 KB of sources) | 0.9 |
| `tenacity` | 0.15 |

The pydantic stack is about 7.7 MB, 86% of the core; removing it (open decision O4, tasks 14.1 to 14.3 of `0-base-structure`) brings the core to about 1.2 MB. Without it the core does not go below about 8.7 MB.

Done since the previous table (2026-10-30): `jinja2` and `markupsafe` left the core (the prompts engine is standard library), and the provider SDK extras
(`google` 176 MB, `cohere` 33 MB, `anthropic` 10 MB) are now empty because every provider has one built-in REST adapter.

### Import cost per component package (until pydantic is removed, open decision O4)
Whether a package loads pydantic when imported, measured by the modules that import it at the top level (2026-11-05):

- `skye` and `skye.base` (and the facades `skye.interfaces`, `skye.data`, `skye.messages`, `skye.completion`, `skye.exceptions`, `skye.config`): no.
- `skye.agents`, `skye.auth`, `skye.flows`, `skye.gateway`, `skye.guard`, `skye.models`, `skye.observe`, `skye.policy`, `skye.prompts`, `skye.store`, `skye.teams`: no.
- `skye.router`: yes (one module).
- `skye.tools`: yes (two modules, among them the pydantic `CapabilitySchema`).
- `skye.memory`: yes (one module).
- `skye.utils`: yes (`validation`, for pydantic structured-output classes).
