# Skye AI

**Modular GenAI library with optional extras**

Skye AI provides a foundational layer for building AI agents and intelligent applications with a Clean Architecture approach. The base package includes only interfaces and models, while all implementations are available as optional extras.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
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
pip install skyeai[memory]    # add only what you need: tokens, auth, memory, postgres, mcp, ...
```

Every extra is optional and loaded lazily. All extras and install options: [getting started](https://github.com/ggiallo28/skye/blob/main/docs/getting-started.md).

## Quick start

One call creates the client of a provider, in the style of `boto3.client`:

```python
import skye
from skye import UserMessage

# AWS credentials come from the usual sources: environment variables, ~/.aws or the instance role
client = skye.provider("bedrock", region="us-east-1")
response = client.complete(
    messages=[UserMessage(content="Hello!")],
    model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
)
print(response.content)
```

The same line works for every provider (`"openai"`, `"anthropic"`, `"bedrock"`, `"azure"`, `"google"`, `"cohere"`); for embeddings add `provider_type="embedding"`.
To balance several models with fallbacks, use the router: [router overview](https://github.com/ggiallo28/skye/blob/main/docs/router/overview.md).

## Examples

Runnable examples are in [`examples/`](https://github.com/ggiallo28/skye/blob/main/examples/README.md), one folder per topic:

| Folder | What it shows |
|---|---|
| [`examples/basic`](https://github.com/ggiallo28/skye/tree/main/examples/basic) | quick start, async and streaming, configuration, completion requests |
| [`examples/providers`](https://github.com/ggiallo28/skye/blob/main/examples/providers/README.md) | OpenAI, Anthropic, Azure, Bedrock, Google, embeddings, multimodal, structured output, function calling, your own adapter |
| [`examples/routing`](https://github.com/ggiallo28/skye/blob/main/examples/routing/README.md) | the router: strategies, `.skye` configuration, fallbacks, health and usage |
| [`examples/capabilities`](https://github.com/ggiallo28/skye/blob/main/examples/capabilities/README.md) | local functions, remote APIs, function calling, the MCP client |
| [`examples/advanced`](https://github.com/ggiallo28/skye/blob/main/examples/advanced/README.md) | multimodal, structured output, function calling, streaming, prompt engineering, your own provider |
| [`examples/prompts`](https://github.com/ggiallo28/skye/tree/main/examples/prompts) | templates, few-shot examples, roles, multimodal prompts |
| [`examples/serverless`](https://github.com/ggiallo28/skye/tree/main/examples/serverless) | a handler that creates its client once, and a router with external state |

Every example is run offline against a fake network by `tests/examples`, so it cannot drift from the library.

## Documentation

The documentation is a wiki with one section per component; start from [`docs/index.md`](https://github.com/ggiallo28/skye/blob/main/docs/index.md).

| Topic | Page |
|---|---|
| Getting started, install, quick start | [getting started](https://github.com/ggiallo28/skye/blob/main/docs/getting-started.md) |
| Architecture and layers | [architecture](https://github.com/ggiallo28/skye/blob/main/docs/architecture.md) |
| Core interfaces and configuration | [interfaces](https://github.com/ggiallo28/skye/blob/main/docs/base/interfaces.md), [configuration](https://github.com/ggiallo28/skye/blob/main/docs/base/configuration.md) |
| Providers, embeddings, multimodal, streaming | [provider guide](https://github.com/ggiallo28/skye/blob/main/docs/models/provider-guide.md) |
| Function calling and capabilities | [function calling](https://github.com/ggiallo28/skye/blob/main/docs/tools/function-calling.md) |
| Routing, `.skye` files, health, fallbacks | [router overview](https://github.com/ggiallo28/skye/blob/main/docs/router/overview.md), [routing guide](https://github.com/ggiallo28/skye/blob/main/docs/router/routing-guide.md) |
| Lazy loading and serverless deployment | [deployment](https://github.com/ggiallo28/skye/blob/main/docs/deployment.md) |
| Size and load budgets | [budgets](https://github.com/ggiallo28/skye/blob/main/docs/budgets.md) |
| Codename glossary | [glossary](https://github.com/ggiallo28/skye/blob/main/docs/glossary.md) |
| Development: setup, tests, code quality | [development](https://github.com/ggiallo28/skye/blob/main/docs/development.md) |
| Roadmap | [roadmap](https://github.com/ggiallo28/skye/blob/main/docs/roadmap.md) |

How the project is specified: the requirements, the design and the decisions are in `.kiro/steering/` (`10-requirements.md`, `11-design.md`, `12-decisions.md`) and the per-component specs in `.kiro/specs/`.

## Contributing

See [CONTRIBUTING.md](https://github.com/ggiallo28/skye/blob/main/CONTRIBUTING.md). Fork, create a branch, make your changes with tests, run the code quality checks, and open a pull request.

## License

MIT License - see [LICENSE](https://github.com/ggiallo28/skye/blob/main/LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/ggiallo28/skye/issues)
- **Documentation**: [Full Documentation](https://github.com/ggiallo28/skye/blob/main/docs/index.md)

## Acknowledgments

Skye AI is inspired by:
- **LangChain** - For pioneering LLM application frameworks
- **LiteLLM** - For provider abstraction patterns
- **Clean Architecture** - For architectural principles
- **Cedar** - For the policy model (principal, action, resource, context; default deny; forbid overrides permit)
