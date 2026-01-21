# Nimbus Examples

Welcome to the Nimbus examples directory! This collection demonstrates how to use Nimbus for building GenAI applications.

## Quick Start

### Installation

```bash
# Install Nimbus with OpenAI support
pip install nimbus[openai]

# Install with multiple providers
pip install nimbus[openai,anthropic,bedrock]

# Install everything
pip install nimbus[all]
```

### Set Up API Keys

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Azure OpenAI
export AZURE_OPENAI_API_KEY="..."
export AZURE_API_BASE="https://..."

# AWS Bedrock (uses AWS credentials)
export AWS_PROFILE="your-profile"
# or
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

## Example Categories

### 1. Basic Examples (`examples/basic/`)

Start here to learn the fundamentals:
- Simple completions
- Multi-turn conversations
- Structured outputs
- Message types and metadata

**Run:**
```bash
python examples/basic/simple_completion.py
```

### 2. Capabilities (`examples/capabilities/`)

Learn how to use capabilities (tools/functions):
- Function calling
- Capability execution
- Multi-turn capability workflows
- Provider-specific implementations

**Run:**
```bash
python examples/capabilities/function_calling_example.py
```

### 3. Providers (`examples/providers/`)

Explore provider-specific features:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- AWS Bedrock
- Azure OpenAI
- Embeddings
- Multimodal inputs
- Structured outputs

**Run:**
```bash
python examples/providers/openai_example.py
python examples/providers/anthropic_example.py
python examples/providers/bedrock_example.py
```

### 4. Routing (`examples/routing/`)

Master load balancing and failover:
- Basic routing
- YAML configuration
- Fallback chains
- Rate limiting
- Multiple routing strategies

**Run:**
```bash
python examples/routing/basic_routing.py
python examples/routing/yaml_config.py
```

### 5. Advanced (`examples/advanced/`)

Explore advanced patterns:
- Multimodal processing
- Streaming responses
- Prompt engineering
- Custom providers
- Async operations

**Run:**
```bash
python examples/advanced/multimodal.py
python examples/advanced/streaming.py
```

## Common Patterns

### Basic Completion

```python
import nimbus
from nimbus.messages import UserMessage

client = nimbus.provider("openai", api_key="sk-...")

response = client.complete(
    messages=[UserMessage(content="Hello, world!")],
    model="gpt-4"
)

print(response.content)
```

### With Capabilities

```python
import nimbus
from nimbus.messages import UserMessage

client = nimbus.provider("openai", api_key="sk-...")

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

response = client.complete(
    messages=[UserMessage(content="What's the weather in Paris?")],
    model="gpt-4",
    capabilities=capabilities
)
```

### With Routing

```python
from nimbus.routes import ModelRouter, ModelTarget, RouteConfig

router = ModelRouter(
    routes=[
        RouteConfig(
            alias="gpt-4",
            targets=[
                ModelTarget(
                    model="gpt-4",
                    provider="openai",
                    api_key="sk-..."
                )
            ]
        )
    ]
)

response = router.complete(
    messages=[UserMessage("Hello!")],
    model="gpt-4"
)

# Tag-based selection
response = router.complete(
    messages=[UserMessage("Hello!")],
    tags=["fast", "cheap"]
)
```

### With YAML Configuration

```yaml
# router_config.yaml
routes:
  - alias: "gpt-4"
    targets:
      - model: "gpt-4"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
```

```python
from nimbus.routes import ModelRouter

router = ModelRouter.from_yaml("router_config.yaml")
response = router.complete(
    messages=[UserMessage("Hello!")],
    model="gpt-4"
)
```

## Supported Providers

| Provider | Models | Status |
|----------|--------|--------|
| OpenAI | GPT-4, GPT-3.5, etc. | ✅ Supported |
| Anthropic | Claude 3 family | ✅ Supported |
| AWS Bedrock | Claude, Llama, etc. | ✅ Supported |
| Azure OpenAI | GPT-4, GPT-3.5, etc. | ✅ Supported |
| Local Models | Ollama, LM Studio | ✅ Supported |

## Key Features

- **Multi-Provider Support**: Use the same code with different providers
- **Load Balancing**: Distribute requests across multiple deployments
- **Failover**: Automatic fallback to alternative models
- **Rate Limiting**: Enforce TPM/RPM limits
- **Capabilities**: Call functions/tools from models
- **Streaming**: Real-time token-by-token responses
- **Structured Outputs**: Type-safe responses with Pydantic
- **Async Support**: Full async/await support
- **YAML Configuration**: Declarative configuration files
- **Environment Variables**: Secure credential management

## Learning Path

1. **Start with basics**: `examples/basic/simple_completion.py`
2. **Learn capabilities**: `examples/capabilities/function_calling_example.py`
3. **Explore providers**: `examples/providers/openai_example.py`
4. **Master routing**: `examples/routing/basic_routing.py`
5. **Advanced patterns**: `examples/advanced/multimodal.py`

## Troubleshooting

### API Key Issues

```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Set API key
export OPENAI_API_KEY="sk-..."
```

### Provider Not Available

```bash
# Install provider extras
pip install nimbus[openai]
pip install nimbus[anthropic]
pip install nimbus[bedrock]
```

### Import Errors

```bash
# Make sure Nimbus is installed
pip install nimbus

# Check installation
python -c "import nimbus; print(nimbus.__version__)"
```

## Documentation

- [Nimbus Documentation](https://github.com/nimbus-ai/nimbus)
- [API Reference](https://github.com/nimbus-ai/nimbus/docs)
- [Architecture Guide](https://github.com/nimbus-ai/nimbus/docs/architecture.md)

## Contributing

Found a bug or want to add an example? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Add your example
4. Submit a pull request

## License

These examples are part of Nimbus and are licensed under the same license as the main project.

## Support

- 📖 [Documentation](https://github.com/nimbus-ai/nimbus)
- 💬 [Discussions](https://github.com/nimbus-ai/nimbus/discussions)
- 🐛 [Issues](https://github.com/nimbus-ai/nimbus/issues)
- 📧 [Email](mailto:support@nimbus-ai.com)

---

Happy coding! 🚀
