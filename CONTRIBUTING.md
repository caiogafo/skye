# Contributing to Skye

Skye is a light, modular library for serverless GenAI applications. Contributions are welcome. Please read these rules before opening a pull request.

## Where code comes from

- Write the code yourself, or take it from a source whose licence allows it.
- Do not copy code from another project without adding its licence and attribution (a `NOTICE` or `THIRD_PARTY_NOTICES` file, and a comment at the copied code). Ideas and public API shapes are free; code and documentation text are not.
- Never copy from the `enterprise/` directory of LiteLLM: it is under a separate commercial licence.
- Skye is inspired by LangChain, LiteLLM, Pydantic, Cedar, Strands and Amazon Bedrock AgentCore Gateway. "Inspired" means ideas only. Do not use "AgentCore" in a product or module name.
- Prompt templates must be written for Skye or carry the licence of their source.
- Skye is MIT licensed. By contributing you agree that your contribution is released under the same licence.

## Dependencies and size

Skye is deployed as an AWS Lambda zip, without containers. For everything the library imports, in this order: the Python standard library, then libraries already in the Lambda runtime (boto3, botocore, urllib3, ...), then pure-Python packages, only when nothing earlier can do the job. Provider SDKs and other optional libraries are imported inside the function that uses them (`LazyImporter`), never at module level.

The limits are in `budgets.toml` and are checked in every pull request (see `docs/budgets.md`):

```bash
make budget-fast    # policy and import checks, a second
make budget         # installs Skye in clean environments, about a minute
```

A budget only goes down. Raising one needs a reason in the pull request and a review from the owner of `budgets.toml`.

## Specs

Design work is spec driven, with Kiro. Requirements, design and tasks for each feature live in `.kiro/specs/`, and project-wide rules in `.kiro/steering/`. For a new feature, add or update the spec in the same pull request.

## Built-in vs external library

When a Component offers a built-in standard-library implementation and one backed by an external library (a provider SDK, `fastmcp`), both sit behind the same Port and return the same Skye types. The external types are converted to Skye types at one boundary point inside the owning Component, and none is exposed in a Port return value, parameter or public API. Today this governs `models` (provider SDKs; only the SDK path exists, no REST adapter yet) and the `tools` MCP client (`mcp_client.py` built-in, `mcp_fastmcp.py` fastmcp, one conversion in `mcp_boundary.py`, which imports no third-party library). A future external backend for `observe`, `store`, `prompts` or `agents` follows the same rule, with no new Component and no new Port. Keep the library import inside a function in the owning file, convert at the boundary, and add the file to `SDK_OWNERS` in `tests/budget/test_boundary_rule.py` (`make budget-fast` enforces it; `tests/differential/test_boundary_leak.py` checks both MCP clients against the fake server). Details: `docs/budgets.md`, Requirement 16 in `.kiro/specs/skye-structure/`.

## Before you open a pull request

```bash
uv run pytest
make check
make budget-fast
```
