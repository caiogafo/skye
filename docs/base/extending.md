---
title: "Extending Skye"
status: current
last_updated: 2026-11-05
---

# Extending Skye

To extend the library, implement one Port from `skye.interfaces`, register it where the table says, and copy the example next to it.
A Port is the contract (`...Interface`, or a name without the suffix such as `Runnable`, `DecisionModel` and `StorageBackend`); a
"data" row is a type a Port uses, not something to implement. Every Port states what it raises, what it returns when something is
missing and whether it is safe to call concurrently, in the docstring of its module. A test (`tests/unit/test_port_signatures.py`)
checks each built-in implementation and a short reference implementation of each Port against the Port's signatures.

| Name | Kind | Where to register | Example | Status |
|---|---|---|---|---|
| `AuthenticationInterface` | credential provider | `auth` registry (`skye.auth`) | `examples/auth/custom_credential_source.py` | implemented |
| `AuthorizerInterface` | authorizer | injected into the runtime (`skye.policy`) | `examples/policy/authorizer.py` | implemented |
| `CapabilityContext` | data type, not a Port | - | - | data |
| `CapabilityInterface` | tool | tools registry (`skye.tools`) | `examples/tools/registry.py` | implemented |
| `CapabilitySchema` | data type, not a Port | - | - | data |
| `ConfigLoaderInterface` | configuration loader | `skye.config.ConfigLoader` satisfies it by structure | - | implemented |
| `ContentReaderInterface` | document reader | none yet | - | not yet (reference in the same test) |
| `CostCalculatorInterface` | cost calculator | `skye.models.CostCalculator` is the built-in one | `examples/models/cost_tracking.py` | implemented |
| `Decision` | data type, not a Port | - | - | data |
| `DecisionModel` | decision model | `models` | `examples/models/decision_model.py` | implemented |
| `DecisionResult` | data type, not a Port | - | - | data |
| `EventHandlerInterface` | agent hooks | passed to the agent (`skye.agents`) | `examples/agents/agent_with_hooks.py` | implemented |
| `EventType` | data type, not a Port | - | - | data |
| `MemoryEntryLike` | data type, not a Port | - | - | data |
| `MemoryInterface` | memory | passed to the agent (`skye.memory`) | `examples/memory/custom_memory.py` | implemented |
| `ModelInterface` | model provider | provider registry (`skye.models`) | `examples/advanced/custom_providers.py` | implemented |
| `ModelHealthInterface` | router health role (failures, cooldown, usage) | part of `ModelRouterInterface` | `examples/routing/fallbacks_and_health.py` | implemented |
| `ModelRouterInterface` | router (selection, health and configuration together) | `skye.router` | `examples/routing/basic_routing.py` | implemented |
| `ModelSelectionInterface` | router selection role (register, select, complete) | part of `ModelRouterInterface` | `examples/routing/basic_routing.py` | implemented |
| `ObserverInterface` | observability exporter | observe registry (`skye.observe`) | `examples/observe/custom_exporter.py` | implemented |
| `PluginInterface` | plugin | plugin registration | - | not yet (reference in the same test) |
| `PromptBuilderInterface` | prompt builder (rendering, registry and schema together) | `skye.prompts` | `examples/advanced/prompt_engineering.py` | implemented |
| `PromptRegistryInterface` | prompt registry role (templates, defaults) | part of `PromptBuilderInterface` | `examples/advanced/prompt_engineering.py` | implemented |
| `PromptRenderingInterface` | prompt rendering role | part of `PromptBuilderInterface` | `examples/advanced/prompt_engineering.py` | implemented |
| `PromptSchemaInterface` | prompt schema role (output schema, validation) | part of `PromptBuilderInterface` | `examples/advanced/prompt_engineering.py` | implemented |
| `ProviderRegistryInterface` | provider registry | `skye.models` | `examples/advanced/custom_providers.py` | implemented |
| `RouterConfigurationInterface` | router configuration role (strategy, fallbacks, policies) | part of `ModelRouterInterface` | `examples/routing/basic_routing.py` | implemented |
| `RoutingStrategy` | data type, not a Port | - | - | data |
| `Runnable` | agent, team or flow unit | passed wherever a `Runnable` is accepted | `examples/agents/custom_agent_type.py`, `examples/teams/team_of_runnables.py` | implemented |
| `SafetyFilterInterface` | safety filter | `skye.guard` | `examples/guard/safety_filters.py` | implemented |
| `SafetyResult` | data type, not a Port | - | - | data |
| `StorageBackend` | store backend | one module in `skye.store` | `examples/store/custom_backend.py` | implemented |
| `TokenCounterInterface` | token counter | `skye.models.TokenCounter` is the built-in one | `examples/models/token_counting.py` | implemented |
| `ToolProvider` | toolset of an agent | pass it to the agent; `CapabilityRegistry` is one (`skye.tools`), the gateway client will be another | `examples/capabilities/capability_agent.py` | implemented by the registry |
| `VectorEncoderInterface` | embedding provider | provider registry (`skye.models`) | `examples/providers/embeddings_example.py` | implemented |
