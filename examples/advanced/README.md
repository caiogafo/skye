# Advanced Examples

This directory contains advanced examples demonstrating complex patterns and features.

## Examples

### `multimodal.py`
Working with multimodal inputs (text, images, audio, video).

**Topics covered:**
- Image inputs with URLs and base64
- Audio and video processing
- Mixed content in messages
- Provider-specific multimodal support

### `structured_output.py`
Requesting structured outputs with declared schemas (nested objects, enums, optional fields) and validating the answer.

**Topics covered:**
- Defining output schemas
- Nested schemas
- Field validation
- Type-safe responses
- Enum fields
- Optional fields

### `function_calling.py`
Advanced function calling patterns.

**Topics covered:**
- Several capabilities defined with `@capability`
- Executing the calls the model asks for (`execute_capability_calls`)
- Capability result messages and the follow-up call
- A capability that raises: the error goes back to the model

### `streaming.py`
Streaming responses and handling tokens in real-time.

**Topics covered:**
- Streaming completions with `stream`
- Token-by-token processing and time to first token
- Async streaming with `astream`

### `prompt_engineering.py`
Advanced prompt engineering techniques.

**Topics covered:**
- Few-shot learning with an example template
- Chain-of-thought prompting with system and user messages
- Template composition
- Dynamic prompts: callable defaults and custom filters

### `custom_providers.py`
Implementing custom model providers.

**Topics covered:**
- Extending `BaseModelProvider`
- The transformation of a request and of an answer
- Provider registration, then `skye.provider("name")`
- Errors of the library (a lighter option, a `Runnable`, is in `examples/providers/bring_your_own_adapter.py`)

## Running the Examples

```bash
# Run multimodal example
python examples/advanced/multimodal.py

# Run structured output example
python examples/advanced/structured_output.py

# Run function calling example
python examples/advanced/function_calling.py

# Run streaming example
python examples/advanced/streaming.py

# Run prompt engineering example
python examples/advanced/prompt_engineering.py

# Run custom providers example
python examples/advanced/custom_providers.py
```

## Key Concepts

All of them create the client with one call, `skye.provider(name, **config)`.

### Multimodal Processing

```python
from skye.base.messages import UserMessage

message = UserMessage(content="What's in this image?", images=["https://example.com/image.jpg"])
response = client.complete(messages=[message], model="gpt-4o")
```

### Structured Outputs

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

response = client.complete(messages=[...], model="gpt-4", response_schema=Person)
person = response.structured_output  # a Person; a non-conforming answer raises ValidationError
```

### Streaming

```python
for chunk in client.stream(messages=[...], model="gpt-4"):
    print(chunk.delta, end="", flush=True)
```

### Async Operations

```python
import asyncio

async def main():
    response = await client.acomplete(messages=[...], model="gpt-4")
    print(response.content)

asyncio.run(main())
```

## Performance Tips

1. **Batch Requests**: Use batch APIs when available
2. **Caching**: Cache responses for repeated queries
3. **Streaming**: Use streaming for long responses
4. **Async**: Use async for concurrent requests
5. **Rate Limiting**: Respect provider rate limits

## Error Handling

```python
from skye.base.exceptions import ProviderError, SkyeError, ValidationError

try:
    response = client.complete(messages=[...], model="gpt-4")
except ValidationError as e:
    print(f"The answer did not match the schema: {e}")
except ProviderError as e:
    print(f"The provider failed: {e}")
except SkyeError as e:
    print(f"Error: {e}")
```

## Next Steps

- Explore the Skye documentation
- Check out the provider-specific examples
- Implement custom providers for your use case
- Contribute examples back to the community
