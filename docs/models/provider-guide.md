---
title: "Provider guide"
status: current
last_updated: 2026-11-02
---

# Provider Guide

## Installation by Provider

Each provider is available as an optional extra:

```bash
# OpenAI
pip install skyeai[openai]

# Anthropic
pip install skyeai[anthropic]

# AWS Bedrock
pip install skyeai[bedrock]

# Azure OpenAI (served by the openai extra)
pip install skyeai[openai]

# Google
pip install skyeai[google]

# Cohere (embeddings)
pip install skyeai[cohere]

# All providers
pip install skyeai[all-providers]
```

## LLM Providers

### OpenAI

```python
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage

# Create provider client
client = create_provider("openai", api_key="sk-...")

# Make completion request
response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"
)

print(response.content)
```

### Anthropic

```python
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage

client = create_provider("anthropic", api_key="sk-ant-...")

response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="claude-3-sonnet-20240229"
)
```

### AWS Bedrock

```python
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage

# Works with or without boto3 installed
# In AWS Lambda, boto3 is pre-installed
client = create_provider("bedrock", region="us-east-1")

response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="anthropic.claude-3-sonnet-20240229-v1:0"
)
```

### Azure OpenAI

```python
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage

client = create_provider(
    "azure",
    azure_endpoint="https://your-resource.openai.azure.com/",
    api_key="your-api-key",
    api_version="2024-02-15-preview"
)

response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"  # Your deployment name
)
```

### Google

```python
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage

client = create_provider(
    "google",
    project_id="your-project",
    location="us-central1"
)

response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="gemini-1.5-pro"
)
```

## Embedding Providers

```python
from skye.models.registry import provider as create_provider

# OpenAI embeddings
embedder = create_provider(
    "openai",
    model="text-embedding-3-small",
    api_key="sk-...",
    provider_type="embedding"
)

embeddings = embedder.encode_batch([
    "Hello world",
    "Goodbye world"
])

# Get vector dimension
print(f"Dimension: {embedder.get_vector_dimension()}")

# Bedrock embeddings
embedder = create_provider(
    "bedrock",
    model="amazon.titan-embed-text-v1",
    region="us-east-1",
    provider_type="embedding"
)

embeddings = embedder.encode_batch(["Hello world"])

# Google embeddings
embedder = create_provider(
    "google",
    model="textembedding-gecko@003",
    project_id="my-project",
    location="us-central1",
    provider_type="embedding"
)

embeddings = embedder.encode_batch(["Hello world"])

# Single text encoding
embedding = embedder.encode("Single text")

# Async encoding
embeddings = await embedder.aencode_batch(["text1", "text2"])
```

## Multimodal Inputs

```python
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage

client = create_provider("openai", api_key="sk-...")

# Image from URL
response = client.complete(
    messages=[
        UserMessage(
            content="What's in this image?",
            images=["https://example.com/image.jpg"]
        )
    ],
    model="gpt-4-vision-preview"
)

# Image from file path
response = client.complete(
    messages=[
        UserMessage(
            content="Describe this image",
            images=["/path/to/image.png"]
        )
    ],
    model="gpt-4-vision"
)

# Image from base64
import base64
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = client.complete(
    messages=[
        UserMessage(
            content="What's in this image?",
            images=[f"data:image/jpeg;base64,{image_data}"]
        )
    ],
    model="gpt-4-vision"
)
```

## Structured Outputs

```python
from pydantic import BaseModel
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage

class Person(BaseModel):
    name: str
    age: int
    occupation: str

client = create_provider("openai", api_key="sk-...")

response = client.complete(
    messages=[
        UserMessage(content="Extract: John is 30 and works as an engineer")
    ],
    model="gpt-4",
    response_schema=Person
)

person = response.structured_output
print(f"{person.name} is {person.age} years old")
```


## Streaming

```python
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage

client = create_provider("openai", api_key="sk-...")

for chunk in client.stream(
    messages=[UserMessage(content="Write a story")],
    model="gpt-4"
):
    print(chunk.delta, end="", flush=True)
```

## Async Operations

```python
import asyncio
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage

async def main():
    client = create_provider("openai", api_key="sk-...")
    
    response = await client.acomplete(
        messages=[UserMessage(content="Hello!")],
        model="gpt-4"
    )
    
    print(response.content)

asyncio.run(main())
```
