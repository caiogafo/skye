# Basic Examples

This directory contains basic examples demonstrating core Skye concepts.

## Examples

All of them create the client with one call, `skye.provider(name, **config)`, in the style of `boto3.client`.

### `quickstart.py`
Create a client and ask a question.

### `async_and_streaming.py`
`acomplete` (async) and `stream` (chunks as the model writes them).

### `configuration.py`
Configuration from a file, the environment and code, in that order of precedence; `${VAR}` substitution; the three prefixed environment variables.

### `simple_completion.py`
Completion requests with different message types, token usage, structured outputs and several providers.

## Running the Examples

```bash
# Run basic completion example
python examples/basic/quickstart.py

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
