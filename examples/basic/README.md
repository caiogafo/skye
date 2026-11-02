# Basic Examples

This directory contains basic examples demonstrating core Skye concepts.

## Examples

### `simple_completion.py`
Basic completion request with different message types and token usage tracking.

**Topics covered:**
- Creating completion requests
- Using different message types (UserMessage, AssistantMessage, SystemMessage)
- Handling token usage
- Structured outputs
- Prompt templates

### `streaming_example.py`
Streaming responses from language models.

**Topics covered:**
- Streaming completions
- Handling stream chunks
- Real-time token counting
- Async streaming

## Running the Examples

```bash
# Run basic completion example
python examples/basic/simple_completion.py

# Run streaming example
python examples/basic/streaming_example.py
```

## Key Concepts

- **CompletionRequest**: The main request object for LLM calls
- **SkyeMessage**: Base message class with UserMessage, AssistantMessage, SystemMessage
- **CompletionResponse**: Response from the model with content and metadata
- **TokenUsage**: Tracks prompt, completion, and total tokens used
- **Streaming**: Real-time token-by-token responses

## Next Steps

After understanding basic usage, explore:
- `examples/capabilities/` - Using capabilities (tools/functions)
- `examples/providers/` - Provider-specific features
- `examples/routing/` - Load balancing and routing
- `examples/advanced/` - Advanced patterns
