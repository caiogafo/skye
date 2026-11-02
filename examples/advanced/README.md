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
Requesting structured outputs with Pydantic schemas.

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
- Complex capability schemas
- Parallel capability execution
- Capability result handling
- Error handling in capabilities

### `streaming.py`
Streaming responses and handling tokens in real-time.

**Topics covered:**
- Streaming completions
- Token-by-token processing
- Streaming with capabilities
- Async streaming

### `prompt_engineering.py`
Advanced prompt engineering techniques.

**Topics covered:**
- Few-shot learning
- Chain-of-thought prompting
- Prompt templates
- Dynamic prompt generation

### `custom_providers.py`
Implementing custom model providers.

**Topics covered:**
- Extending ModelInterface
- Custom transformation logic
- Provider registration
- Error handling

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

### Multimodal Processing

```python
from skye.base.messages import UserMessage

message = UserMessage(
    content=[
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
    ]
)
```

### Structured Outputs

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

request = CompletionRequest(
    messages=[...],
    model="gpt-4",
    response_schema=Person
)
```

### Streaming

```python
request = CompletionRequest(
    messages=[...],
    model="gpt-4",
    stream=True
)

for chunk in provider.stream(request):
    print(chunk.delta, end="", flush=True)
```

### Async Operations

```python
import asyncio

async def main():
    response = await provider.acomplete(request)
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
from skye.base.exceptions import SkyeError, RateLimitError

try:
    response = provider.complete(request)
except RateLimitError as e:
    print(f"Rate limited: {e}")
except SkyeError as e:
    print(f"Error: {e}")
```

## Next Steps

- Explore the Skye documentation
- Check out the provider-specific examples
- Implement custom providers for your use case
- Contribute examples back to the community
