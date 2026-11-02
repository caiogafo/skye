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
from skye.base.completion import CompletionRequest, CompletionResponse
from skye.base.messages import UserMessage, AssistantMessage

# router (core)
from skye.router import ModelRouter, ModelTarget
from skye.base.interfaces.router import RoutingStrategy

# providers (only with the matching extra installed; loaded lazily)
from skye.models.llm import openai_compatible
```

## First call

```python
from skye.router import ModelRouter
from skye.base.messages import UserMessage

router = ModelRouter.from_yaml("router_config.yaml")
response = router.complete(messages=[UserMessage(content="Hello!")], model="gpt-4")
print(response.content)
```

Next: [routing guide](router/routing-guide.md), [configuration](base/configuration.md),
[structured outputs](models/structured-outputs.md).
