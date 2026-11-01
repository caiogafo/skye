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
| `agents` | Agent runtime | - |
| `prompts` | Prompt management | - |
| `tools` | Capability/tool registry | none |
| `mcp` | MCP client | fastmcp (heavy: about 43 MB, 7 compiled) |
| `memory` | Persistent memory | redis, asyncpg |
| `guard` | Safety filters | - |
| `observe` | Observability | - (no telemetry library yet) |
| `all` | All components | All of the above |

## Quick Start

### Basic Usage

```python
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

# Create provider client (boto3-style)
client = create_provider("bedrock", region="us-east-1")

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
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

async def main():
    client = create_provider("openai", api_key="sk-...")
    
    response = await client.acomplete(
        messages=[UserMessage(content="Explain async/await")],
        model="gpt-4"
    )
    
    print(response.content)

asyncio.run(main())
```

### Streaming

```python
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

client = create_provider("openai", api_key="sk-...")

for chunk in client.stream(
    messages=[UserMessage(content="Write a story")],
    model="gpt-4"
):
    print(chunk.delta, end="", flush=True)
```

### Structured Outputs

```python
from pydantic import BaseModel
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

class Person(BaseModel):
    name: str
    age: int
    occupation: str

client = create_provider("openai", api_key="sk-...")

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

# Azure OpenAI (served by the openai extra)
pip install nimbus[openai]

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
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

# Create provider client
client = create_provider("openai", api_key="sk-...")

# Make completion request
response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"
)

print(response.content)
```

#### Anthropic

```python
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

client = create_provider("anthropic", api_key="sk-ant-...")

response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="claude-3-sonnet-20240229"
)
```

#### AWS Bedrock

```python
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

# Works with or without boto3 installed
# In AWS Lambda, boto3 is pre-installed
client = create_provider("bedrock", region="us-east-1")

response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="anthropic.claude-3-sonnet-20240229-v1:0"
)
```

#### Azure OpenAI

```python
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

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

#### Google Vertex AI

```python
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

client = create_provider(
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
from nimbus.models.registry import provider as create_provider

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

# Vertex AI embeddings
embedder = create_provider(
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
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

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

### Structured Outputs

```python
from pydantic import BaseModel
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

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

### Function Calling (Capabilities)

Nimbus supports two ways to provide capabilities to the LLM:

1. **Direct list** - Pass capabilities as an array (simple, no registry needed)
2. **CapabilityRegistry** - Pass a registry for search/discovery (advanced)

#### Option 1: Direct Capabilities (Recommended)

```python
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage
from nimbus.tools import capability

# Define capability using decorator
@capability
def get_weather(location: str) -> str:
    """Get weather for a location.
    
    Args:
        location: The city or location to get weather for
    """
    return f"Weather in {location}: Sunny, 72°F"

client = create_provider("openai", api_key="sk-...")

# Pass capabilities directly - no registry needed!
response = client.complete(
    messages=[UserMessage(content="What's the weather in San Francisco?")],
    model="gpt-4",
    capabilities=[get_weather]  # Direct list
)

# Check if model requested capability calls
if response.has_capability_calls():
    # Option 1: Execute automatically (no registry needed!)
    capability_messages = await response.execute_capability_calls()
    
    # Option 2: Execute individually with control
    capability_messages = []
    for capability in response.get_capability_calls():
        # Execute with LLM-provided arguments
        msg = capability.execute()
        
        # Or override specific arguments
        msg = capability.execute(location="New York")  # Override location
        
        capability_messages.append(msg)
    
    # Option 3: Execute with argument overrides
    overrides = {
        "call_123": {"units": "celsius"}  # Override specific call arguments
    }
    capability_messages = await response.execute_capability_calls(
        argument_overrides=overrides
    )
    
    # Continue conversation with results
    final_response = client.complete(
        messages=[
            UserMessage(content="What's the weather in San Francisco?"),
            response.to_message(),  # Assistant's response with capability calls
            *capability_messages    # Spread capability results as messages
        ],
        model="gpt-4"
    )
    
    print(final_response.content)
```

#### Option 2: CapabilityRegistry with Manual Search

Search for relevant tools and pass the results:

```python
from nimbus.tools import capability, CapabilityRegistry

# Define multiple capabilities
@capability
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    return f"Weather in {location}: Sunny, 72°F"

@capability
def get_forecast(location: str, days: int = 3) -> str:
    """Get weather forecast for multiple days."""
    return f"{days}-day forecast for {location}"

# Create registry with tools
registry = CapabilityRegistry(capabilities=[get_weather, get_forecast])

# Search for relevant tools
search_results = registry.search("weather forecast")
selected_tools = [cap for name, cap, score in search_results]

# Pass search results
response = client.complete(
    messages=[UserMessage(content="What's the weather like?")],
    model="gpt-4",
    capabilities=selected_tools  # Pass search results
)
```

#### Option 3: CapabilityRegistry with Automatic Search

Pass the registry directly - search happens automatically:

```python
# Create registry with tools
registry = CapabilityRegistry(capabilities=[get_weather, get_forecast])

# Pass registry - search happens automatically
response = client.complete(
    messages=[UserMessage(content="What's the weather like?")],
    model="gpt-4",
    capabilities=registry  # Registry enables automatic search
)
```

**When to use each approach:**
- **Direct list**: Simple use cases, fixed set of tools
- **Manual search**: You control which tools based on context
- **Automatic search**: Let the system find relevant tools dynamically

**Important**: In all cases, you can execute capabilities without the registry:
```python
if response.has_capability_calls():
    messages = await response.execute_capability_calls()  # No registry needed!
```

### Streaming

```python
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

client = create_provider("openai", api_key="sk-...")

for chunk in client.stream(
    messages=[UserMessage(content="Write a story")],
    model="gpt-4"
):
    print(chunk.delta, end="", flush=True)
```

### Async Operations

```python
import asyncio
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

async def main():
    client = create_provider("openai", api_key="sk-...")
    
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
from nimbus.models.registry import provider as create_provider

# This doesn't import OpenAI SDK until you actually use it
client = create_provider("openai", api_key="sk-...")

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
from nimbus.models.registry import provider as create_provider
from nimbus.base.messages import UserMessage

def lambda_handler(event, context):
    # Bedrock provider works without boto3 in dependencies
    client = create_provider("bedrock", region="us-east-1")
    
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
from nimbus.base.config import ConfigLoader

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
from nimbus.base.completion import CompletionResponse, StreamChunk
from nimbus.base.messages import NimbusMessage

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
from nimbus.base.interfaces import CapabilityInterface, CapabilitySchema

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
from nimbus.base.interfaces import MemoryInterface
from nimbus.memory import MemoryEntry

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

The router is the main entry point for load balancing across multiple providers and deployments:

```python
from nimbus.base.messages import UserMessage
from nimbus.router import ModelRouter, ModelTarget, RouteConfig
from nimbus.base.interfaces.router import RoutingStrategy

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
                model="gpt-4",
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

# Use the router directly - it handles provider instantiation
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"  # This is the alias, router picks the best target
)

# Or use tag-based selection
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    tags=["premium", "paid"]
)

# Or combine both (model must have all specified tags)
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4",
    tags=["premium"]
)
```

### Router Configuration from YAML

```python
from nimbus.router import ModelRouter

# Load router from YAML file with environment variable substitution
router = ModelRouter.from_yaml("router_config.yaml")

# Use the router
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-3.5-turbo"  # Alias defined in YAML
)

# Or use tag-based selection
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    tags=["fast", "cheap"]
)
```

Example YAML configuration:
```yaml
# router_config.yaml
routes:
  - alias: "gpt-3.5-turbo"
    strategy: "rate_limit_aware"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 200000
        rpm: 2000
        tags: ["fast", "cheap", "general"]
      - model: "gpt-3.5-turbo"
        provider: "azure"
        api_key: "${AZURE_API_KEY}"
        api_base: "${AZURE_API_BASE}"
        tpm: 100000
        rpm: 1000
        tags: ["fast", "cheap", "general", "enterprise"]
  - alias: "gpt-4"
    strategy: "least_busy"
    targets:
      - model: "gpt-4"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 100000
        rpm: 500
        tags: ["smart", "expensive", "reasoning"]

fallbacks:
  - primary: "gpt-4"
    fallbacks: ["gpt-3.5-turbo"]

retry_policies:
  - error_type: "RateLimitError"
    max_retries: 3
```

### Flexible Model Selection

The router supports flexible model selection with both model names/aliases and tag-based filtering:

```python
# Use specific model or alias
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"
)

# Use tag-based selection (router picks best model with these tags)
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    tags=["fast", "cheap"]
)

# Combine both (model must have all specified tags)
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4",
    tags=["premium"]  # Ensures gpt-4 has premium tag
)

# Async version
response = await router.acomplete(
    messages=[UserMessage(content="Hello!")],
    tags=["reasoning", "multilingual"]
)
```

### Rate Limiting and Health Tracking

The router automatically tracks rate limits and health metrics:

```python
# Check model health
health = router.get_model_health("gpt-4:openai:gpt-4")
print(f"Success rate: {health.success_rate:.1%}")
print(f"Average latency: {health.average_latency_ms:.1f}ms")

# Check usage stats
stats = router.get_usage_stats("gpt-4:openai:gpt-4")
print(f"TPM used: {stats.tpm_used}/{stats.tpm_limit}")
print(f"RPM used: {stats.rpm_used}/{stats.rpm_limit}")

# Check models in cooldown
cooled_down = router.get_cooldown_models()
for info in cooled_down:
    print(f"{info.model_id} cooled down until {info.cooldown_until}")
```

### Fallbacks and Retry Policies

```python
from nimbus.router import ModelRouter, FallbackConfig, RetryPolicyConfig

router = ModelRouter(
    routes=[...],
    fallbacks=[
        FallbackConfig(
            primary="gpt-4",
            fallbacks=["gpt-3.5-turbo", "claude-3-sonnet"]
        )
    ],
    retry_policies=[
        RetryPolicyConfig(error_type="RateLimitError", max_retries=3),
        RetryPolicyConfig(error_type="TimeoutError", max_retries=2)
    ]
)
```

### Serverless Support with External Storage

For serverless environments, use external storage backends:

```python
from nimbus.router import ModelRouter
from nimbus.store import RedisBackend, DynamoDBBackend

# Redis backend for persistent state
redis_storage = RedisBackend("redis://localhost:6379")
router = ModelRouter(
    routes=[...],
    storage=redis_storage
)

# DynamoDB backend for AWS Lambda
dynamodb_storage = DynamoDBBackend(
    table_name="nimbus-router-state",
    region="us-east-1"
)
router = ModelRouter(
    routes=[...],
    storage=dynamodb_storage
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
- [ ] Prompt management
- [ ] Agent runtime
- [ ] Memory systems
- [ ] Safety filters
- [ ] Policy engine inspired by [Cedar](https://www.cedarpolicy.com/)
  - Rules are `permit` or `forbid` statements over principal, action, resource and context. Everything is denied unless a `permit` matches, and a `forbid` always wins
  - Evaluated in pure Python, with no compiled dependency. The official Cedar engine is a Rust library, so Nimbus implements a small subset of the model instead of wrapping it
  - Guards capability and tool calls, model and region routing, memory access and MCP servers. Every decision is sent to observability
- [ ] Gateway inspired by [Amazon Bedrock AgentCore Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-core-concepts.html)
  - One MCP endpoint (stateless HTTP, runs in a single Lambda function) that exposes Lambda functions, OpenAPI specs, upstream MCP servers and local capabilities as tools
  - Inbound authorization by IAM or a JWT authorizer, outbound authorization per target (execution role, API key, OAuth client credentials)
  - Every tool listing and tool call goes through the policy engine, so a caller only sees the tools it may use. Two tool selectors: hybrid search (keywords and embeddings) and Jev, a decision model
  - Standard library only: no `mcp` package, no web framework
- [ ] Observability integration

## Acknowledgments

Nimbus is inspired by:
- **LangChain** - For pioneering LLM application frameworks
- **LiteLLM** - For provider abstraction patterns
- **Clean Architecture** - For architectural principles
- **Amazon Bedrock AgentCore Gateway** - For the gateway model (targets, inbound and outbound authorization, policy on every tool call)
- **Cedar** - For the policy model (principal, action, resource, context; default deny; forbid overrides permit)
- **Pydantic** - For data validation and settings management
