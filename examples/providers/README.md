# Skye Provider Examples

This directory contains examples demonstrating the simplified boto3-style API for Skye providers.

## Quick Start

```python
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage, SystemMessage

# Create a client
client = create_provider("openai", api_key="sk-...")

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
client = create_provider("openai", api_key="sk-...")
response = client.complete(
    messages=[UserMessage("Hello")],
    model="gpt-4",
    temperature=0.7
)
```

**Installation:** `pip install skyeai[openai]`

### AWS Bedrock

```python
client = create_provider("bedrock", region="us-east-1")
response = client.complete(
    messages=[UserMessage("Hello")],
    model="anthropic.claude-3-sonnet-20240229-v1:0"
)
```

**Installation:** `pip install skyeai[bedrock]`

### Anthropic

```python
client = create_provider("anthropic", api_key="sk-ant-...")
response = client.complete(
    messages=[UserMessage("Hello")],
    model="claude-3-sonnet-20240229"
)
```

**Installation:** `pip install skyeai[anthropic]`

### Azure OpenAI

```python
client = create_provider(
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

**Installation:** `pip install skyeai[azure]`

### Google

```python
client = create_provider(
    "google",
    project_id="your-project-id",
    location="us-central1"
)
response = client.complete(
    messages=[UserMessage("Hello")],
    model="gemini-1.5-pro"
)
```

**Installation:** `pip install skyeai[google]`

## API Reference

### Creating a Client

```python
client = create_provider(name, **config)
```

- `name`: Provider name ("openai", "bedrock", "anthropic", "azure", "google")
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
- `messages`: List of `SkyeMessage` objects or a string
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
from skye.base.messages import UserMessage, SystemMessage, AssistantMessage

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
- `google_example.py` - Google Gemini models

## Running Examples

```bash
# Set your API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export AWS_PROFILE="your-profile"

# Run an example
python examples/providers/openai_example.py
```
