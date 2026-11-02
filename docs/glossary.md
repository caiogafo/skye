# Codename glossary

A codename is a small watermark in the Nimbus cloud and weather theme. The plain name is always the real name; a codename never appears in an import path, folder, file, class, function or config key.

## Component codenames (15)

| Codename | Component | Role |
|----------|-----------|------|
| stratus | `base` | Messages, completion, errors, config and the Ports (interfaces). Standard library only. |
| ozone | `auth` | Authentication and credentials: strategies, credential sources and a token cache. Authorization is `policy`. |
| zephyr | `models` | Adapters to every kind of model API (LLMs, embeddings, decision models) and the shared HTTP transport. |
| lake | `store` | External state: in-memory, file, DynamoDB, Redis, PostgreSQL. |
| jet | `router` | ModelRouter, routing strategies, health tracking and fallbacks. |
| updraft | `tools` | Tool registry, local functions, remote APIs and the MCP client. |
| cirrus | `prompts` | Loaders, role-based messages and templates. |
| dew | `memory` | Memory implementations behind the memory Port. |
| halo | `guard` | Safety filters. |
| isobar | `policy` | Policy engine (Cedar-inspired): authorization decisions. |
| radar | `observe` | Events, logs, metrics and traces. |
| horizon | `gateway` | MCP gateway with a toolset per operation. |
| cyclone | `agents` | The agent loop, BaseAgent and hooks. |
| front | `teams` | Optional teams of agents. |
| stream | `flows` | Optional flows (workflows). |

## Documentation-only watermarks

These are not component codenames and are not counted among the 15.

| Watermark | Meaning |
|-----------|---------|
| vapor | The `Runnable` Port (composition abstraction). |
| nimbus | The whole project; the umbrella watermark, free after the rename to Skye. |

## `auth` and `policy`

`auth` is authentication and credentials (who are you, how do you prove it). `policy` is authorization (may this principal perform this action on this resource).
