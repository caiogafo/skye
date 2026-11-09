---
title: "Skye documentation"
status: current
last_updated: 2026-11-02
---

# Skye documentation

New here? Start with [getting started](getting-started.md).

One section per component; the section name is the component's short name.

| Section | Contents |
|---------|----------|
| [`base`](base/index.md) | Messages, completion, errors, config and the Ports (interfaces). Standard library only. |
| [`auth`](auth/index.md) | Authentication and credentials: strategies, credential sources and a token cache. Authorization is `policy`. |
| [`models`](models/index.md) | Adapters to every kind of model API (LLMs, embeddings, decision models) and the shared HTTP transport. |
| [`store`](store/index.md) | External state: in-memory, file, DynamoDB, Redis, PostgreSQL. |
| [`router`](router/index.md) | ModelRouter, routing strategies, health tracking and fallbacks. |
| [`tools`](tools/index.md) | Tool registry, local functions, remote APIs and the MCP client. |
| [`prompts`](prompts/index.md) | Loaders, role-based messages and templates. |
| [`memory`](memory/index.md) | Memory implementations behind the memory Port. |
| [`guard`](guard/index.md) | Safety filters. |
| [`policy`](policy/index.md) | Policy engine (Cedar-inspired): authorization decisions. |
| [`observe`](observe/index.md) | Events, logs, metrics and traces. |
| [`gateway`](gateway/index.md) | MCP gateway with a toolset per operation. |
| [`agents`](agents/index.md) | The agent loop (`AgentLoop`), the default `Agent` and hooks. |
| [`teams`](teams/index.md) | Optional teams of agents. |
| [`flows`](flows/index.md) | Optional flows (workflows). |

Other pages: [getting started](getting-started.md), [architecture](architecture.md), [deployment](deployment.md), [budgets](budgets.md), [development](development.md), [roadmap](roadmap.md), [codename glossary](glossary.md).
