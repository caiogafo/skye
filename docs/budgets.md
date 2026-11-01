# Size and load budgets

Nimbus is meant for serverless, where every dependency is paid at install time (package size), at cold start (import time and memory) and at build time (a compiled wheel needs a container for the right architecture). The limits live in `budgets.toml` and are checked by tests and by the `budgets` workflow on every pull request.

## Principles

For everything Nimbus imports, in this order:

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
| Third-party imports at module level in `src/nimbus` match `[imports.max_files]` | `test_policy.py` | nothing |
| `import nimbus` imports no provider SDK or optional library (known leaks are listed) | `test_load_budget.py` | nothing |
| Core install: packages, size, compiled packages, every subpackage imports | `test_footprint_budget.py` | `uv`, network |
| `import nimbus` in a clean core install: modules, time, memory | `test_footprint_budget.py` | `uv`, network |
| Each extra: size added over the core, compiled packages added | `test_footprint_budget.py` | `uv`, network |
| Serverless profile (core + `bedrock`) stays far below the 250 MB Lambda limit | `test_footprint_budget.py` | `uv`, network |

Run them:

```bash
make budget-fast    # policy and import checks, a second
make budget         # installs Nimbus in clean environments, about a minute
```

Sizes exclude the libraries Lambda already ships. Time is the best of five fresh interpreters. Measurements were taken on Python 3.13; the workflow runs the fast checks on 3.10 and 3.13 and the footprint checks on 3.13.

## No external-library type outside its Component

`tests/budget/test_boundary_rule.py` (part of `make budget-fast`) checks Requirement 20: provider SDKs (`openai`, `anthropic`, `boto3`, `vertexai`/`google.cloud.aiplatform`, `cohere`) and `fastmcp`/`mcp` are imported only by the files that own them, only inside a function, `tools/mcp_boundary.py` imports no third-party library, no public annotation in `models`/`tools` names an external type, and the provider and MCP conversions return Nimbus types only. A new external backend (for `observe`, `store`, `prompts`, `agents`) adds its owning file to `SDK_OWNERS` in that test; no new Component or Port. `tests/differential/test_boundary_leak.py` runs the same check on both MCP clients (needs `fastmcp`, dev group).

## Changing a budget

A budget only goes down. When a PR fixes something (removes a dependency, moves an import behind `LazyImporter`), the matching test fails until the list in `budgets.toml` is updated, so the number follows the code. Raising a number needs a reason in the PR and a review from the owner of `budgets.toml` (`.github/CODEOWNERS`).

To make the check blocking, require the `budgets / fast checks` and `budgets / footprint` jobs in the repository's branch protection rules. This is a GitHub setting, not part of the repository.

## Debt recorded today (2026-10-30)

| Item | Why it matters | Target |
|---|---|---|
| Core depends on `pydantic`, `jinja2`, `pyyaml`, `tenacity` (none in Lambda, none in the standard library) | about 9 MB and 10 packages | standard library only |
| Compiled in the core: `pydantic-core` (Rust), `pyyaml` and `markupsafe` (C) | needs a container build | none |
| Extras `agents`, `guard`, `prompts`, `teams`, `flows` have no dependencies of their own | they are modules, not extras | remove from `pyproject.toml` |
| Extra sizes over the core: `google` 176 MB, `cohere` 33 MB, `openai` 18 MB, `memory` 12 MB, `anthropic` 10 MB | most come from provider SDKs | call the provider REST APIs with the standard library or `urllib3` |
| `nimbus[all]` is about 274 MB, over the Lambda limit | cannot be deployed | not advertised for Lambda |
