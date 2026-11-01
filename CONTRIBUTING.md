# Contributing to Nimbus

Nimbus is a light, modular library for serverless GenAI applications. Contributions are welcome. Please read these rules before opening a pull request.

## Where code comes from

- Write the code yourself, or take it from a source whose licence allows it.
- Do not copy code from another project without adding its licence and attribution (a `NOTICE` or `THIRD_PARTY_NOTICES` file, and a comment at the copied code). Ideas and public API shapes are free; code and documentation text are not.
- Never copy from the `enterprise/` directory of LiteLLM: it is under a separate commercial licence.
- Nimbus is inspired by LangChain, LiteLLM, Pydantic, Cedar, Strands and Amazon Bedrock AgentCore Gateway. "Inspired" means ideas only. Do not use "AgentCore" in a product or module name.
- Prompt templates must be written for Nimbus or carry the licence of their source.
- Nimbus is MIT licensed. By contributing you agree that your contribution is released under the same licence.

## Dependencies and size

Nimbus is deployed as an AWS Lambda zip, without containers. For everything the library imports, in this order: the Python standard library, then libraries already in the Lambda runtime (boto3, botocore, urllib3, ...), then pure-Python packages, only when nothing earlier can do the job. Provider SDKs and other optional libraries are imported inside the function that uses them (`LazyImporter`), never at module level.

The limits are in `budgets.toml` and are checked in every pull request (see `docs/budgets.md`):

```bash
make budget-fast    # policy and import checks, a second
make budget         # installs Nimbus in clean environments, about a minute
```

A budget only goes down. Raising one needs a reason in the pull request and a review from the owner of `budgets.toml`.

## Specs

Design work is spec driven, with Kiro. Requirements, design and tasks for each feature live in `.kiro/specs/`, and project-wide rules in `.kiro/steering/`. For a new feature, add or update the spec in the same pull request.

## Before you open a pull request

```bash
uv run pytest
make check
make budget-fast
```
