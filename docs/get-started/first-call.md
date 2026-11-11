---
title: "First model call"
status: current
---

# First model call

This page shows you how to create a client for a model provider, send it a message and read the answer, first in plain Python and
then with `async`/`await`.

## What you need

- Skye installed: see [Install](index.md). Every built-in provider is part of the base install; you do not need an extra.
- A key for one provider, for example `OPENAI_API_KEY`. You can follow the examples without a key: see
  [Run the examples offline](#run-the-examples-offline).

## Create a client and ask a question

`skye.provider(name, **config)` creates the client of a provider, in the style of `boto3.client`. The first argument is the provider
name; the other arguments are its configuration. The client has `complete` for one answer.

```python
import skye
from skye import UserMessage

client = skye.provider("openai")  # the key from OPENAI_API_KEY; or api_key="sk-..."

response = client.complete(
    messages=[UserMessage(content="What is the capital of France?")],
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=100,
)
print(response.content)
```

`messages` is a list of messages; a plain string also works and becomes one `UserMessage`. `model` is the provider's model name.
`temperature` and `max_tokens` are optional: when you leave them out, the request keeps its defaults.

Without `api_key`, each client reads its provider's standard variable (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
`AZURE_OPENAI_API_KEY`, `COHERE_API_KEY`); when it is not set, `ConfigurationError` names it. Bedrock and Google find their
credentials in the usual places of their cloud. [Call a provider](../guides/models/call-a-provider.md) lists every provider and
its options.

## Read the answer

`complete` returns a `CompleteResponse`. The fields you use most:

| Field | What it holds |
|---|---|
| `content` | the text of the answer |
| `finish_reason` | why the model stopped, as the provider says it (for example `stop` on OpenAI, `end_turn` on Anthropic) |
| `usage` | a `TokenUsage` with `prompt_tokens`, `completion_tokens` and `total_tokens` |
| `provider`, `model` | who answered |
| `structured_output` | the typed object, when you asked for a [structured output](../guides/models/structured-output.md) |

This example sends a system message and a user message, prints the fields above, and then continues a conversation by sending the
whole history again:

```python
--8<-- "examples/basic/simple_completion.py:19:29"
```

The message types are `SystemMessage`, `UserMessage`, `AssistantMessage` and `CapabilityMessage` (the result of a tool call); you
import all four from `skye`.

## The same call with async

Every client also has `acomplete`, the async form of `complete`. It takes the same arguments. The `sys.path` and `_offline` lines
only pick a scripted client when no key is set (see [below](#run-the-examples-offline)):

```python
--8<-- "examples/basic/async_and_streaming.py"
```

The example also shows `stream`, which yields the answer in chunks as the model writes it. [Streaming and async](../guides/models/streaming.md)
covers both in detail.

## Errors

A failed call raises a `ProviderError` (from `skye`) of the class of the failure: `RateLimitError`, `ServerError`,
`ProviderTimeoutError`, `AuthenticationError`, `BadRequestError` (all in `skye.exceptions`). The client retries the first three by
itself, three times by default with a growing wait (or the server's `Retry-After`), and raises the others at once: a wrong key or a bad
request does not get better by asking again. A wrong configuration, such as a missing key, raises `ConfigurationError` when you
create the client. All of them are `SkyeError`, so one `except SkyeError` catches every error of the library. See
[Errors and retries](../guides/models/call-a-provider.md#errors-and-retries).

## Run the examples offline

The runnable examples in [`examples/`](https://github.com/ggiallo28/skye/blob/main/examples/README.md) work with or without a key.
They create the client with `get_client("openai")` from
[`examples/_offline.py`](https://github.com/ggiallo28/skye/blob/main/examples/_offline.py), a helper of the examples that is not
part of the package:

- with `OPENAI_API_KEY` set, it returns `skye.provider("openai", api_key=...)` and the call is real;
- without the key, it returns a scripted client that answers locally, with the same methods (`complete`, `acomplete`, `stream`,
  `astream`) and the same response type, and it prints `mode: scripted`.

```python
--8<-- "examples/basic/quickstart.py"
```

Run it with `python examples/basic/quickstart.py`. The tests of the project run every example this way, so the code on these pages
stays correct.

## See also

- [Call a provider](../guides/models/call-a-provider.md): OpenAI, Anthropic, Bedrock, Azure OpenAI, Google and their options.
- [First router](first-router.md): one name for several models, with a fallback.
- [`skye` API reference](../reference/api/skye.md) and [`skye.models` API reference](../reference/api/models.md).
- Examples: [`basic/quickstart.py`](https://github.com/ggiallo28/skye/blob/main/examples/basic/quickstart.py),
  [`basic/simple_completion.py`](https://github.com/ggiallo28/skye/blob/main/examples/basic/simple_completion.py),
  [`basic/async_and_streaming.py`](https://github.com/ggiallo28/skye/blob/main/examples/basic/async_and_streaming.py).
