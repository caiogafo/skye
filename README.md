# Skye AI

**Modular GenAI library with optional extras**

Skye AI provides a foundational layer for building AI agents and intelligent applications with a Clean Architecture approach. The base package includes only interfaces and models, while all implementations are available as optional extras.

[![PyPI](https://img.shields.io/pypi/v/skyeai?label=PyPI)](https://pypi.org/project/skyeai/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/readthedocs/skye?label=Docs)](https://skye.readthedocs.io/)
[![Install size: 1.1 MB](https://img.shields.io/badge/Install%20size-1.1%20MB-2EA44F)](https://skye.readthedocs.io/en/latest/budgets/)
[![Built with Kiro](https://img.shields.io/badge/Built%20with-Kiro-790ECB)](https://kiro.dev)

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
pip install skyeai[redis]     # add only what you need: tokens, auth, redis, postgres, aws, mcp, ...
```

Every extra is optional and loaded lazily. All extras and install options: [getting started](https://skye.readthedocs.io/en/latest/getting-started/).

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
To balance several models with fallbacks, use the router: [router overview](https://skye.readthedocs.io/en/latest/router/overview/).

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

The documentation is online at **[skye.readthedocs.io](https://skye.readthedocs.io)**; the source of every page is in `docs/`.

| You want to | Page |
|---|---|
| Install and make a first call | [Get started](https://skye.readthedocs.io/en/latest/get-started/) |
| Call a provider, stream, get structured output | [Models guides](https://skye.readthedocs.io/en/latest/guides/models/call-a-provider/) |
| Route across models with fallbacks | [Routing guides](https://skye.readthedocs.io/en/latest/guides/routing/aliases-and-fallbacks/) |
| Write prompts and routers in `.skye` | [The .skye language](https://skye.readthedocs.io/en/latest/concepts/skye-language/), [reference](https://skye.readthedocs.io/en/latest/reference/skye-language/) |
| Keep state across invocations | [Choose a store backend](https://skye.readthedocs.io/en/latest/guides/state/choose-a-backend/) |
| Deploy on AWS Lambda | [Deploy on AWS Lambda](https://skye.readthedocs.io/en/latest/get-started/lambda/) |
| Look up a class or a function | [Python API](https://skye.readthedocs.io/en/latest/reference/api/skye/), [CLI](https://skye.readthedocs.io/en/latest/reference/cli/) |
| Understand the design | [Architecture](https://skye.readthedocs.io/en/latest/concepts/architecture/), [Serverless first](https://skye.readthedocs.io/en/latest/concepts/serverless-first/) |
| See what is planned | [Status and roadmap](https://skye.readthedocs.io/en/latest/project/roadmap/) |

How the project is specified: the requirements, the design and the decisions are in `.kiro/steering/` (`10-requirements.md`, `11-design.md`, `12-decisions.md`) and the per-component specs in `.kiro/specs/`.

## Contributing

See [CONTRIBUTING.md](https://github.com/ggiallo28/skye/blob/main/CONTRIBUTING.md). Fork, create a branch, make your changes with tests, run the code quality checks, and open a pull request.

Everyone taking part in the project follows the [Code of Conduct](https://github.com/ggiallo28/skye/blob/main/CODE_OF_CONDUCT.md).

## License

MIT License - see [LICENSE](https://github.com/ggiallo28/skye/blob/main/LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/ggiallo28/skye/issues)
- **Documentation**: [skye.readthedocs.io](https://skye.readthedocs.io)

## Acknowledgments

Skye AI is inspired by:
- **LangChain** - For pioneering LLM application frameworks
- **LiteLLM** - For provider abstraction patterns
- **Clean Architecture** - For architectural principles
- **Cedar** - For the policy model (principal, action, resource, context; default deny; forbid overrides permit)
