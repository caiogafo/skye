# Nimbus

**Modular GenAI library with optional extras**

Nimbus provides a foundational layer for building AI agents and intelligent applications with a Clean Architecture approach. The base package includes only interfaces and models, while all implementations are available as optional extras.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🎯 **Provider-agnostic** - Unified interface for OpenAI, Anthropic, AWS Bedrock, Azure, and more
- 🧩 **Modular architecture** - Install only what you need via optional extras
- 🔒 **Type-safe** - Complete type hints with Pydantic validation
- ⚡ **Async-first** - Both sync and async APIs throughout
- 🔄 **Load balancing** - Multiple routing strategies with automatic fallbacks
- 📊 **Observability** - Built-in telemetry, logging, and tracing
- 🛡️ **Safety filters** - Input/output validation and moderation
- 💾 **Memory systems** - Episodic and semantic memory support

## Installation

### Base Package (Interfaces + Models)

```bash
pip install nimbus
```

Or with uv:

```bash
uv pip install nimbus
```

### With Optional Extras

```bash
# Single provider
pip install nimbus[bedrock]
uv pip install nimbus[bedrock]

# Multiple extras
pip install nimbus[bedrock,agents,memory]
uv pip install nimbus[bedrock,agents,memory]

# Everything
pip install nimbus[all]
uv pip install nimbus[all]
```

### Available Extras

| Extra | Description | Dependencies |
|-------|-------------|--------------|
| `bedrock` | AWS Bedrock provider | boto3 |
| `openai` | OpenAI provider | openai |
| `anthropic` | Anthropic provider | anthropic |
| `azure` | Azure OpenAI provider | azure-ai-inference |
| `agents` | Agent runtime | - |
| `prompts` | Prompt management | - |
| `tools` | Capability/tool registry | - |
| `memory` | Persistent memory | redis, psycopg2 |
| `guard` | Safety filters | - |
| `observe` | Observability | opentelemetry, prometheus |
| `all` | All components | All of the above |

## Quick Start

### Basic Usage

```python
import nimbus
from nimbus.messages import UserMessage

# Create provider client (boto3-style)
client = nimbus.provider("bedrock", region="us-east-1")

# Make completion request
response = client.complete(
    messages=[UserMessage(content="Hello, world!")],
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    temperature=0.7
)

print(response.content)
```

### Async Usage

```python
import asyncio
import nimbus
from nimbus.messages import UserMessage

async def main():
    client = nimbus.provider("openai", api_key="sk-...")
    
    response = await client.acomplete(
        messages=[UserMessage(content="Explain async/await")],
        model="gpt-4"
    )
    
    print(response.content)

asyncio.run(main())
```

### Streaming

```python
import nimbus
from nimbus.messages import UserMessage

client = nimbus.provider("openai", api_key="sk-...")

for chunk in client.stream(
    messages=[UserMessage(content="Write a story")],
    model="gpt-4"
):
    print(chunk.delta, end="", flush=True)
```

### Structured Outputs

```python
from pydantic import BaseModel
import nimbus
from nimbus.messages import UserMessage

class Person(BaseModel):
    name: str
    age: int
    occupation: str

client = nimbus.provider("openai", api_key="sk-...")

response = client.complete(
    messages=[UserMessage(content="Extract: John is 30 and works as an engineer")],
    model="gpt-4",
    response_schema=Person
)

person = response.structured_output  # Returns Person instance
print(f"{person.name} is {person.age} years old")
```

## Provider Guide

### Installation by Provider

Each provider is available as an optional extra:

```bash
# OpenAI
pip install nimbus[openai]

# Anthropic
pip install nimbus[anthropic]

# AWS Bedrock
pip install nimbus[bedrock]

# Azure OpenAI
pip install nimbus[azure]

# Google Vertex AI
pip install nimbus[vertex]

# Cohere (embeddings)
pip install nimbus[cohere]

# All providers
pip install nimbus[all-providers]
```

### LLM Providers

#### OpenAI

```python
import nimbus
from nimbus.messages import UserMessage

# Create provider client
client = nimbus.provider("openai", api_key="sk-...")

# Make completion request
response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"
)

print(response.content)
```

#### Anthropic

```python
import nimbus
from nimbus.messages import UserMessage

client = nimbus.provider("anthropic", api_key="sk-ant-...")

response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="claude-3-sonnet-20240229"
)
```

#### AWS Bedrock

```python
import nimbus
from nimbus.messages import UserMessage

# Works with or without boto3 installed
# In AWS Lambda, boto3 is pre-installed
client = nimbus.provider("bedrock", region="us-east-1")

response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="anthropic.claude-3-sonnet-20240229-v1:0"
)
```

#### Azure OpenAI

```python
import nimbus
from nimbus.messages import UserMessage

client = nimbus.provider(
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

#### Google Vertex AI

```python
import nimbus
from nimbus.messages import UserMessage

client = nimbus.provider(
    "vertex",
    project_id="your-project",
    location="us-central1"
)

response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="gemini-1.5-pro"
)
```

### Embedding Providers

```python
import nimbus

# OpenAI embeddings
embedder = nimbus.provider(
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
embedder = nimbus.provider(
    "bedrock",
    model="amazon.titan-embed-text-v1",
    region="us-east-1",
    provider_type="embedding"
)

embeddings = embedder.encode_batch(["Hello world"])

# Vertex AI embeddings
embedder = nimbus.provider(
    "vertex",
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

### Multimodal Inputs

```python
import nimbus
from nimbus.messages import UserMessage

client = nimbus.provider("openai", api_key="sk-...")

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

### Structured Outputs

```python
from pydantic import BaseModel
import nimbus
from nimbus.messages import UserMessage

class Person(BaseModel):
    name: str
    age: int
    occupation: str

client = nimbus.provider("openai", api_key="sk-...")

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

### Function Calling (Capabilities)

```python
import nimbus
from nimbus.messages import UserMessage, CapabilityMessage
from nimbus.capabilities import capability

# Define capability using decorator
@capability
def get_weather(location: str) -> str:
    """Get weather for a location.
    
    Args:
        location: The city or location to get weather for
    """
    # Your implementation here
    return f"Weather in {location}: Sunny, 72°F"

client = nimbus.provider("openai", api_key="sk-...")

response = client.complete(
    messages=[
        UserMessage(content="What's the weather in San Francisco?")
    ],
    model="gpt-4",
    capabilities=[get_weather]
)

# Check if model called a function
if response.capability_calls:
    for call in response.capability_calls:
        print(f"Called: {call.name}")
        print(f"Args: {call.arguments}")
        
        # Execute the capability
        result = get_weather.execute(**call.arguments)
        
        # Continue conversation with result
        final_response = client.complete(
            messages=[
                UserMessage(content="What's the weather in San Francisco?"),
                response.to_message(),  # Assistant's response with function call
                CapabilityMessage(
                    content=result,
                    capability_id=call.id,
                    capability_name=call.name
                )
            ],
            model="gpt-4"
        )
        
        print(final_response.content)
```

### Streaming

```python
import nimbus
from nimbus.messages import UserMessage

client = nimbus.provider("openai", api_key="sk-...")

for chunk in client.stream(
    messages=[UserMessage(content="Write a story")],
    model="gpt-4"
):
    print(chunk.delta, end="", flush=True)
```

### Async Operations

```python
import asyncio
import nimbus
from nimbus.messages import UserMessage

async def main():
    client = nimbus.provider("openai", api_key="sk-...")
    
    response = await client.acomplete(
        messages=[UserMessage(content="Hello!")],
        model="gpt-4"
    )
    
    print(response.content)

asyncio.run(main())
```

### Lazy Loading and Optional Dependencies

Nimbus uses lazy loading to defer importing provider SDKs until they're actually used. This means:

1. **Minimal startup overhead**: Only import what you use
2. **Optional dependencies**: Install only the providers you need
3. **Lambda-friendly**: Bedrock works in AWS Lambda without boto3 as a dependency (it's pre-installed)

```python
import nimbus

# This doesn't import OpenAI SDK until you actually use it
client = nimbus.provider("openai", api_key="sk-...")

# SDK is imported here when complete() is called
response = client.complete(
    messages=[...],
    model="gpt-4"
)
```

### AWS Lambda Deployment

Nimbus is Lambda-friendly:

```python
# In AWS Lambda, boto3 is pre-installed
# No need to include it in your deployment package
import nimbus
from nimbus.messages import UserMessage

def lambda_handler(event, context):
    # Bedrock provider works without boto3 in dependencies
    client = nimbus.provider("bedrock", region="us-east-1")
    
    response = client.complete(
        messages=[UserMessage(content=event['prompt'])],
        model="anthropic.claude-3-sonnet-20240229-v1:0"
    )
    
    return {"response": response.content}
```

### Configuration

Nimbus supports multiple configuration sources with precedence: code > environment > file.

#### Environment Variables

```bash
export NIMBUS_LOG_LEVEL=INFO
export NIMBUS_OPENAI_API_KEY=sk-...
export NIMBUS_ENABLE_TELEMETRY=true
```

#### Configuration File

```yaml
# nimbus.yaml
log_level: INFO
enable_telemetry: true

models:
  gpt-4:
    provider: openai
    api_key: ${OPENAI_API_KEY}
    temperature: 0.7
    max_tokens: 2000
    rate_limits:
      requests_per_minute: 60
      tokens_per_minute: 90000
```

#### Load Configuration

```python
from pathlib import Path
from nimbus import ConfigLoader

config = ConfigLoader.load(
    config_path=Path("nimbus.yaml"),
    overrides={"log_level": "DEBUG"}
)
```

## Architecture

Nimbus follows Clean Architecture principles with a stable core of interfaces:

```
┌─────────────────────────────────────────┐
│         nimbus (base package)           │
│  ┌───────────────────────────────────┐  │
│  │   Interfaces & Contracts          │  │
│  │   - ModelInterface                │  │
│  │   - CapabilityInterface           │  │
│  │   - MemoryInterface               │  │
│  │   - SafetyFilterInterface         │  │
│  │   - ObserverInterface             │  │
│  │   - And more...                   │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Data Models (Pydantic)          │  │
│  │   - CompletionRequest/Response    │  │
│  │   - UserMessage, AssistantMessage │  │
│  │   - ModelConfig, NimbusConfig     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                  ▲
                  │ depends on
                  │
    ┌─────────────┴─────────────┐
    │   Optional Extras         │
    │   - providers/            │
    │   - agents/               │
    │   - memory/               │
    │   - tools/                │
    └───────────────────────────┘
```

## Core Interfaces

### ModelInterface

Unified interface for all LLM providers:

```python
from abc import ABC, abstractmethod
from typing import Iterator
from nimbus import CompletionResponse, StreamChunk
from nimbus.messages import NimbusMessage

class ModelInterface(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[NimbusMessage],
        model: str,
        **kwargs
    ) -> CompletionResponse:
        """Execute a synchronous completion request."""
        pass
    
    @abstractmethod
    async def acomplete(
        self,
        messages: list[NimbusMessage],
        model: str,
        **kwargs
    ) -> CompletionResponse:
        """Execute an asynchronous completion request."""
        pass
    
    @abstractmethod
    def stream(
        self,
        messages: list[NimbusMessage],
        model: str,
        **kwargs
    ) -> Iterator[StreamChunk]:
        """Execute a streaming completion request."""
        pass
```

### CapabilityInterface

Define tools/functions that agents can use:

```python
from nimbus import CapabilityInterface, CapabilitySchema

class WebSearchCapability(CapabilityInterface):
    def get_schema(self) -> CapabilitySchema:
        return CapabilitySchema(
            name="web_search",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
    
    def execute(self, query: str) -> str:
        # Implementation
        return search_results
```

### MemoryInterface

Store and retrieve agent memories:

```python
from nimbus import MemoryInterface, MemoryEntry

class MyMemory(MemoryInterface):
    def store(self, entry: MemoryEntry) -> str:
        # Store memory and return ID
        pass
    
    def retrieve(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        # Retrieve relevant memories
        pass
```

## Advanced Features

### Load Balancing and Routing

```python
import nimbus
from nimbus.messages import UserMessage
from nimbus.routes import ModelRouter, ModelTarget, RouteConfig
from nimbus.interfaces.router import RoutingStrategy

# Create router with multiple targets for an alias
router = ModelRouter(routes=[
    RouteConfig(
        alias="gpt-4",  # Use this alias as the model name
        targets=[
            ModelTarget(
                model="gpt-4",
                provider="openai",
                api_key="${OPENAI_API_KEY}",
                tpm=100000,
                rpm=1000,
                weight=2.0
            ),
            ModelTarget(
                model="azure/gpt-4",
                provider="azure",
                api_key="${AZURE_API_KEY}",
                api_base="${AZURE_API_BASE}",
                tpm=80000,
                rpm=800,
                weight=1.0
            )
        ],
        strategy=RoutingStrategy.WEIGHTED
    )
])

# Create provider with router
client = nimbus.provider("openai", router=router)

# Use the alias as the model name - router handles load balancing
response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"  # This is the alias, router picks the best target
)
```

### Rate Limiting

```python
from nimbus import ModelConfig, RateLimitConfig

config = ModelConfig(
    model_id="gpt-4",
    provider="openai",
    rate_limits=RateLimitConfig(
        requests_per_minute=60,
        tokens_per_minute=90000,
        requests_per_day=1000
    )
)
```

### Fallbacks and Cooldowns

```python
from nimbus import ModelConfig, CooldownConfig

config = ModelConfig(
    model_id="primary-model",
    provider="openai",
    fallback_models=["backup-model-1", "backup-model-2"],
    cooldown_config=CooldownConfig(
        enabled=True,
        allowed_fails_per_minute=3,
        cooldown_duration_seconds=60
    )
)
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/your-org/nimbus.git
cd nimbus

# Install with dev dependencies
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/nimbus --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_completion.py -v
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type check
uv run mypy src/nimbus --strict

# Run all checks
make check
```

## Documentation

For detailed documentation, see:

- [Architecture Guidelines](.kiro/steering/nimbus-architecture.md)
- [Python Standards](.kiro/steering/python-standards.md)
- [Design Document](.kiro/specs/nimbus/design.md)
- [Requirements](.kiro/specs/nimbus/requirements.md)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run code quality checks
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/nimbus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/nimbus/discussions)
- **Documentation**: [Full Documentation](https://nimbus.readthedocs.io)

## Roadmap

- [x] Core interfaces and models
- [x] Configuration system
- [x] Exception hierarchy
- [ ] Provider implementations (OpenAI, Anthropic, Bedrock)
- [ ] Agent runtime
- [ ] Memory systems
- [ ] Prompt management
- [ ] Safety filters
- [ ] Observability integration

## Acknowledgments

Nimbus is inspired by:
- **LangChain** - For pioneering LLM application frameworks
- **LiteLLM** - For provider abstraction patterns
- **Clean Architecture** - For architectural principles
- **Pydantic** - For data validation and settings management
