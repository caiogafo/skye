---
title: "Structured outputs"
status: current
last_updated: 2026-11-02
---

# Structured outputs

How to get a typed, schema-validated object back from a model instead of free text.

- Define the target shape as a schema and pass it on the request; the adapter asks the
  provider for output that conforms to it.
- The provider-specific way of requesting structured output (response format, tool/function
  calling, JSON mode) is handled **inside the provider adapter** — the core request stays
  provider-agnostic. See [provider transformation architecture](provider-transformation-architecture.md).
- The JSON Schema is derived from the declared shape; the response is validated against it
  before it is returned. A response that does not conform raises a Skye error.

## The declared shape

`response_schema` is a dataclass: `@validated` (with `field(...)` limits, nested dataclasses, enums, optional fields) or a plain
`@dataclass`. A pydantic model of your own also works, because the library only calls its `model_json_schema` and
`model_validate_json`; the library itself does not import pydantic.

```python
import skye
from skye import UserMessage
from skye.data import Validated, validated

@validated
class Person(Validated):
    name: str
    age: int

client = skye.provider("openai", api_key="sk-...")
response = client.complete(messages=[UserMessage(content="Ana is 31")], model="gpt-4", response_schema=Person)
person = response.structured_output  # a Person
```

## How each provider is asked

| Provider | Request | Reply read from |
|---|---|---|
| OpenAI, Azure OpenAI | `response_format` of type `json_schema`; `strict` only when every property is required (strict mode demands it) | the message text |
| Anthropic | one forced tool (`skye_structured_output`) whose `input_schema` is the schema (function calling) | the input of that tool |
| Bedrock | the same forced tool in `toolConfig` | the input of that tool |
| Google | `responseMimeType: application/json` and the JSON Schema in the system instruction | the text |

The reply is checked once, for every provider: a text that is not JSON, lacks a required field or holds a value of the wrong type
raises `ValidationError` naming the field; it is not retried. These request shapes are tested against a fake network, not against
the live services. The forced tool is used only when the request carries no other capabilities.
