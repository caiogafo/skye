# Nimbus Specification

This directory contains the complete specification for the **nimbus** library - a modular GenAI platform with optional extras.

## Documents

- **[requirements.md](requirements.md)** - Detailed requirements with user stories and acceptance criteria
- **[design.md](design.md)** - Comprehensive design document with architecture, interfaces, and data models
- **[tasks.md](tasks.md)** - Implementation plan with actionable coding tasks

## Quick Overview

### What is Nimbus?

Nimbus is a single Python package that provides:
- **Base**: Interfaces and models (always installed)
- **Extras**: Optional implementations (install only what you need)

### Installation

```bash
# Base only (interfaces + models)
pip install nimbus

# With specific components
pip install nimbus[bedrock]              # AWS Bedrock provider
pip install nimbus[openai]               # OpenAI provider
pip install nimbus[agents]               # Agent runtime
pip install nimbus[memory]               # Persistent memory

# Multiple extras
pip install nimbus[bedrock,agents,memory]

# Everything
pip install nimbus[all]
```

### Architecture

```
nimbus (base)
├── Interfaces (ModelInterface, CapabilityInterface, etc.)
├── Models (CompletionRequest, UserMessage, etc.)
├── Exceptions (NimbusError hierarchy)
└── Configuration (ConfigLoader, ModelConfig)

Optional Extras:
├── providers/    [bedrock], [openai], [anthropic]
├── agents/       [agents]
├── prompts/      [prompts]
├── tools/        [tools]
├── memory/       [memory]
├── guard/        [guard]
└── observe/      [observe]
```

### Key Design Principles

1. **Clean Architecture** - All extras depend on base, base depends on nothing
2. **Provider Agnostic** - Unified interface for all LLM providers
3. **Optional Everything** - Install only what you need
4. **Type Safe** - Complete type hints with Pydantic validation
5. **Async First** - Both sync and async APIs throughout

### Usage Example

```python
# Install: pip install nimbus[bedrock]

from nimbus.completion import CompletionRequest
from nimbus.messages import UserMessage
from nimbus.providers.bedrock import BedrockModel

model = BedrockModel(model_id="anthropic.claude-3-sonnet")
response = model.complete(
    CompletionRequest(
        messages=[UserMessage(content="Hello, world!")],
        model="claude-3-sonnet"
    )
)

print(response.content)
```

## Getting Started with Implementation

1. **Review the requirements** - Understand what needs to be built
2. **Study the design** - Learn the architecture and interfaces
3. **Follow the tasks** - Implement incrementally following the task list

To start implementing:
```bash
# Open the tasks file in your IDE
open .kiro/specs/nimbus/tasks.md

# Or start with task 1
# See tasks.md for detailed implementation steps
```

## Key Features

### Core Interfaces

- **ModelInterface** - LLM provider abstraction
- **CapabilityInterface** - Tools/functions for agents
- **MemoryInterface** - Persistent memory storage
- **VectorEncoderInterface** - Text embedding models
- **ModelRouterInterface** - Load balancing and routing
- **EventHandlerInterface** - Lifecycle event hooks
- **SafetyFilterInterface** - Input/output validation
- **ContentReaderInterface** - Document loading

### Advanced Features

- **Load Balancing** - Multiple routing strategies (round-robin, cost-based, rate-limit-aware)
- **Rate Limiting** - Per-model and global rate limits
- **Fallbacks** - Automatic failover to backup models
- **Cooldowns** - Temporary suspension of failed models
- **Structured Outputs** - Type-safe responses with Pydantic
- **Streaming** - First-class streaming support
- **Observability** - Built-in telemetry and logging

## Component Status

| Component | Status | Description |
|-----------|--------|-------------|
| Base (interfaces + models) | ✅ Specified | Core contracts and data structures |
| Providers (bedrock, openai, etc.) | 📋 Planned | LLM provider implementations |
| Agents | 📋 Planned | Agent runtime and execution |
| Memory | 📋 Planned | Episodic and semantic memory |
| Prompts | 📋 Planned | Prompt template management |
| Tools | 📋 Planned | Capability registry |
| Guard | 📋 Planned | Safety filters |
| Observe | 📋 Planned | Telemetry and monitoring |

## Next Steps

1. ✅ **Spec Complete** - Requirements, design, and tasks defined
2. 🔄 **Implementation** - Start with task 1 in tasks.md
3. 📦 **Testing** - Write tests as you implement
4. 📚 **Documentation** - Add docstrings and examples
5. 🚀 **Release** - Publish to PyPI

## Questions?

Refer to:
- [Nimbus Architecture Guidelines](../../steering/nimbus-architecture.md)
- [Python Standards](../../steering/python-standards.md)
- [Design Document](design.md) for detailed technical information
