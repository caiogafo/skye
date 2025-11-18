# Nimbus Provider Examples

This directory contains examples demonstrating the simplified boto3-style API for Nimbus providers.

## Quick Start

```python
import nimbus
from nimbus.messages import UserMessage, SystemMessage

# Create a client
client = nimbus.provider("openai", api_key="sk-...")

# Simple completion
response = client.complete(
    messages=[UserMessage("What is AI?")],
    model="gpt-4"
)

print(response.content)
print(response.usage.total_tokens)
```

## Supported Providers

### OpenAI

```python
client = nimbus.provider("openai", api_key="sk-...")
response = client.complete(
    messages=[UserMessage("Hello")],
    model="gpt-4",
    temperature=0.7
)
```

**Installation:** `pip install nimbus[openai]`

### AWS Bedrock

```python
client = nimbus.provider("bedrock", region="us-east-1")
response = client.complete(
    messages=[UserMessage("Hello")],
    model="anthropic.claude-3-sonnet-20240229-v1:0"
)
```

**Installation:** `pip install nimbus[bedrock]`

### Anthropic

```python
client = nimbus.provider("anthropic", api_key="sk-ant-...")
response = client.complete(
    messages=[UserMessage("Hello")],
    model="claude-3-sonnet-20240229"
)
```

**Installation:** `pip install nimbus[anthropic]`

### Azure OpenAI

```python
client = nimbus.provider(
    "azure",
    api_key="...",
    azure_endpoint="https://your-resource.openai.azure.com",
    api_version="2024-02-15-preview"
)
response = client.complete(
    messages=[UserMessage("Hello")],
    model="gpt-4"  # Your deployment name
)
```

**Installation:** `pip install nimbus[azure]`

### Google Vertex AI

```python
client = nimbus.provider(
    "vertex",
    project_id="your-project-id",
    location="us-central1"
)
response = client.complete(
    messages=[UserMessage("Hello")],
    model="gemini-1.5-pro"
)
```

**Installation:** `pip install nimbus[vertex]`

## API Reference

### Creating a Client

```python
client = nimbus.provider(name, **config)
```

- `name`: Provider name ("openai", "bedrock", "anthropic", "azure", "vertex")
- `**config`: Provider-specific configuration

### Completion

```python
response = client.complete(
    messages=[...],
    model="...",
    temperature=0.7,
    max_tokens=100
)
```

**Parameters:**
- `messages`: List of `NimbusMessage` objects or a string
- `model`: Model identifier
- `temperature`: Sampling temperature (0.0-2.0)
- `max_tokens`: Maximum tokens to generate

**Returns:** `CompletionResponse` with:
- `response.content`: Generated text
- `response.model`: Model used
- `response.usage.total_tokens`: Total tokens used
- `response.finish_reason`: Finish reason

### Streaming

```python
for chunk in client.stream(messages=[...], model="..."):
    print(chunk.delta, end="", flush=True)
```

### Async Completion

```python
response = await client.acomplete(
    messages=[...],
    model="..."
)
```

## Message Types

```python
from nimbus.messages import UserMessage, SystemMessage, AssistantMessage

messages = [
    SystemMessage("You are a helpful assistant."),
    UserMessage("What is AI?"),
    AssistantMessage("AI stands for..."),
    UserMessage("Tell me more")
]
```

## Examples

- `bedrock_example.py` - AWS Bedrock with Claude and Titan models
- `openai_example.py` - OpenAI GPT models
- `anthropic_example.py` - Anthropic Claude models
- `azure_example.py` - Azure OpenAI deployments
- `vertex_example.py` - Google Vertex AI Gemini models

## Running Examples

```bash
# Set your API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export AWS_PROFILE="your-profile"

# Run an example
python examples/providers/openai_example.py
```
