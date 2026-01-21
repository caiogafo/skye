---
inclusion: always
---

# Nimbus Architecture Guidelines

## Overview

Nimbus is a modular suite of Python libraries for building GenAI applications. This document provides architectural guidelines and conventions that all Nimbus components must follow.

## Development Tools

**IMPORTANT**: Always use `uv` for running commands in this project:

```bash
# Run tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/unit/test_example.py

# Run with coverage
uv run pytest tests/ --cov=src/nimbus

# Run linters
uv run ruff check src/ tests/
uv run mypy src/

# Format code
uv run black src/ tests/
```

Do NOT use plain `pytest`, `python`, or `pip` commands. Always prefix with `uv run`.

## Core Principles

### 1. Clean Architecture

- **Dependency Rule**: All components depend on nimbus-core, but nimbus-core depends on NO other Nimbus components
- **Interface-First**: Define interfaces in core, implement in plugins
- **Separation of Concerns**: Each component has a single, well-defined responsibility

### 2. Modularity

- **Optional by Default**: Base package provides only interfaces and models; all implementations are optional extras
- **Plug-and-Play**: Install only the components you need via extras
- **Single Package**: All components in one package, versioned together for consistency

### 3. Provider Agnosticism

- **No Vendor Lock-in**: Support multiple providers (OpenAI, Anthropic, AWS Bedrock, Azure, local models)
- **Unified Interface**: Same API regardless of underlying provider
- **Transparent Switching**: Change providers without code changes
- **Transformation Encapsulation**: All provider-specific transformations are contained within provider client classes
- **Core Library Independence**: Core library code (routers, capabilities, models) remains completely provider-agnostic

## Naming Conventions

### Package Structure

Nimbus is a single package with optional extras:

**Base Package:**
- `nimbus` (interfaces + models only)

**Optional Extras:**
- `nimbus[bedrock]` (AWS Bedrock provider)
- `nimbus[openai]` (OpenAI provider)
- `nimbus[anthropic]` (Anthropic provider)
- `nimbus[agents]` (agent runtime)
- `nimbus[prompts]` (prompt management)
- `nimbus[tools]` (capabilities/tools)
- `nimbus[memory]` (persistent memory)
- `nimbus[guard]` (safety filters)
- `nimbus[observe]` (observability)

### Interface Names

All interfaces follow the pattern: `{Concept}Interface`

Examples:
- `ModelInterface` (not LLMInterface or ProviderInterface)
- `CapabilityInterface` (not ToolInterface or FunctionInterface)
- `VectorEncoderInterface` (not EmbeddingInterface)
- `EventHandlerInterface` (not CallbackInterface)
- `ContentReaderInterface` (not DocumentLoaderInterface)

### Capability Terminology

**IMPORTANT**: Always use "Capability" terminology, never "Tool":
- ✅ `CapabilityCall`, `CapabilityResult`, `CapabilityCallHandler`
- ❌ `ToolCall`, `ToolResult`, `ToolCallHandler` (removed in v1.0.0)

The term "capability" better represents the concept of functions/tools that LLMs can invoke.

### Model Names

Use Nimbus-specific terminology:

- `NimbusMessage` (base message class)
- `UserMessage`, `AssistantMessage`, `SystemMessage`, `CapabilityMessage` (not HumanMessage, AIMessage, ToolMessage)
- `ContentChunk` (not Document)
- `CompletionRequest`, `CompletionResponse` (standard)

### Avoid LangChain-Style Names

Do NOT use these patterns:
- ❌ `BaseMessage`, `HumanMessage`, `AIMessage`
- ❌ `Document`, `DocumentLoader`
- ❌ `Embeddings`, `EmbeddingModel`
- ❌ `OutputParser`, `StrOutputParser`
- ❌ `Callback`, `CallbackHandler`

Use Nimbus equivalents:
- ✅ `NimbusMessage`, `UserMessage`, `AssistantMessage`
- ✅ `ContentChunk`, `ContentReader`
- ✅ `VectorEncoder`
- ✅ `ResponseFormatter` (or integrate into message APIs)
- ✅ `EventHandler`

## Provider Architecture

### Transformation Encapsulation

All provider-specific transformations MUST be encapsulated within provider client classes:

**Provider Client Responsibilities:**
- Transform Nimbus requests to provider-specific format
- Transform provider responses to Nimbus format
- Handle provider-specific message formats
- Handle provider-specific capability/tool formats
- Extract and convert tool calls from provider responses
- Map provider-specific parameters and options

**Core Library Responsibilities:**
- Define provider-agnostic interfaces and models
- Implement routing logic using only Nimbus models
- Implement capability handling using only Nimbus models
- Provide thin delegation layers for transformations

**Example Provider Client:**
```python
class OpenAIProvider(BaseModelProvider):
    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """All OpenAI-specific transformation logic here."""
        return {
            "model": request.model,
            "messages": self._transform_messages(request.messages),
            "tools": self._transform_capabilities(request.capabilities) if request.capabilities else None,
            # ... all other OpenAI-specific mappings
        }
    
    def _transform_messages(self, messages: list[NimbusMessage]) -> list[dict[str, Any]]:
        """OpenAI-specific message transformation."""
        # All OpenAI message format logic here
        pass
    
    def _transform_capabilities(self, capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
        """OpenAI-specific capability transformation."""
        # All OpenAI tool format logic here
        pass
```

**Adding a New Provider:**
To add a new provider, you only need to:
1. Create a new provider client class inheriting from `BaseModelProvider`
2. Implement all transformation methods for that provider
3. No changes to core library code required

## Code Standards

### Type Safety

- **Complete Type Hints**: All public APIs must have type hints
- **Pydantic Models**: Use Pydantic for all data structures
- **Runtime Validation**: Validate interface compliance at runtime

### Error Handling

- **Custom Exceptions**: Use NimbusError hierarchy
- **Context Preservation**: Include original errors and stack traces
- **Structured Logging**: Log all errors with appropriate severity

### Async Support

- **Dual APIs**: Provide both sync and async versions of I/O operations
- **Naming Convention**: Async methods prefixed with `a` (e.g., `acomplete`, `aencode`)

### Documentation

- **Docstrings**: All public APIs must have docstrings
- **Type Hints**: Serve as inline documentation
- **Examples**: Include usage examples in docstrings

## Package Structure

### Single Package with Extras

```
nimbus/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── nimbus/
│       ├── __init__.py          # Core exports
│       ├── completion.py        # Always included
│       ├── messages.py          # Always included
│       ├── config.py            # Configuration loading
│       ├── exceptions.py        # Exception hierarchy
│       ├── interfaces/          # Always included
│       ├── capabilities/        # Capability system
│       ├── providers/           # Optional extras
│       │   ├── llm/            # LLM providers
│       │   └── embeddings/     # Embedding providers
│       ├── routes/              # Router with load balancing
│       ├── agents/              # Optional extras
│       ├── memory/              # Optional extras
│       ├── guard/               # Safety filters
│       ├── observe/             # Observability
│       ├── prompts/             # Prompt management
│       └── utils/               # Utilities
└── tests/
    ├── unit/                    # Fast, isolated tests
    │   ├── capabilities/
    │   ├── providers/
    │   ├── routes/
    │   └── utils/
    ├── integration/             # Multi-component tests
    │   ├── capabilities/
    │   ├── providers/
    │   └── routes/
    ├── stress/                  # Performance tests
    │   ├── test_concurrent_routing.py
    │   ├── test_rate_limiting.py
    │   └── test_capability_load.py
    └── fixtures/                # Shared test fixtures
```

### Dependencies

- **Minimal Base**: Only pydantic and pyyaml in base
- **Optional Dependencies**: Heavy dependencies only installed with extras
- **Extras Configuration**: Use [project.optional-dependencies] for optional components

Example pyproject.toml:
```toml
[project]
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
bedrock = ["boto3>=1.28"]
openai = ["openai>=1.0"]
memory = ["redis>=5.0"]
all = ["boto3>=1.28", "openai>=1.0", "redis>=5.0"]
```

## Advanced Features

### Load Balancing and Routing

When implementing model routing:
- Support multiple routing strategies (round-robin, least-busy, cost-based, rate-limit-aware)
- Implement fallback mechanisms
- Track model health and performance
- Support cooldowns for failed models

### Rate Limiting

- Track requests per minute (RPM) and tokens per minute (TPM)
- Support both per-model and global rate limits
- Implement token bucket or sliding window algorithms

### Structured Outputs

- Use Pydantic models for schema definition
- Generate JSON Schema automatically
- Handle provider-specific differences transparently
- Validate responses against schema

### Observability

- Emit structured log events
- Support correlation IDs for request tracing
- Provide hooks for custom telemetry
- Track token usage and costs

## Testing Guidelines

### Unit Tests

- Test each component in isolation
- Mock external dependencies
- Focus on business logic

### Integration Tests

- Test component interactions
- Use real implementations where possible
- Test configuration loading from multiple sources

### Test Coverage

- Aim for 80%+ coverage on core functionality
- Optional tests can be marked with `*` in task lists
- Focus on critical paths first

## Configuration Management

### Multi-Source Configuration

Support configuration from:
1. Code (highest priority)
2. Environment variables (NIMBUS_ prefix)
3. Configuration files (YAML/JSON)

### Environment Variables

Use consistent naming:
- `NIMBUS_LOG_LEVEL`
- `NIMBUS_MODEL_PROVIDER`
- `NIMBUS_API_KEY`
- `NIMBUS_ENABLE_TELEMETRY`

### Environment Variable Substitution

Both YAML and Python configurations support environment variable substitution using `${VAR_NAME}` syntax:

**In YAML:**
```yaml
api_key: "${OPENAI_API_KEY}"
api_base: "${AZURE_API_BASE}"
```

**In Python:**
```python
from nimbus.routes import ModelTarget

target = ModelTarget(
    model="gpt-4",
    provider="openai",
    api_key="${OPENAI_API_KEY}"  # Will be substituted automatically
)
```

**Security Best Practices:**
- Never hardcode API keys in configuration files
- Use environment variables for all sensitive data
- Consider using `.env` files for local development
- Use secure secret management in production (AWS Secrets Manager, Azure Key Vault, etc.)

### Configuration Files

Support both YAML and JSON with environment variable substitution:
```yaml
# nimbus.yaml
log_level: INFO
models:
  gpt-4:
    provider: openai
    api_key: ${OPENAI_API_KEY}
    temperature: 0.7
```

### Router Configuration from YAML

Routers can be configured via YAML files:
```yaml
# router_config.yaml
routes:
  - alias: "gpt-3.5-turbo"
    strategy: "rate_limit_aware"
    targets:
      - model: "azure/chatgpt-v-2"
        provider: "azure"
        api_key: "${AZURE_API_KEY}"
        api_base: "${AZURE_API_BASE}"
        tpm: 100000
        rpm: 1000
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 200000
        rpm: 2000

fallbacks:
  - primary: "gpt-4"
    fallbacks: ["gpt-3.5-turbo"]

retry_policies:
  - error_type: "RateLimitError"
    max_retries: 3
```

Load router from YAML:
```python
from nimbus.routes import ModelRouter

router = ModelRouter.from_yaml("router_config.yaml")
```

## Version Compatibility

### Semantic Versioning

- MAJOR: Breaking changes to interfaces
- MINOR: New features, backward compatible
- PATCH: Bug fixes

### Interface Stability

- Core interfaces should remain stable
- Deprecate before removing
- Provide migration guides for breaking changes

## Security Best Practices

### API Key Management

- Never hardcode API keys
- Use environment variables or secure vaults
- Support key rotation

### Input Validation

- Validate all inputs using Pydantic
- Sanitize user-provided content
- Implement rate limiting to prevent abuse

### Safety Filters

- Support input and output moderation
- Allow configurable safety policies
- Log safety violations

## Performance Considerations

### Caching

- Cache model responses when appropriate
- Support TTL-based cache invalidation
- Allow cache bypass for sensitive operations

### Batching

- Support batch operations for embeddings
- Implement request batching for efficiency
- Balance latency vs. throughput

### Resource Management

- Implement proper cleanup in plugin shutdown
- Use context managers for resource handling
- Support connection pooling

## Contributing to Nimbus

### Code Review Checklist

- [ ] Follows naming conventions
- [ ] Has complete type hints
- [ ] Has docstrings for public APIs
- [ ] Includes tests
- [ ] Updates documentation
- [ ] No hardcoded credentials
- [ ] Handles errors gracefully

### Pull Request Guidelines

- Reference related issues
- Include usage examples
- Update CHANGELOG.md
- Ensure CI passes

## Installation Examples

```bash
# Base only (interfaces + models)
pip install nimbus

# With specific provider
pip install nimbus[bedrock]

# Multiple extras
pip install nimbus[bedrock,agents,memory]

# Everything
pip install nimbus[all]
```

## Import Examples

```python
# Core models (always available)
from nimbus.completion import CompletionRequest, CompletionResponse
from nimbus.messages import UserMessage, AssistantMessage

# Capabilities (always available)
from nimbus.capabilities import (
    CapabilityInterface,
    CapabilityCall,
    CapabilityResult,
    CapabilityCallHandler,
    capability,
    CapabilityRegistry
)

# Router (always available)
from nimbus.routes import ModelRouter, ModelTarget, RouteConfig
from nimbus.interfaces.router import RoutingStrategy

# Providers (only if installed with extras)
from nimbus.providers.llm.bedrock import BedrockModel
from nimbus.providers.llm.openai import OpenAIModel
from nimbus.providers.llm.anthropic import AnthropicModel

# Other components (only if installed with extras)
from nimbus.agents import AgentRuntime
from nimbus.memory import EpisodicMemory
```

## Configuration Examples

### Programmatic Configuration

```python
from nimbus.routes import ModelRouter, ModelTarget, RouteConfig
from nimbus.interfaces.router import RoutingStrategy

router = ModelRouter(routes=[
    RouteConfig(
        alias="gpt-3.5-turbo",
        targets=[
            ModelTarget(
                model="azure/chatgpt-v-2",
                provider="azure",
                api_key="${AZURE_API_KEY}",  # Env var substitution
                tpm=100000,
                rpm=1000
            ),
            ModelTarget(
                model="gpt-3.5-turbo",
                provider="openai",
                api_key="${OPENAI_API_KEY}",  # Env var substitution
                tpm=200000,
                rpm=2000
            )
        ],
        strategy=RoutingStrategy.RATE_LIMIT_AWARE
    )
])
```

### YAML Configuration

```python
from nimbus.routes import ModelRouter

# Load from YAML file
router = ModelRouter.from_yaml("router_config.yaml")

# Use the router
response = router.complete(
    messages=[UserMessage("Hello!")],
    model="gpt-4"
)
```

## References

- [Nimbus Design](../.kiro/specs/nimbus/design.md)
- [Nimbus Requirements](../.kiro/specs/nimbus/requirements.md)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
