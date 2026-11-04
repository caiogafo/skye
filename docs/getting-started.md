---
title: "Getting started"
status: current
last_updated: 2026-11-02
---

# Getting started

Skye is one package, `skyeai`, with optional extras. Install the base and add only the
extras you need.

## Install

```bash
# Base: messages, completion, errors, config, Ports (standard library only)
pip install skyeai

# With one provider / feature extra
pip install skyeai[openai]
pip install skyeai[bedrock]

# Several at once
pip install skyeai[openai,memory]
```

An extra pulls third-party libraries only where a component actually imports them; many
components (for example `tools`, `prompts`, `guard`) are pure Python and need no extra. See
[budgets](budgets.md) and the project rules steering (`00-rules`) for the dependency rules.

## Imports

Import by **component** name; there is no layer in the path.

```python
# base re-exports (always available)
from skye import CompletionRequest, CompletionResponse
from skye import UserMessage, AssistantMessage

# router (core)
from skye.router import ModelRouter, ModelTarget
from skye.router import RoutingStrategy

# provider classes (no extra needed: each provider has a built-in REST adapter)
from skye.models import OpenAIProvider, AnthropicProvider
```

## First call

```python
from skye.router import ModelRouter
from skye import UserMessage

router = ModelRouter.from_yaml("router_config.yaml")  # a YAML file needs the extra: pip install skyeai[yaml]
response = router.complete(messages=[UserMessage(content="Hello!")], model="gpt-4")
print(response.content)
```

Next: [routing guide](router/routing-guide.md), [configuration](base/configuration.md),
[structured outputs](models/structured-outputs.md).

## Installation options and extras

### Base Package (Interfaces + Models)

```bash
pip install skyeai
```

Or with uv:

```bash
uv pip install skyeai
```

### With Optional Extras

```bash
# Single provider
pip install skyeai[bedrock]
uv pip install skyeai[bedrock]

# Multiple extras
pip install skyeai[bedrock,agents,memory]
uv pip install skyeai[bedrock,agents,memory]

# Everything
pip install skyeai[all]
uv pip install skyeai[all]
```

### Available Extras

The standard installation (`pip install skyeai`) has only `pydantic` and `tenacity` and works without any extra. Each extra installs one
optional library, only for what you ask for:

| Extra | What it enables | Library installed |
|-------|-----------------|-------------------|
| `yaml` | reading a YAML file (router and library configuration; JSON needs nothing) | pyyaml |
| `auth` | RS256 signing for service-account authentication | rsa |
| `memory` | the Redis store backend | redis |
| `postgres` | the PostgreSQL store backend | asyncpg (compiled) |
| `mcp` | the optional `fastmcp` client, chosen with `impl="fastmcp"` (the built-in client needs nothing) | fastmcp (heavy, compiled) |
| `tokens` | exact token counts for `gpt-*`, `o1-*` and `o3-*` models (a standard-library estimate is used without it) | tiktoken (compiled) |
| `openai`, `anthropic`, `bedrock`, `google`, `cohere` | nothing: each provider has a built-in REST adapter; they exist so old install commands keep working | none |
| `agents`, `prompts`, `tools`, `guard`, `teams`, `flows`, `observe` | nothing: these components are part of the core | none |
| `all` | all the libraries above | all of the above |

## Quick Start

### Basic Usage

```python
import skye
from skye import UserMessage

# Create provider client (boto3-style)
client = skye.provider("bedrock", region="us-east-1")

# Make completion request
response = client.complete(
    messages=[UserMessage(content="Hello, world!")],
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    temperature=0.7
)

print(response.content)
```

### Async Usage

```python
import asyncio
import skye
from skye import UserMessage

async def main():
    client = skye.provider("openai", api_key="sk-...")
    
    response = await client.acomplete(
        messages=[UserMessage(content="Explain async/await")],
        model="gpt-4"
    )
    
    print(response.content)

asyncio.run(main())
```

### Streaming

```python
import skye
from skye import UserMessage

client = skye.provider("openai", api_key="sk-...")

for chunk in client.stream(
    messages=[UserMessage(content="Write a story")],
    model="gpt-4"
):
    print(chunk.delta, end="", flush=True)
```

### Structured Outputs

```python
import skye
from skye import UserMessage
from skye.data import Validated, validated

@validated
class Person(Validated):
    name: str
    age: int
    occupation: str

client = skye.provider("openai", api_key="sk-...")

response = client.complete(
    messages=[UserMessage(content="Extract: John is 30 and works as an engineer")],
    model="gpt-4",
    response_schema=Person
)

person = response.structured_output  # Returns Person instance
print(f"{person.name} is {person.age} years old")
```

