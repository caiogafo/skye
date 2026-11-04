# Example coverage gaps — Skye (`skyeai`)

READ-ONLY investigation. No code or examples were changed. This report maps every component's user-facing
capabilities to the examples that demonstrate them, lists the missing examples needed to reach full coverage,
and flags examples that contradict current decisions. Import-style changes (open decision O21) are explicitly
out of scope.

## Summary answer

The `examples/` tree is **heavily skewed to three components** — `models` (providers), `router`, and `prompts` —
and has **no examples at all for 9 of the 15 components**: `auth`, `store`, `memory`, `guard`, `policy`, `observe`,
`gateway`, `agents`, `teams`, `flows` (10 counting `base` which has only incidental coverage). Of the extension
points the owner called out in open decision O20 (custom provider, custom credential source, custom store backend,
custom tool, custom exporter, bring-your-own `Runnable`, policy, memory, guard, agent-with-hooks, team, flow), only
**two are covered** (custom provider, bring-your-own `Runnable`).

Three concrete contradictions with current decisions need rewriting before this tree is used to define the UI:

1. **Pydantic in structured-output examples (violates D24).** `examples/advanced/structured_output.py`,
   `examples/providers/structured_output_example.py`, and `examples/basic/simple_completion.py` all define the
   user's output schema with `pydantic.BaseModel`. D24 says new data structures are dataclasses, not pydantic, and
   steering "must never present pydantic as the standard". `examples/providers/multimodal_example.py` also shows a
   `pydantic.BaseModel` schema inside its prose.
2. **Stale `prompts/` example set (violates D20, Requirement 13).** `examples/prompts/` (12 files) repeatedly refers
   to "Jinja2" features, uses a legacy `MockPromptBuilder` alias, and manipulates `sys.path`. D20 removed Jinja2;
   the engine is the standard-library `prompts/engine.py`.
3. **An empty placeholder file.** `examples/providers/router_example.py` is 0 bytes.

The components the specs clearly expect users to drive directly — especially the layer-3 runtime (`agents`, `teams`,
`flows`), the gateway (MCP server), and the optional services (`memory`, `guard`, `policy`, `observe`) — have no
example of how a user calls them, which is exactly the gap the owner wants closed before fixing import length.

---

## Evidence: inventory of existing examples

44 Python example files under `examples/` (`find examples -name '*.py'`), across 7 top-level dirs: `basic`,
`capabilities`, `providers`, `routing`, `advanced`, `serverless`, `prompts`. The test harness
`tests/examples/test_examples.py` runs every `*.py` under `examples/` (except `__init__.py`) offline against a fake
network (`tests/examples/fake_network.py`), so each example is an executable statement of the public API (O20).

| Example file | Component(s) | Capabilities demonstrated |
|---|---|---|
| `basic/quickstart.py` | models | `skye.provider`, `complete`, `UserMessage` |
| `basic/simple_completion.py` | models, base | `complete`, message types, token usage, **structured output via pydantic**, `CapabilityMessage` |
| `basic/async_and_streaming.py` | models | `acomplete`, `stream`, chunk `delta` |
| `basic/configuration.py` | base | `ConfigLoader`, `substitute_env_vars`, 3 prefixed env vars, `${VAR}`, precedence |
| `capabilities/local_function.py` | tools | `@capability`, schema from signature, sync+async execute |
| `capabilities/function_calling_example.py` | tools, models | `@capability`, capability calls round-trip |
| `capabilities/remote_api.py` | tools | `RemoteAPICapability` (GET/POST/PUT/DELETE, auth headers) |
| `capabilities/mcp_client.py` | tools | `create_mcp_client` built-in client, list/call tools |
| `capabilities/mcp_server.py` | tools | `MCPCapability` from a running server (needs `mcp` extra) |
| `providers/openai_example.py` | models, router | `skye.provider("openai")`, stream, async, `ModelTarget`/`RouteConfig` |
| `providers/anthropic_example.py` | models | `skye.provider("anthropic")`, stream, system messages |
| `providers/azure_example.py` | models | `skye.provider("azure")`, endpoint/deployment config |
| `providers/bedrock_example.py` | models, router | `skye.provider("bedrock")`, stream, router targets, lambda handler |
| `providers/google_example.py` | models | `skye.provider("google")`, stream, GCP project/location (D19 name correct) |
| `providers/embeddings_example.py` | models | `provider_type="embedding"`, `encode`, `encode_batch`, `aencode` |
| `providers/multimodal_example.py` | models | `ImageHandler` usage (mostly prose); **shows pydantic schema** |
| `providers/function_calling_example.py` | tools, models | capability calling (duplicate of capabilities dir) |
| `providers/structured_output_example.py` | models, base | **structured output via pydantic** (nested, enum, validation, optional) |
| `providers/bring_your_own_adapter.py` | base/models | custom `Runnable` adapter (extension point) |
| `providers/custom_providers.py` *(in advanced/)* | models | — see advanced |
| `providers/router_example.py` | — | **EMPTY (0 bytes)** |
| `routing/basic_routing.py` | router | `ModelRouter`, `RouteConfig`, `ModelTarget`, strategies, metrics |
| `routing/fallbacks_and_health.py` | router, store | fallbacks, retry policy, `get_model_health`, usage, cooldown, external store |
| `routing/yaml_config.py` | router, base | router from YAML, strategies, fallbacks, rate limits |
| `routing/yaml_config_example.py` | router, base | router from YAML + `${VAR}` substitution, `get_model_health`, `acomplete` |
| `advanced/streaming.py` | models | `stream` + `astream`, time-to-first-token |
| `advanced/function_calling.py` | tools, models | multiple capabilities, parallel execution, error inside a capability |
| `advanced/multimodal.py` | models | `ImageHandler` for URL/data-URL/file/bytes (notes message-carry not yet wired) |
| `advanced/structured_output.py` | models, base | **structured output via pydantic** (nested, enum, optional, `ValidationError`) |
| `advanced/custom_providers.py` | models | subclass `BaseModelProvider`, register, `skye.provider("shout")` (extension point) |
| `advanced/prompt_engineering.py` | prompts, models | `BasePromptBuilder`, few-shot, if/for, `[SYSTEM]`/`[USER]` roles |
| `serverless/lambda_handler.py` | models | client created once outside handler, warm-invocation pattern |
| `serverless/serverless_router_example.py` | router, store | router + external storage across invocations |
| `prompts/*` (12 files) | prompts | `BasePromptBuilder`/`MockPromptBuilder`: templates, few-shot, roles, multimodal, agent templates — **stale, "Jinja2" language, `sys.path` hacks** |

---

## Per-component capability map

Capabilities are drawn from source (`src/skye/**/__init__.py`, `base/interfaces/`, `base/completion.py`,
`base/messages.py`) and the steering requirements/design, then mapped to examples.

### base (layer 0, codename stratus)

Public surface: message types (`UserMessage`, `AssistantMessage`, `SystemMessage`, `CapabilityMessage`,
`ContentChunk`, `StreamChunk`); `CompletionRequest`/`CompletionResponse` (`to_message`, `get_output`,
`has_capability_calls`, `get_capability_calls`); `ConfigLoader` + `substitute_env_vars`; the `SkyeError` hierarchy
(`ProviderError`, `ConfigurationError`, `ValidationError`, `CapabilityExecutionError`, `MissingExtraError`); all Ports
in `base/interfaces/` (22 interface modules).

| Capability | Example(s) | Status |
|---|---|---|
| Message types (user/assistant/system/capability) | `basic/simple_completion.py` | Covered |
| `ContentChunk` content type | — | **MISSING** |
| `CompletionRequest`/`CompletionResponse` fields | `providers/structured_output_example.py` et al. | Covered (indirectly) |
| `response.to_message()` round-trip | `providers/multimodal_example.py` (prose) | Partial |
| Config precedence + `${VAR}` | `basic/configuration.py` | Covered |
| `MissingExtraError` on absent extra | — | **MISSING** |
| Error hierarchy (`ProviderError`, etc.) | — | **MISSING** (only `ValidationError` referenced) |

### auth (layer 0, codename ozone)

Source today: `auth/sigv4.py`, `auth/aws.py`, `auth/google.py` (stdlib SigV4 signer, Bedrock API key, Google
RS256 with `rsa`). Requirement 11 capability surface: strategies (API key/bearer, SigV4, OAuth2); credential sources
(environment, files, container creds, IMDSv2, token exchange, metadata server, cloud secret managers); 401 refresh +
retry; **custom credential source registration** (extension point); reading vendor-tool caches.

| Capability | Example(s) | Status |
|---|---|---|
| Any auth strategy / credential source | — | **MISSING (no `examples/auth/` dir)** |
| Custom credential source (extension point) | — | **MISSING** |

### models (layer 1, codename zephyr) — best covered

Surface: `skye.provider(name, **config)`; `complete`/`acomplete`/`stream`/`astream`; embeddings
`encode`/`encode_batch`/`aencode`/`aencode_batch` (`provider_type="embedding"`); providers openai/anthropic/
bedrock/azure/google/cohere; `TokenCounter.count_tokens`/`count_message_tokens`; `CostCalculator.calculate_cost`/
`add_custom_pricing`/`get_pricing`; `ImageHandler` multimodal; structured output via `response_schema`; DecisionModel
(Jev) Port; custom provider + bring-your-own `Runnable` extension points.

| Capability | Example(s) | Status |
|---|---|---|
| `skye.provider` + `complete` | `basic/quickstart.py`, all provider examples | Covered |
| `acomplete` / `stream` / `astream` | `basic/async_and_streaming.py`, `advanced/streaming.py` | Covered |
| openai/anthropic/bedrock/azure/google | `providers/*_example.py` | Covered |
| cohere language provider | — (only cohere *embeddings*) | **MISSING** |
| Embeddings encode/encode_batch/aencode | `providers/embeddings_example.py` | Covered |
| Multimodal image inputs | `advanced/multimodal.py`, `providers/multimodal_example.py` | Covered (prose-heavy) |
| Structured output (`response_schema`) | 3 files | Covered **but pydantic (D24 violation)** |
| Token counting (approx stdlib + `tiktoken` extra per D25) | — | **MISSING** |
| Cost estimate + custom pricing (R19) | — | **MISSING** |
| DecisionModel / Jev | — | **MISSING** |
| Custom provider (extension point) | `advanced/custom_providers.py` | Covered |
| Bring-your-own `Runnable` | `providers/bring_your_own_adapter.py` | Covered |
| Retry / `ProviderError` mapping (R9.2) | — | **MISSING** |

### store (layer 1, codename lake)

Backends exported: `InMemoryBackend`, `FileSystemBackend`, `DynamoDBBackend`, `RedisBackend`, `PostgreSQLBackend`,
`DurableFunctionBackend` (all behind `StorageBackend` Port). Per D30 PostgreSQL is its own `postgres` extra; file,
in-memory, DynamoDB are core; Redis via `memory` extra.

| Capability | Example(s) | Status |
|---|---|---|
| Backends used standalone via `StorageBackend` | — (only as router state) | **MISSING (no `examples/store/` dir)** |
| File / DynamoDB / Redis / Postgres backend | partial (router state only) | **MISSING** |
| Custom store backend (extension point) | — | **MISSING** |

### router (layer 2, codename jet) — well covered

Surface: `ModelRouter`, `ModelTarget`, `RouteConfig`, `FallbackConfig`, `RetryPolicyConfig`,
`AllowedFailsPolicyConfig`, `RoutingStrategy`, health (`get_model_health`), rate limiting (tpm/rpm), cooldown,
`register_model`, `set_fallbacks`, YAML config (`load_router_config`, extra `yaml`), `${VAR}` substitution.

| Capability | Example(s) | Status |
|---|---|---|
| Router with targets + strategies | `routing/basic_routing.py` | Covered |
| Fallbacks, health, usage, cooldown | `routing/fallbacks_and_health.py` | Covered |
| YAML config + `${VAR}` | `routing/yaml_config.py`, `yaml_config_example.py` | Covered |
| External storage for router state | `serverless/serverless_router_example.py` | Covered |
| `register_model` / `set_fallbacks` direct API | docstring only | Partial |

### tools (layer 2, codename updraft) — well covered except MCP facets

Surface: `@capability`, `LocalFunctionCapability`, `RemoteAPICapability`, `MCPCapability`, `create_mcp_client`
(built-in + `impl="fastmcp"`), `MCPServerClient`, `MCPToolCapability`, `MCPPrompt`/`MCPPromptArgument` (prompt facet,
D26), `Resource` (resource Port, D26), `CapabilityRegistry`, `CapabilityCallHandler`, `CapabilityCall`,
`CapabilityResult`, `CapabilitySchema`.

| Capability | Example(s) | Status |
|---|---|---|
| Local function capability | `capabilities/local_function.py`, `advanced/function_calling.py` | Covered |
| Remote API capability | `capabilities/remote_api.py` | Covered |
| MCP client (built-in) list/call tools | `capabilities/mcp_client.py` | Covered |
| MCP via `fastmcp` (`impl="fastmcp"`) | — | **MISSING** |
| MCP prompts facet (`MCPPrompt`, D26) | — | **MISSING** |
| MCP resources (`Resource`, D26) | — | **MISSING** |
| `CapabilityRegistry` (register/search) | — | **MISSING** |
| Custom tool via registry (extension point) | — | **MISSING** (only `@capability` shown) |

### prompts (layer 2, codename cirrus) — covered but stale

Surface: `BasePromptBuilder` (`register_template`, `render`), stdlib engine (`{{ }}`, `if`/`elif`/`else`, `for`,
filters per D20), few-shot, role markers, template composition, multimodal content. Note: `prompts` extra is empty
(engine is stdlib).

| Capability | Example(s) | Status |
|---|---|---|
| Templates + render to messages | `advanced/prompt_engineering.py`, `prompts/basic_usage.py` | Covered |
| Few-shot | `prompts/few_shot_learning.py`, `advanced/prompt_engineering.py` | Covered |
| Roles | `prompts/message_roles*.py` | Covered |
| if/for/filters (stdlib engine) | `advanced/prompt_engineering.py` | Covered |
| Multimodal content in templates | `prompts/multimodal_content.py` | Covered |
| — | all `prompts/*` | **Stale: "Jinja2" language, `MockPromptBuilder`, `sys.path` hacks (D20)** |

### memory (layer 2, codename dew)

Source today: only `MemoryEntry` (**a `pydantic.BaseModel`** in `memory/__init__.py`). Requirement 12 / memory Port:
store/retrieve conversation and state memory; semantic search via embeddings; backends via `store`. Extra `memory`
(redis).

| Capability | Example(s) | Status |
|---|---|---|
| Any memory usage | — | **MISSING (no `examples/memory/` dir)** |
| Custom memory (extension point per O20) | — | **MISSING** |

### guard (layer 2, codename halo)

Source: `guard/__init__.py` is `__all__ = []` (declared-but-minimal). Requirement: safety filters, pre-flight checks,
`safety` + `decision` Ports.

| Capability | Example(s) | Status |
|---|---|---|
| Input/output safety validation | — | **MISSING (no `examples/guard/` dir)** |

### policy (layer 2, codename isobar)

Source: minimal. Requirement 4/D9: authorizer Port (principal, action, resource → permit/forbid), Cedar-ish policy
(open decisions O9/O10).

| Capability | Example(s) | Status |
|---|---|---|
| Authorizer usage | — | **MISSING (no `examples/policy/` dir)** |

### observe (layer 2, codename radar)

Source: `observe/__init__.py` is `__all__ = []`. Requirement 18: events/logs/metrics/traces, `observer` +
`event_handler` Ports, custom exporter extension point.

| Capability | Example(s) | Status |
|---|---|---|
| Observer / exporter usage | — | **MISSING (no `examples/observe/` dir)** |
| Custom exporter (extension point) | — | **MISSING** |

### gateway (layer 3, codename horizon)

Source: minimal. Requirement 10/44-48: the library acting as an MCP server, toolset per operation, authorizer on
every listing/call. (Open decision O19 may fold gateway into `tools` — but an example of "Skye as MCP server" still
belongs somewhere.)

| Capability | Example(s) | Status |
|---|---|---|
| Expose capabilities as an MCP endpoint | — | **MISSING (no `examples/gateway/` dir)** |

### agents (layer 3, codename cyclone)

Source: `agents/registry.py` exports `REACT`, `ReActAgent`, `create_agent`, `get_agent_type`, `list_agent_types`,
`register_agent_type` (ReAct placeholder + agent-type registry). Requirement 5/design: agent loop, hooks, steps,
retries, optional services by injection. Several defaults open (O11-O13).

| Capability | Example(s) | Status |
|---|---|---|
| Create/run an agent (`create_agent`, ReAct) | — | **MISSING (no `examples/agents/` dir)** |
| Agent with hooks / tools / memory | — | **MISSING** |
| Custom agent type (`register_agent_type`, extension point) | — | **MISSING** |

### teams (layer 3, codename front)

Source: minimal. Requirement 5/D7/D8: compose `Runnable` units toward a shared objective; roles as free strings owned
by `teams`. Extra `teams` empty.

| Capability | Example(s) | Status |
|---|---|---|
| Build a team of `Runnable`s with roles | — | **MISSING (no `examples/teams/` dir)** |

### flows (layer 3, codename stream)

Source: minimal. Requirement 5: sequence `Runnable` units into steps; cycle detection. Extra `flows` empty.

| Capability | Example(s) | Status |
|---|---|---|
| Sequence `Runnable`s into a flow | — | **MISSING (no `examples/flows/` dir)** |

---

## Consolidated list of missing examples (to reach full coverage)

Grouped by component. Proposed paths follow the O20 convention `examples/<component>/`. Each is one small script the
`tests/examples` harness can run offline.

### base
- `examples/base/content_chunks.py` — build and inspect `ContentChunk`/`StreamChunk` content types.
- `examples/base/errors.py` — the `SkyeError` hierarchy: catch `ProviderError`, `ConfigurationError`,
  `ValidationError`, `CapabilityExecutionError`, and `MissingExtraError` (raised when an extra is absent).

### models
- `examples/models/token_counting.py` — approximate stdlib count vs exact with the `tiktoken` extra (D25).
- `examples/models/cost_tracking.py` — `CostCalculator.calculate_cost`, `add_custom_pricing`, per-request cost (R19).
- `examples/models/cohere.py` — `skye.provider("cohere")` language completion (only embeddings exist today).
- `examples/models/decision_model.py` — the DecisionModel (Jev) Port: finite option set in, choice + probabilities out.
- `examples/models/retry_and_errors.py` — transient-error retry (R9.2) and `ProviderError` mapping.

### auth (no dir today)
- `examples/auth/credential_sources.py` — API-key/bearer, SigV4, env/file/IMDSv2 sources (non-interactive, D11/D12).
- `examples/auth/custom_credential_source.py` — register a custom credential source (extension point, O20).

### store (no dir today)
- `examples/store/backends.py` — use `StorageBackend` directly: in-memory, file, DynamoDB (core), Redis (`memory`
  extra), PostgreSQL (`postgres` extra per D30).
- `examples/store/custom_backend.py` — one new module implementing the storage Port (extension point).

### tools
- `examples/tools/mcp_fastmcp.py` — `create_mcp_client(target, impl="fastmcp")` (extra `mcp`) returning identical types.
- `examples/tools/mcp_prompts_and_resources.py` — MCP prompt facet (`MCPPrompt`) returning `base` messages and MCP
  `Resource` list/read by URI (D26).
- `examples/tools/registry.py` — register and search capabilities with `CapabilityRegistry` (custom-tool extension).

### prompts
- Rewrite the `prompts/` set (see contradictions) rather than add new files; no capability gap.

### memory (no dir today)
- `examples/memory/conversation_memory.py` — store/retrieve conversation + state through the memory Port.
- `examples/memory/custom_memory.py` — a custom memory implementation (extension point, O20).

### guard (no dir today)
- `examples/guard/safety_filters.py` — input/output validation and a pre-flight decision check.

### policy (no dir today)
- `examples/policy/authorizer.py` — authorizer Port returning permit/forbid for (principal, action, resource).

### observe (no dir today)
- `examples/observe/telemetry.py` — events/metrics/traces through the `observer` Port.
- `examples/observe/custom_exporter.py` — register a custom exporter (extension point).

### gateway (no dir today)
- `examples/gateway/mcp_server.py` — expose Skye capabilities as an MCP endpoint with an authorizer on listing/call
  (keep even if O19 moves the catalogue into `tools`).

### agents (no dir today)
- `examples/agents/react_agent.py` — `create_agent`/ReAct loop with a model and tools.
- `examples/agents/agent_with_hooks.py` — inject memory/guard/observe via hooks (optional services by injection).
- `examples/agents/custom_agent_type.py` — `register_agent_type` (extension point).

### teams (no dir today)
- `examples/teams/team_of_runnables.py` — compose `Runnable`s with free-string roles toward a shared objective.

### flows (no dir today)
- `examples/flows/sequential_flow.py` — sequence `Runnable`s into steps; show cycle detection.

### Extension-point coverage summary (O20)
Covered: custom provider (`advanced/custom_providers.py`), bring-your-own `Runnable`
(`providers/bring_your_own_adapter.py`). **Missing: custom credential source, custom store backend, custom tool via
registry, custom exporter, policy, custom memory, agent-with-hooks, custom agent type, team, flow.**

---

## Examples that contradict current decisions (rewrite before use)

| File | Contradiction | Decision | Fix |
|---|---|---|---|
| `advanced/structured_output.py` | user schema is `pydantic.BaseModel` (+ enum/nested) | D24 | Rewrite schema as a `@dataclass`; `response_schema` already accepts "a class with `model_validate_json`" per `base/completion.py`, so the example must show the dataclass path, not pydantic. |
| `providers/structured_output_example.py` | `pydantic.BaseModel` + `Field(...)` validation | D24 | Same; replace `Field(min_length=...)` validation prose with dataclass-based shaping. |
| `basic/simple_completion.py` | `structured_output_example()` uses `pydantic.BaseModel` | D24 | Rewrite that function to a dataclass. |
| `providers/multimodal_example.py` | prose shows `pydantic.BaseModel` schema | D24 | Update the embedded snippet to a dataclass. |
| `prompts/*.py` (12 files) | "Jinja2" language, `MockPromptBuilder` alias, `sys.path.insert` hacks | D20, R13 | Rewrite against the stdlib engine, drop the Jinja2 wording and the `MockPromptBuilder` alias, install-and-import normally (no `sys.path`). |
| `providers/router_example.py` | empty 0-byte file | — | Delete or write a real router example (routing is already covered in `routing/`). |

Notes:
- **Not a contradiction for examples:** the core *library* still uses pydantic internally
  (`router/config_models.py`, `tools/capability_models.py`, `tools/schema.py`, `memory/__init__.py`,
  `base/completion.py` references). D24 explicitly defers moving existing core models (open decision O4). The example
  rule is narrower — examples must not *present pydantic as the standard* to users, which the four structured-output
  files do.
- **Provider name `google` (D19) is correct** in `providers/google_example.py` and the registry
  (`src/skye/models/__init__.py` registers `"google"`), so no Vertex-AI rename is outstanding in examples.
- No LangChain-style names (`BaseMessage`, `HumanMessage`, `Document`, `Embeddings`, `OutputParser`, `Callback`)
  were found in `examples/`.

---

## Components with NO examples directory, and whether the spec implies one

The spec/steering treat every component as having a user-facing surface and O20 explicitly proposes an example per
component including extension points. So every "none" below is a genuine gap, not an intentional omission.

| Component | Example dir? | Spec implies an example? | Why |
|---|---|---|---|
| auth | none | Yes | R11 extension point (custom credential source) + strategies users configure |
| store | none | Yes | R12 backends + custom-backend extension point |
| memory | none | Yes (optional extra) | memory Port, custom memory (O20) |
| guard | none | Yes (optional) | `safety` Port, pre-flight checks |
| policy | none | Yes | authorizer Port used by gateway/agents |
| observe | none | Yes | `observer` Port + custom-exporter extension point |
| gateway | none | Yes | the MCP-server story (R44-48); keep even if O19 folds it into `tools` |
| agents | none | Yes (optional) | agent loop, hooks, `register_agent_type` extension point |
| teams | none | Yes (optional) | compose `Runnable`s with roles (D7/D8) |
| flows | none | Yes (optional) | sequence `Runnable`s (R5) |
| base | none (incidental only) | Partly | errors + content types deserve their own small examples |

`models`, `router`, `tools`, `prompts` have dirs; `serverless` is a cross-cutting usage dir (fine to keep).

---

## Recommendations (implement nothing here)

1. **Close the structured-output D24 gap first** — the three pydantic examples are the most visible contradiction and
   the shape the owner will react to. Rewrite them around a dataclass + `response_schema`.
2. **Add one example per uncovered component** (the ~24 files listed above), prioritising the layer-3 runtime
   (`agents`, `teams`, `flows`) and the gateway, since those define the orchestration UI the owner wants to feel
   before the import-length spec (O21).
3. **Cover the missing extension points** (custom credential source, store backend, tool-via-registry, exporter,
   policy, memory, agent-with-hooks, custom agent type) — O20 calls these out specifically.
4. **Rewrite the stale `prompts/` set** to the stdlib engine and drop the `sys.path`/`Jinja2`/`MockPromptBuilder`
   legacy; delete the empty `providers/router_example.py`.
5. Keep every new example runnable under `tests/examples` (offline, fake network) so each is an executable spec of the
   public API, consistent with O20.
6. Import-style changes are **out of scope** here (O21); write the new examples in the current explicit-path style and
   let the import-length spec rewrite them later.
