---
title: "First router"
status: current
---

# First router

This page shows you how to give one name to a model and a fallback, so that your code asks for `"fast"` and the router picks the
model, and tries the next one when the first fails. You build the router in Python first, then load the same router from a `.skye`
file.

## What you need

- Skye installed: see [Install](index.md).
- The key of each provider you route to, in its standard variable: `OPENAI_API_KEY` for OpenAI, `ANTHROPIC_API_KEY` for Anthropic.
  Bedrock reads the usual AWS credentials. Azure OpenAI needs its endpoint, so it goes in the full form (below), not in the shorthand.
- A first call working: see [First model call](first-call.md).

## An alias with a fallback, in Python

`ModelRouter` takes a dictionary from an alias to a list of `"provider/model"` entries. The first entry is the primary; the others
are its fallbacks, tried in order:

```python
from skye import UserMessage
from skye.router import ModelRouter

router = ModelRouter({"fast": ["openai/gpt-4o-mini", "anthropic/claude-haiku-5-5"]})

response = router.complete(messages=[UserMessage(content="What is 2+2?")], model="fast")
print(response.content)
print(router.last_serving["provider"], router.last_serving["fallback"])
```

What you get:

- `router.complete` takes the same messages as a client and the alias as `model`. It returns the same `CompleteResponse`.
- The router creates the client of each entry with `skye.provider` and reads its key from the standard variable of the provider.
- When the primary fails, the router calls the fallback. `router.last_serving` tells you who answered: `provider`, `model`,
  `fallback` (`True` when a fallback answered), `tried` (the targets that failed first). The same record is in
  `response.metadata["router"]`.
- `router.list_aliases()` lists the names: here `fast` and `fast/fallback1`, the route the shorthand makes for the fallback.

A provider name without a key in the environment raises `ConfigurationError` when you create the router, not at the first call.

## The full form

The shorthand builds the same objects you can write yourself: a `RouteConfig` per alias with its `ModelTarget` list, and a
`FallbackConfig` for the chain. The full form gives you the strategy of each route, rate limits (`tpm`, `rpm`) and retry policies:

```python
--8<-- "examples/routing/fallbacks_and_health.py:13:45"
```

`router_provider("openai")` comes from the offline helper of the examples: it returns `"openai"` when `OPENAI_API_KEY` is set and a
local scripted provider otherwise, so the example runs without a key.

## The same router from a `.skye` file

A router can live in a `.skye` file instead of Python code. The same shorthand reads:

```skye
---
title       = "chat"
description = "The chat models: a fast OpenAI model with an Anthropic fallback."
version     = "0.1.0"
tags        = []
---

router "chat" {
  route "fast" = ["openai/gpt-4o-mini", "anthropic/claude-haiku-5-5"]
}
```

Save it as `router.skye`, check it with `skye check router.skye`, and load it with `ModelRouter.from_file`:

```python
from skye import UserMessage
from skye.router import ModelRouter

router = ModelRouter.from_file("router.skye")  # name="chat" when the file holds several routers
response = router.complete(messages=[UserMessage(content="Hello!")], model="fast")
```

Keyword arguments of `from_file` override the file, for example `ModelRouter.from_file("router.skye", cooldown_seconds=120.0)`.
In the long form of a route, a key is written as `api_key = env.OPENAI_API_KEY`, so the file never holds a secret.
[`examples/routing/router_config.skye`](https://github.com/ggiallo28/skye/blob/main/examples/routing/router_config.skye) shows every
strategy in the long form, and [First .skye file](first-skye-file.md) shows how to create, format and draw such a file.

## See also

- [Aliases and fallbacks](../guides/routing/aliases-and-fallbacks.md): fallback chains, tags and the serving record in detail.
- [Strategies](../guides/routing/strategies.md) and [Health and cooldown](../guides/routing/health-and-cooldown.md).
- [Router state in a store](../guides/routing/router-state.md): keep health and usage between serverless invocations.
- [`skye.router` API reference](../reference/api/router.md).
- Examples: [`routing/basic_routing.py`](https://github.com/ggiallo28/skye/blob/main/examples/routing/basic_routing.py),
  [`routing/fallbacks_and_health.py`](https://github.com/ggiallo28/skye/blob/main/examples/routing/fallbacks_and_health.py),
  [`routing/skye_config_example.py`](https://github.com/ggiallo28/skye/blob/main/examples/routing/skye_config_example.py).
