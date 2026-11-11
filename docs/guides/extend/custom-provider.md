---
title: "Custom provider"
status: current
---

# Custom provider

This guide shows you how to write a provider adapter for a model API that Skye does not cover, register it under a name, and use it
like the built-in ones.

## Before you start

You may not need an adapter:

- **An OpenAI-compatible server** (vLLM, Ollama, LM Studio, a gateway): use the OpenAI provider with its address,
  `skye.provider("openai", api_key="...", api_base="http://localhost:8000/v1")`.
- **A function or an SDK you only want to call**: wrap it as a `Runnable`, which is lighter. See
  [`bring_your_own_adapter.py`](https://github.com/ggiallo28/skye/blob/main/examples/providers/bring_your_own_adapter.py).

Write an adapter when you want the full client: `complete`, `stream`, the async forms, capabilities, structured output, retries,
health counters and routing.

## How an adapter works

`BaseModelProvider` in [`skye.models`](../../reference/api/models.md) keeps what is common to every provider. Your subclass only
translates: Skye types to the wire format of the service, and back. All the provider-specific logic stays in your class; nothing else
in Skye changes.

```mermaid
flowchart LR
    req["CompleteRequest"] --> tr["_transform_request<br/>(_transform_messages, _transform_capabilities)"]
    tr --> call["_call_provider"]
    call --> resp["_transform_response<br/>(_extract_capability_calls)"]
    resp --> out["CompleteResponse"]
```

## 1. Subclass `BaseModelProvider`

Implement the eleven abstract methods. This toy provider answers by shouting the last message; the "service" is a local function, so
nothing leaves the process.

```python
--8<-- "examples/advanced/custom_providers.py:10:69"
```

What each method does:

| Method | Turns | Into |
|---|---|---|
| `_initialize_client()` | nothing | the client of the service, created on first use (`self.client`); return `None` for plain HTTP |
| `_transform_messages(messages)` | Skye messages | the message list of the service (roles, system text, images, tool results) |
| `_transform_capabilities(capabilities)` | capabilities (`get_schema()` of each) | the tool definitions of the service |
| `_transform_request(request)` | a `CompleteRequest` | the request body of the service |
| `_call_provider(request)` | the request body | the raw answer |
| `_call_provider_stream(request)` | the request body | an iterator of raw chunks |
| `_transform_response(response)` | the raw answer | a `CompleteResponse` (content, finish reason, `TokenUsage`, `capability_calls`) |
| `_transform_stream_chunk(chunk)` | a raw chunk | a `StreamChunk` |
| `_extract_capability_calls(response)` | the raw answer | a list of `CapabilityCall` (`skye.completion`), or `None` |
| `format_capability_results(results)` | capability results | the messages the service expects for them |
| `get_model_info()` | nothing | a dictionary describing the model (see below) |

The keyword arguments given to `skye.provider(name, **config)` arrive in your constructor and are kept in `self.config`. Read keys and
endpoints from there, and import an SDK only inside `_initialize_client`, so importing your module stays cheap.

## 2. Describe the model

`get_model_info()` tells Skye what the model can do. The keys it reads:

| Key | Effect |
|---|---|
| `provider` | the provider name in errors |
| `supports_system_messages` | `False` puts the system text of a rendered prompt in the first user message (default `True`) |
| `supports_structured_output`, `supports_function_calling` | either one lets an output schema travel natively; without both, the schema is written as instructions in the prompt |
| `supports_streaming` | whether `stream` makes sense for this model |

## 3. Register it and use it

```python
--8<-- "examples/advanced/custom_providers.py:72:80"
```

`ProviderRegistry.register_model_provider(name, cls)` makes `name` a provider like `"openai"`: `skye.provider(name, **config)` builds
it, and a router can balance it with the others (`"shout/shout-1"` in a route). An embedding adapter subclasses `BaseEmbeddingProvider`
and is registered with `register_embedding_provider`.

## What you get for free

- **Entry points**: `complete`, `stream`, `acomplete` and `astream`. The async forms run the sync ones in a worker thread of the
  event loop's executor (`astream` hands each chunk over through a queue), so the loop is never blocked; override them when the
  service has a native async client.
- **Retries** (decision D104): a `RateLimitError`, `ServerError` or `ProviderTimeoutError` raised by the transform or the call is
  retried up to `max_retries` times (3 by default, `0` turns them off), with exponential backoff (1, 2, 4 ... seconds, at most 20)
  or the error's `retry_after`; a stream only before its first chunk. Any other `ProviderError` is raised at once, unchanged. Any
  other exception is wrapped in a `ProviderError` (a `ProviderTimeoutError` for a timeout or a dropped connection). A
  `ValidationError` (bad input) is not retried. Raise the subclass that matches the failure, so the client and the router read it.
- **HTTP**: `skye.models.post_json(url, body, headers=..., authenticator=..., provider=...)` and `skye.models.stream_sse_json` are
  the standard-library transport of the built-in adapters; they return the decoded JSON (`JsonObject`, attribute access) and raise
  the `ProviderError` subclass of the response. `authenticator` takes any authenticator of `skye.auth` (SigV4, Entra ID, Google).
- **Structured output**: when the request has a `response_schema`, the text of the answer is validated against it once, for every
  provider; a mismatch raises `ValidationError`.
- **Capabilities**: the capabilities of the request are attached to the response, so `response.execute_capability_calls()` works.
- **Health**: success, failure and latency counters (`get_health_metrics()`), which the router reads.

## See also

- [Call a provider](../models/call-a-provider.md): how the built-in providers are used.
- [Which Port to implement](index.md): `ModelInterface` and `VectorEncoderInterface` are the Ports behind the base classes.
- Reference: [`skye.models`](../../reference/api/models.md).
- Example: [`custom_providers.py`](https://github.com/ggiallo28/skye/blob/main/examples/advanced/custom_providers.py).
