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
from nimbus import CompletionRequest, UserMessage
from nimbus.providers.bedrock import BedrockModel

# Initialize model
model = BedrockModel(model_id="anthropic.claude-3-sonnet")

# Create request
request = CompletionRequest(
    messages=[UserMessage(content="Hello, world!")],
    model="claude-3-sonnet",
    temperature=0.7
)

# Get response
response = model.complete(request)
print(response.content)
```

### Async Usage

```python
import asyncio
from nimbus import CompletionRequest, UserMessage
from nimbus.providers.openai import OpenAIModel

async def main():
    model = OpenAIModel(api_key="your-api-key")
    
    request = CompletionRequest(
        messages=[UserMessage(content="Explain async/await")],
        model="gpt-4"
    )
    
    response = await model.acomplete(request)
    print(response.content)

asyncio.run(main())
```

### Streaming

```python
from nimbus import CompletionRequest, UserMessage
from nimbus.providers.openai import OpenAIModel

model = OpenAIModel(api_key="your-api-key")

request = CompletionRequest(
    messages=[UserMessage(content="Write a story")],
    model="gpt-4",
    stream=True
)

for chunk in model.stream(request):
    print(chunk.delta, end="", flush=True)
```

### Structured Outputs

```python
from pydantic import BaseModel
from nimbus import CompletionRequest, UserMessage
from nimbus.providers.openai import OpenAIModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

model = OpenAIModel(api_key="your-api-key")

request = CompletionRequest(
    messages=[UserMessage(content="Extract: John is 30 and works as an engineer")],
    model="gpt-4",
    response_schema=Person
)

response = model.complete(request)
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
from nimbus import CompletionRequest, UserMessage
from nimbus.providers import ProviderRegistry

# Get provider from registry
provider = ProviderRegistry.get_model_provider(
    "openai",
    api_key="sk-..."
)

request = CompletionRequest(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"
)

response = provider.complete(request)
print(response.content)
```

#### Anthropic

```python
from nimbus import CompletionRequest, UserMessage
from nimbus.providers import ProviderRegistry

provider = ProviderRegistry.get_model_provider(
    "anthropic",
    api_key="sk-ant-..."
)

request = CompletionRequest(
    messages=[UserMessage(content="Hello!")],
    model="claude-3-sonnet"
)

response = provider.complete(request)
```

#### AWS Bedrock

```python
from nimbus import CompletionRequest, UserMessage
from nimbus.providers import ProviderRegistry

# Works with or without boto3 installed
# In AWS Lambda, boto3 is pre-installed
provider = ProviderRegistry.get_model_provider(
    "bedrock",
    region_name="us-east-1"
)

request = CompletionRequest(
    messages=[UserMessage(content="Hello!")],
    model="anthropic.claude-3-sonnet"
)

response = provider.complete(request)
```

#### Azure OpenAI

```python
from nimbus import CompletionRequest, UserMessage
from nimbus.providers import ProviderRegistry

provider = ProviderRegistry.get_model_provider(
    "azure",
    azure_endpoint="https://your-resource.openai.azure.com/",
    api_key="your-api-key",
    api_version="2024-02-15-preview",
    deployment_name="gpt-4"
)

request = CompletionRequest(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"
)

response = provider.complete(request)
```

#### Google Vertex AI

```python
from nimbus import CompletionRequest, UserMessage
from nimbus.providers import ProviderRegistry

provider = ProviderRegistry.get_model_provider(
    "vertex",
    project_id="your-project",
    location="us-central1"
)

request = CompletionRequest(
    messages=[UserMessage(content="Hello!")],
    model="gemini-pro"
)

response = provider.complete(request)
```

### Embedding Providers

```python
from nimbus.providers import ProviderRegistry

# OpenAI embeddings
embedding_provider = ProviderRegistry.get_embedding_provider(
    "openai",
    model="text-embedding-3-small",
    api_key="sk-..."
)

embeddings = embedding_provider.encode_batch([
    "Hello world",
    "Goodbye world"
])

# Bedrock embeddings
embedding_provider = ProviderRegistry.get_embedding_provider(
    "bedrock",
    model="amazon.titan-embed-text-v1",
    region_name="us-east-1"
)

embeddings = embedding_provider.encode_batch(["Hello world"])

# Cohere embeddings
embedding_provider = ProviderRegistry.get_embedding_provider(
    "cohere",
    model="embed-english-v3.0",
    api_key="..."
)

embeddings = embedding_provider.encode_batch(["Hello world"])
```

### Multimodal Inputs

```python
from nimbus import CompletionRequest, UserMessage
from nimbus.providers import ProviderRegistry

provider = ProviderRegistry.get_model_provider("openai", api_key="sk-...")

# Image from URL
request = CompletionRequest(
    messages=[
        UserMessage(
            content="What's in this image?",
            images=["https://example.com/image.jpg"]
        )
    ],
    model="gpt-4-vision"
)

response = provider.complete(request)

# Image from file path
request = CompletionRequest(
    messages=[
        UserMessage(
            content="Describe this image",
            images=["/path/to/image.png"]
        )
    ],
    model="gpt-4-vision"
)

response = provider.complete(request)

# Image from base64
import base64
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

request = CompletionRequest(
    messages=[
        UserMessage(
            content="What's in this image?",
            images=[f"data:image/jpeg;base64,{image_data}"]
        )
    ],
    model="gpt-4-vision"
)

response = provider.complete(request)
```

### Structured Outputs

```python
from pydantic import BaseModel
from nimbus import CompletionRequest, UserMessage
from nimbus.providers import ProviderRegistry

class Person(BaseModel):
    name: str
    age: int
    occupation: str

provider = ProviderRegistry.get_model_provider("openai", api_key="sk-...")

request = CompletionRequest(
    messages=[
        UserMessage(content="Extract: John is 30 and works as an engineer")
    ],
    model="gpt-4",
    response_schema=Person
)

response = provider.complete(request)
person = response.structured_output
print(f"{person.name} is {person.age} years old")
```

### Function Calling

```python
from nimbus import CompletionRequest, UserMessage, CapabilityMessage
from nimbus.providers import ProviderRegistry

provider = ProviderRegistry.get_model_provider("openai", api_key="sk-...")

# Define capabilities
capabilities = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

request = CompletionRequest(
    messages=[
        UserMessage(content="What's the weather in San Francisco?")
    ],
    model="gpt-4",
    capabilities=capabilities
)

response = provider.complete(request)

# Check if model called a function
if response.capability_calls:
    for call in response.capability_calls:
        print(f"Called: {call['function']['name']}")
        print(f"Args: {call['function']['arguments']}")
        
        # Execute the function and send result back
        if call['function']['name'] == 'get_weather':
            result = get_weather(call['function']['arguments']['location'])
            
            # Continue conversation with result
            request = CompletionRequest(
                messages=[
                    UserMessage(content="What's the weather in San Francisco?"),
                    response.to_message(),  # Assistant's response with function call
                    CapabilityMessage(
                        content=result,
                        capability_id=call['id'],
                        capability_name=call['function']['name']
                    )
                ],
                model="gpt-4"
            )
            
            final_response = provider.complete(request)
            print(final_response.content)
```

### Streaming

```python
from nimbus import CompletionRequest, UserMessage
from nimbus.providers import ProviderRegistry

provider = ProviderRegistry.get_model_provider("openai", api_key="sk-...")

request = CompletionRequest(
    messages=[UserMessage(content="Write a story")],
    model="gpt-4",
    stream=True
)

for chunk in provider.stream(request):
    print(chunk.delta, end="", flush=True)
```

### Async Operations

```python
import asyncio
from nimbus import CompletionRequest, UserMessage
from nimbus.providers import ProviderRegistry

async def main():
    provider = ProviderRegistry.get_model_provider("openai", api_key="sk-...")
    
    request = CompletionRequest(
        messages=[UserMessage(content="Hello!")],
        model="gpt-4"
    )
    
    response = await provider.acomplete(request)
    print(response.content)

asyncio.run(main())
```

### Lazy Loading and Optional Dependencies

Nimbus uses lazy loading to defer importing provider SDKs until they're actually used. This means:

1. **Minimal startup overhead**: Only import what you use
2. **Optional dependencies**: Install only the providers you need
3. **Lambda-friendly**: Bedrock works in AWS Lambda without boto3 as a dependency (it's pre-installed)

```python
# This doesn't import OpenAI SDK until you actually use it
provider = ProviderRegistry.get_model_provider("openai", api_key="sk-...")

# SDK is imported here when complete() is called
response = provider.complete(request)
```

Check which providers are available:

```python
from nimbus.providers import ProviderRegistry

print("Available LLM providers:", ProviderRegistry.list_model_providers())
print("Available embedding providers:", ProviderRegistry.list_embedding_providers())
```

### AWS Lambda Deployment

Nimbus is Lambda-friendly:

```python
# In AWS Lambda, boto3 is pre-installed
# No need to include it in your deployment package
from nimbus.providers import ProviderRegistry

def lambda_handler(event, context):
    # Bedrock provider works without boto3 in dependencies
    provider = ProviderRegistry.get_model_provider(
        "bedrock",
        region_name="us-east-1"
    )
    
    from nimbus import CompletionRequest, UserMessage
    request = CompletionRequest(
        messages=[UserMessage(content=event['prompt'])],
        model="anthropic.claude-3-sonnet"
    )
    
    response = provider.complete(request)
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
from nimbus import CompletionRequest, CompletionResponse

class ModelInterface(ABC):
    @abstractmethod
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a synchronous completion request."""
        pass
    
    @abstractmethod
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute an asynchronous completion request."""
        pass
    
    @abstractmethod
    def stream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
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
from nimbus import ModelRouterInterface, RoutingStrategy, ModelConfig

router = ModelRouter()

# Register multiple models
router.register_model(ModelConfig(
    model_id="gpt-4-primary",
    provider="openai",
    weight=2.0,
    priority=1
))

router.register_model(ModelConfig(
    model_id="gpt-4-fallback",
    provider="openai",
    weight=1.0,
    priority=2
))

# Set routing strategy
router.set_routing_strategy(RoutingStrategy.WEIGHTED)

# Route requests automatically
response = router.route_request(request)
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
