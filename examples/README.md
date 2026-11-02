# Skye Examples

Welcome to the Skye examples directory! This collection demonstrates how to use Skye for building GenAI applications.

## Quick Start

### Installation

```bash
# Install Skye with OpenAI support
pip install skyeai[openai]

# Install with multiple providers
pip install skyeai[openai,anthropic,bedrock]

# Install everything
pip install skyeai[all]
```

### Set Up API Keys

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Azure OpenAI
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://..."

# AWS Bedrock (uses AWS credentials)
export AWS_PROFILE="your-profile"
# or
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

## How every example creates a client

One call, in the style of `boto3.client`; the same line for every provider:

```python
import skye

client = skye.provider("openai", api_key="sk-...")
response = client.complete(messages=[...], model="gpt-4")
```

Skye is built for serverless architectures, where the size of the library and its cold start make a difference, so each example needs
only the extra of the provider it uses. Every example is run offline against a fake network by `tests/examples`, so none of them can
drift from the library.

## Example Categories

### 1. Basic Examples (`examples/basic/`)

Start here to learn the fundamentals:
- `quickstart.py`: create a client with one call and ask a question
- `async_and_streaming.py`: `acomplete` and `stream`
- `configuration.py`: file, environment and code overrides, `${VAR}` substitution
- `simple_completion.py`: multi-turn conversations, structured outputs, message types and metadata

**Run:**
```bash
python examples/basic/quickstart.py
```

### 2. Capabilities (`examples/capabilities/`)

Learn how to use capabilities (tools/functions):
- Function calling
- Capability execution
- Multi-turn capability workflows
- Provider-specific implementations

- `mcp_client.py`: list and call the tools of an MCP server with the built-in client

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
- `bring_your_own_adapter.py`: your own model or SDK wrapper as a `Runnable`

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
- `fallbacks_and_health.py`: fallbacks, retry policies, health, usage and cooldown

**Run:**
```bash
python examples/routing/basic_routing.py
python examples/routing/yaml_config.py
```

### 5. Advanced (`examples/advanced/`)

Explore advanced patterns:
- `multimodal.py`: images from a URL, a data URL or a file
- `structured_output.py`: nested schemas, enums and optional fields, validated
- `function_calling.py`: several capabilities, parallel execution, errors inside a capability
- `streaming.py`: `stream` and `astream`, time to first token
- `prompt_engineering.py`: few-shot, chain of thought, composition, dynamic prompts
- `custom_providers.py`: your own provider, registered and used with `skye.provider`

**Run:**
```bash
python examples/advanced/streaming.py
python examples/advanced/custom_providers.py
```

### 6. Serverless (`examples/serverless/`)

Patterns for serverless runtimes, where the size of the library and its cold start matter:
- `lambda_handler.py`: a handler that creates its client once, outside the handler (written for AWS Lambda, valid on any runtime)
- `serverless_router_example.py`: a router whose state lives in an external store (file system, Redis, DynamoDB, PostgreSQL)

**Run:**
```bash
python examples/serverless/lambda_handler.py
```

### 7. Prompts (`examples/prompts/`)

Templates, few-shot examples, message roles and multimodal prompts (`basic_usage.py`, `few_shot_learning.py`, `message_roles.py`, `multimodal_content.py`).

Provider by provider versions of multimodal inputs, structured outputs and function calling are in `examples/providers/`.

## Common Patterns

### Basic Completion

```python
import skye
from skye.base.messages import UserMessage

client = skye.provider("openai", api_key="sk-...")

response = client.complete(
    messages=[UserMessage(content="Hello, world!")],
    model="gpt-4"
)

print(response.content)
```

### With Capabilities

```python
import skye
from skye.base.messages import UserMessage

client = skye.provider("openai", api_key="sk-...")

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
from skye.router import ModelRouter, ModelTarget, RouteConfig

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
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"
)

# Tag-based selection
response = router.complete(
    messages=[UserMessage(content="Hello!")],
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
from skye.router import ModelRouter

router = ModelRouter.from_yaml("router_config.yaml")
response = router.complete(
    messages=[UserMessage(content="Hello!")],
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
pip install skyeai[openai]
pip install skyeai[anthropic]
pip install skyeai[bedrock]
```

### Import Errors

```bash
# Make sure Skye is installed
pip install skyeai

# Check installation
python -c "import skye; print(skye.__version__)"
```

## Documentation

- [Skye Documentation](https://github.com/skyeai/skye)
- [API Reference](https://github.com/skyeai/skye/docs)
- [Architecture Guide](https://github.com/skyeai/skye/docs/architecture.md)

## Contributing

Found a bug or want to add an example? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Add your example
4. Submit a pull request

## License

These examples are part of Skye and are licensed under the same license as the main project.

## Support

- 📖 [Documentation](https://github.com/skyeai/skye)
- 💬 [Discussions](https://github.com/skyeai/skye/discussions)
- 🐛 [Issues](https://github.com/skyeai/skye/issues)
- 📧 [Email](mailto:support@skyeai.com)

---

Happy coding! 🚀
