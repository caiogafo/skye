# Skye

**Modular GenAI library with optional extras**

Skye provides a foundational layer for building AI agents and intelligent applications with a Clean Architecture approach. The base package includes only interfaces and models, while all implementations are available as optional extras.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🎯 **Provider-agnostic** - Unified interface for OpenAI, Anthropic, AWS Bedrock, Azure, and more
- 🧩 **Modular architecture** - Install only what you need via optional extras
- 🔒 **Type-safe** - Complete type hints, with validated dataclasses
- ⚡ **Async-first** - Both sync and async APIs throughout
- 🔄 **Load balancing** - Multiple routing strategies with automatic fallbacks
- 📊 **Observability** - Built-in telemetry, logging, and tracing
- 🛡️ **Safety filters** - Input/output validation and moderation
- 💾 **Memory systems** - Episodic and semantic memory support


## Install

```bash
pip install skyeai            # the base: messages, completion, errors, config, Ports (standard library only)
pip install skyeai[yaml]      # add only what you need: yaml, auth, memory, postgres, mcp, ...
```

Every extra is optional and loaded lazily. All extras and install options: [getting started](docs/getting-started.md).

## Quick start

One call creates the client of a provider, in the style of `boto3.client`:

```python
import skye
from skye import UserMessage

client = skye.provider("openai", api_key="sk-...")
response = client.complete(messages=[UserMessage(content="Hello!")], model="gpt-4")
print(response.content)
```

The same line works for every provider (`"anthropic"`, `"bedrock"`, `"azure"`, `"google"`, `"cohere"`); for embeddings add `provider_type="embedding"`.
To balance several models with fallbacks, use the router: [router overview](docs/router/overview.md).

## Examples

Runnable examples are in [`examples/`](examples/README.md), one folder per topic:

| Folder | What it shows |
|---|---|
| [`examples/basic`](examples/basic/) | quick start, async and streaming, configuration, completion requests |
| [`examples/providers`](examples/providers/README.md) | OpenAI, Anthropic, Azure, Bedrock, Google, embeddings, multimodal, structured output, function calling, your own adapter |
| [`examples/routing`](examples/routing/README.md) | the router: strategies, YAML configuration, fallbacks, health and usage |
| [`examples/capabilities`](examples/capabilities/README.md) | local functions, remote APIs, function calling, the MCP client |
| [`examples/advanced`](examples/advanced/README.md) | multimodal, structured output, function calling, streaming, prompt engineering, your own provider |
| [`examples/prompts`](examples/prompts/) | templates, few-shot examples, roles, multimodal prompts |
| [`examples/serverless`](examples/serverless/) | a handler that creates its client once, and a router with external state |

Every example is run offline against a fake network by `tests/examples`, so it cannot drift from the library.

## Documentation

The documentation is a wiki with one section per component; start from [`docs/index.md`](docs/index.md).

| Topic | Page |
|---|---|
| Getting started, install, quick start | [getting started](docs/getting-started.md) |
| Architecture and layers | [architecture](docs/architecture.md) |
| Core interfaces and configuration | [interfaces](docs/base/interfaces.md), [configuration](docs/base/configuration.md) |
| Providers, embeddings, multimodal, streaming | [provider guide](docs/models/provider-guide.md) |
| Function calling and capabilities | [function calling](docs/tools/function-calling.md) |
| Routing, YAML, health, fallbacks | [router overview](docs/router/overview.md), [routing guide](docs/router/routing-guide.md) |
| Lazy loading and serverless deployment | [deployment](docs/deployment.md) |
| Size and load budgets | [budgets](docs/budgets.md) |
| Codename glossary | [glossary](docs/glossary.md) |
| Development: setup, tests, code quality | [development](docs/development.md) |
| Roadmap | [roadmap](docs/roadmap.md) |

How the project is specified: the requirements, the design and the decisions are in `.kiro/steering/` (`10-requirements.md`, `11-design.md`, `12-decisions.md`) and the per-component specs in `.kiro/specs/`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Fork, create a branch, make your changes with tests, run the code quality checks, and open a pull request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/skye/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/skye/discussions)
- **Documentation**: [Full Documentation](https://skye.readthedocs.io)

## Acknowledgments

Skye is inspired by:
- **LangChain** - For pioneering LLM application frameworks
- **LiteLLM** - For provider abstraction patterns
- **Clean Architecture** - For architectural principles
- **Amazon Bedrock AgentCore Gateway** - For the gateway model (targets, inbound and outbound authorization, policy on every tool call)
- **Cedar** - For the policy model (principal, action, resource, context; default deny; forbid overrides permit)
- **Pydantic** - For data validation, until the models move to dataclasses (`base` already has)
