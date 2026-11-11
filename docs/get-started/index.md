---
title: "Install"
status: current
---

# Install

Skye is one package, `skyeai`, for Python 3.11 or newer. The base install has no third-party dependency: every model provider
is built in.

=== "pip"

    ```bash
    pip install skyeai
    ```

=== "uv"

    ```bash
    uv add skyeai
    ```

Check it:

```bash
python -c "import skye; print(skye.__version__)"
skye --help
```

## Extras

An extra installs one optional library, only for the feature that needs it. You never need an extra to call a provider.

| You want | Install |
|---|---|
| Exact token counts for OpenAI models | `pip install skyeai[tokens]` |
| State in Valkey or Redis | `pip install skyeai[valkey]` or `pip install skyeai[redis]` |
| State in PostgreSQL (outside Aurora's Data API) | `pip install skyeai[postgres]` |
| DynamoDB or the Aurora Data API outside AWS Lambda | `pip install skyeai[aws]` |
| RS256 signing for service accounts | `pip install skyeai[auth]` |
| The `fastmcp` client instead of the built-in one | `pip install skyeai[mcp]` |

Several at once: `pip install "skyeai[valkey,tokens]"`. The full table, with sizes, is in [Extras](../reference/extras.md).

## Next

1. [First model call](first-call.md): create a client and ask a question.
2. [First router](first-router.md): an alias with a fallback.
3. [First .skye file](first-skye-file.md): write, check and draw a router.
4. [Deploy on AWS Lambda](lambda.md): package size, credentials and state.

## Editor support

`skye vscode install` adds syntax highlighting and live checks for `.skye` files to VS Code. See
[Editor support](../reference/editor.md).
