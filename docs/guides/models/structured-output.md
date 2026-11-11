---
title: "Structured output"
status: current
---

# Structured output

This guide shows you how to get a typed object back from a model instead of free text: you declare the shape, Skye asks the
provider for it, checks the answer and gives you an instance.

## What you need

- A client from `skye.provider(...)`: see [Call a provider](call-a-provider.md). Every built-in model provider supports structured
  output.
- The shape of the answer, as a dataclass or as a JSON Schema.

## Declare the shape with a dataclass

The standard way is a dataclass marked `@validated`, from `skye.data`. Its fields can be nested dataclasses, enums, lists and
optional values; `field(...)` adds a description and limits (`ge`, `gt`, `le`, `lt`, `min_length`, `max_length`). Pass the class as
`response_schema` and read `response.structured_output`:

```python
--8<-- "examples/advanced/structured_output.py:10:57"
```

What you get:

- `response.structured_output` is a `Person`, not a dict; `response.content` still holds the raw text of the answer.
- An answer that is not JSON, lacks a required field, has a value of the wrong type or breaks a limit raises `ValidationError` naming
  the field. The call is not repeated: catch the error and decide.
- A plain `@dataclass` works too, and so does a pydantic model of your own: Skye only calls its `model_json_schema` and
  `model_validate_json`, and does not import pydantic itself.

Limits and lists, and the request-object form of the same call:

```python
--8<-- "examples/providers/structured_output_example.py:12:51"
```

## How each provider is asked

Skye turns the class into a JSON Schema and asks each provider in its own way. The request you write is the same for all.

| Provider | How the schema is sent | Where the answer is read |
|---|---|---|
| OpenAI, Azure OpenAI | `response_format` of type `json_schema`; strict mode only when every property is required, as strict mode demands | the text of the answer |
| Anthropic | the native `output_config.format` of type `json_schema` (objects closed with `additionalProperties: false`); no tool is forced, since a forced `tool_choice` is refused by Claude Opus 5.5, Sonnet 5.5 and Fable 5.1 | the text of the answer |
| Bedrock | one forced tool, `skye_structured_output`, in the Converse `toolConfig` | the input of that tool |
| Google | `responseMimeType: application/json` with a native `responseSchema`; a schema outside Gemini's subset (with `$ref` or `$defs`) goes in the system instruction instead | the text of the answer |

A schema with an optional field (such as `nickname: str | None = None`) is sent to OpenAI in non-strict mode, because strict mode
requires every property.

## Structured output with tools

A request can have both `capabilities` and a `response_schema`: the model may call the tools first, and its final answer follows the
schema. While the answer holds capability calls, `structured_output` stays `None` and nothing is checked; the turn that answers in
text is checked.

| Provider | How the schema travels with tools |
|---|---|
| OpenAI, Azure OpenAI, Google | as without tools: `response_format`, `responseSchema` |
| Anthropic | the native JSON output, `output_config.format` of type `json_schema`, next to the tools (objects are closed with `additionalProperties: false`; numeric and length limits are left out of what is sent, and checked by Skye) |
| Bedrock | the Converse API cannot force the answer tool and offer the others in the same turn, so the schema is written in the system instructions and the text of the final answer is checked |

## A JSON Schema instead of a class: `OutputSchema`

When the shape comes from data, not from code (a prompt file, a configuration), use `OutputSchema` from `skye.interfaces`: a name, a
JSON Schema of an object, and `strict` (default `True`). Pass it as `response_schema`, like a class. The answer comes back as a
`dict`, checked against the whole schema with a small standard-library validator: types, nested objects, arrays and their items,
`enum` and `const`, `required`, `additionalProperties`, `anyOf`/`oneOf`/`allOf`, `$ref` to `$defs`, and the length and number limits.
A mismatch raises `ValidationError` whose `field` is the path of the value (`address.city`, `tags[1]`).

```python
import skye
from skye import UserMessage
from skye.interfaces import OutputSchema

person = OutputSchema(
    "person",
    {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
    },
)

client = skye.provider("openai")  # the key from OPENAI_API_KEY
response = client.complete(messages=[UserMessage(content="Ana is 31")], model="gpt-4o-mini", response_schema=person)
response.structured_output  # {"name": "Ana", "age": 31}
```

## Prompt parts: native fields or text

`PromptParts` (from `skye.interfaces`) is a prompt that names no provider: the messages, the system text, an `OutputSchema`, and a
fallback text that says the same as the schema in words. Pass it to `complete` in place of the messages, and the client decides,
from what the model supports, where each part goes:

```python
from skye import UserMessage
from skye.interfaces import OutputSchema, PromptParts

parts = PromptParts(
    messages=(UserMessage(content="Ana is 31"),),
    system="Extract the person.",
    output=OutputSchema(
        "person",
        {"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}, "required": ["name", "age"]},
    ),
)

response = client.complete(parts, model="gpt-4o-mini")
response.structured_output  # {"name": "Ana", "age": 31}
```

- The system text goes in the native system field: Anthropic `system`, Gemini `systemInstruction`, Bedrock Converse `system`, an
  OpenAI system message. A model that reports no system messages gets it in front of the first user message.
- The schema goes natively when the model supports structured output (OpenAI, Azure OpenAI, Anthropic, Google) or function calling
  (Bedrock, through the forced tool).
- A model with neither gets the fallback text in its instructions, or, when `fallback_text` is `None`, a sentence Skye writes from the
  schema. It answers in plain text and `structured_output` stays `None`.

To see what a client would send, without a call, ask it for the request:

```python
request = client.request_from_parts(parts, model="gpt-4o-mini")
[m.role for m in request.messages]  # ['system', 'user']
request.response_schema             # the OutputSchema: sent natively
```

`PromptParts` needs a `model`: `complete(parts, router=...)` raises `ValueError`. Choose the model first.

You rarely build `PromptParts` by hand: `skye.prompts.render_parts(spec, variables)` renders a `.skye` prompt into one, with the
JSON Schema of its `output` block as the `OutputSchema` and the output instructions as `fallback_text`, and
`BasePromptBuilder.render_parts(name, variables)` does the same for a registered template (see
[Output schema](../prompts/output-schema.md#step-5-send-the-schema-as-a-native-field)).

## See also

- [Output schema](../prompts/output-schema.md): declare the shape of the answer in a `.skye` prompt.
- [Call a provider](call-a-provider.md) and [Streaming and async](streaming.md).
- [`skye.interfaces` API reference](../../reference/api/interfaces.md) (`OutputSchema`, `PromptParts`) and
  [`skye.models` API reference](../../reference/api/models.md).
- Examples: [`advanced/structured_output.py`](https://github.com/ggiallo28/skye/blob/main/examples/advanced/structured_output.py),
  [`providers/structured_output_example.py`](https://github.com/ggiallo28/skye/blob/main/examples/providers/structured_output_example.py).
