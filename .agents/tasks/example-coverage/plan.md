# Implementation Plan — Example coverage for Skye's public interface

Write ~24 new example scripts (plus README entries) so the owner can see every component's call shape. Each
runs offline under `tests/examples` (fake network, no optional libs). Ground truth is `src/skye`, not the
report prose. New examples use the current explicit-path import style (`import skye` + `from skye.base.messages import UserMessage`).

## What I verified during exploration

- Harness: `tests/examples/test_examples.py` runs every `examples/**/*.py` (except `__init__.py`) via `runpy` with
  `run_name="__main__"`, offline, keys from `DUMMY_ENV`, HTTP answered by `tests/examples/fake_network.py`.
  An example "fails" if its output contains a FAILURE_MARKER line (`❌`, `✗`, `Traceback`, `ProviderError:`,
  `ConfigurationError:`, `ValidationError:`, `AttributeError`, `TypeError`, `KeyError`) unless the line also
  contains the word `Expected`. So: never print those markers on a normal path; a deliberately-provoked error
  line must contain `Expected`.
- House style (see `examples/basic/quickstart.py`, `examples/providers/bring_your_own_adapter.py`,
  `examples/advanced/custom_providers.py`, `examples/capabilities/local_function.py`): module docstring, a
  `def main() -> None:` (or `async def main()` run with `asyncio.run(main())`), `if __name__ == "__main__": main()`,
  and an early `return` with a printed skip message when an env var / optional lib / unimplemented API is absent.
- Baseline is green: `uv run pytest tests/examples -q` → 87 passed.
- **Pre-existing lint/format debt** (not caused by this task): `uv run ruff check examples/` reports 1144 errors and
  `uv run black --check examples/` would reformat 38 of 44 files today, on files this task must NOT touch (stale
  `prompts/`, pydantic structured-output files, etc.). Ruff lint set is `E,F,I,N,W,UP`. **Assumption:** the two
  whole-tree commands in the task's "final verification" cannot pass without touching out-of-scope files, so the
  real acceptance bar for THIS task is: (a) `uv run pytest tests/examples -q` passes, and (b) ruff+black are clean
  **on the newly added paths**. Each new file must be written ruff-clean (sorted imports, no unused imports) and
  black-formatted (line length 100) so it adds zero new violations. This is called out as a gap for the owner.
- API ground-truth highlights that change what each example can do (see Digest for exact signatures):
  - `base`: `ContentChunk(text, metadata, chunk_id, source)` and `StreamChunk(id, delta, finish_reason, index)` are
    real dataclasses in `skye.base.messages` / `skye.base.completion`. Error hierarchy in `skye.base.exceptions`:
    `SkyeError`, `ProviderError(message, provider, status_code=…)`, `ConfigurationError`, `ValidationError(message, field, value)`,
    `CapabilityExecutionError(message, capability_name)`, `MissingExtraError(extra, missing, package=None)`. **Live.**
  - `models`: `TokenCounter.count_tokens/count_message_tokens` (stdlib approx offline; tiktoken only with `openai`
    extra, absent in harness → approximate path runs). `CostCalculator.calculate_cost/add_custom_pricing/get_pricing/list_models`.
    Custom provider via `ProviderRegistry.register_model_provider` + `BaseModelProvider`. **Live.**
    - `cohere` is registered **only as an embedding provider**, not a language model provider → `skye.provider("cohere")`
      for completion does NOT exist. `DecisionModel` is a Port only (no concrete model). `retry_and_errors` can show
      the real `ProviderError` type and catch shape, but there is no public "force a retry" switch. → these three are
      **proposed-interface, guarded**.
  - `auth`: real stdlib authenticators in `skye.auth.aws` (`SigV4Authenticator`, `BedrockApiKeyAuthenticator`,
    `bedrock_authenticator`, `CredentialProvider`, `AwsCredentials`) implementing the `AuthenticationInterface` Port
    (`apply(method, url, headers, body=b"") -> dict[str,str]`). A user can write a custom authenticator satisfying the
    Port. **Live** (both auth examples can run real code).
  - `store`: `skye.store` exports the backends; `InMemoryBackend` and `FileSystemBackend` are core and async
    (`connect/get/set/increment/get_multiple/set_multiple`). DynamoDB/Redis/Postgres need optional libs (boto3/redis/asyncpg,
    all forbidden-at-import and absent) → guard those branches. Custom backend = subclass `StorageBackend`. **Live.**
  - `tools`: `CapabilityRegistry` (register/get/list_all/search/execute), `create_mcp_client(target, impl=…)`,
    `MCPPrompt`/`MCPPromptArgument`, `Resource`. `impl="fastmcp"` needs the `mcp` extra (fastmcp forbidden-at-import) →
    guard. Built-in MCP client talks HTTP; fake_network answers `/mcp` JSON-RPC, but it needs a reachable URL — follow
    `examples/capabilities/mcp_client.py` which defaults to localhost and the harness fake answers it. **registry.py Live;
    mcp_fastmcp.py and mcp_prompts_and_resources.py: live where built-in works, guarded for the fastmcp/extra parts.**
  - `memory`: only `MemoryEntry` (a pydantic model — do NOT present it as the user shape) + `MemoryInterface` Port
    (`store/retrieve/get_by_id/delete`, over `MemoryEntryLike` Protocol). No concrete memory store. → **proposed-interface,
    guarded**: user implements `MemoryInterface` with a dataclass entry satisfying `MemoryEntryLike`.
  - `guard`: `__all__ = []`. `SafetyFilterInterface` + `SafetyResult` Port exist in `skye.base.interfaces.safety`. →
    user implements the Port; **live at Port level** (no src concrete needed; the example defines its own filter).
  - `policy`: minimal. `AuthorizerInterface` + `Decision` Port in `skye.base.interfaces.authorizer`. → user implements
    the Port; **live at Port level**.
  - `observe`: `__all__ = []`. `ObserverInterface` (`log_event/record_metric/start_trace/end_trace`, `EventType`) and
    `EventHandlerInterface` Ports. → user implements the Ports; **live at Port level**.
  - `gateway`: minimal, no API. The MCP-server story has no public entry point in src. → **proposed-interface, guarded**:
    compose from `CapabilityRegistry` + `AuthorizerInterface` to show the intended "authorizer on every list/call" shape,
    with a top-of-file docstring stating it targets the planned gateway API and a guarded early return around any absent part.
  - `agents`: real `create_agent/register_agent_type/get_agent_type/list_agent_types/REACT/ReActAgent`. `ReActAgent.invoke`
    raises `NotImplementedError` (placeholder). A user CAN register a custom agent type (any `Runnable` factory) and run it →
    `custom_agent_type.py` is **live**. `react_agent.py` and `agent_with_hooks.py` show the intended shape but must NOT invoke
    the ReAct placeholder (it raises) → **proposed-interface, guarded** (print the intended call, guard the `.invoke` that is
    not implemented yet).
  - `teams`/`flows`: minimal, no API, but the `Runnable` Port (`async invoke(input)->output`) is real and composable. →
    **proposed-interface, guarded**, built purely from the `Runnable` Port with user-defined `Runnable`s, docstring noting the
    planned `teams`/`flows` API, guarded return before any not-yet-existing orchestration call.

Classification summary (the coder records this in each file's module docstring and in the README):
- Live (run real library code end to end): `base/content_chunks.py`, `base/errors.py`, `models/token_counting.py`,
  `models/cost_tracking.py`, `auth/credential_sources.py`, `auth/custom_credential_source.py`, `store/backends.py`,
  `store/custom_backend.py`, `tools/registry.py`, `guard/safety_filters.py`, `policy/authorizer.py`,
  `observe/telemetry.py`, `observe/custom_exporter.py`, `agents/custom_agent_type.py`.
- Live-with-guarded-extra (real built-in path, guard the optional-lib branch): `tools/mcp_fastmcp.py`,
  `tools/mcp_prompts_and_resources.py`.
- Proposed-interface, guarded (shows intended call shape, guarded early return, no fake API invented):
  `models/cohere.py`, `models/decision_model.py`, `models/retry_and_errors.py`, `memory/conversation_memory.py`,
  `memory/custom_memory.py`, `gateway/mcp_server.py`, `agents/react_agent.py`, `agents/agent_with_hooks.py`,
  `teams/team_of_runnables.py`, `flows/sequential_flow.py`.

## Rules every new file obeys

- Create a client with `skye.provider(name, **config)`, variable `client` (`embedder` for embeddings), only where a
  client is actually needed. Examples that only show a Port/dataclass need no client.
- Dataclasses (not pydantic) for any user-facing data shape the example defines. Modern hints (`list[str]`, `X | None`),
  Python 3.10+, Google-style docstrings where a public shape is shown. No LangChain-style names.
- Any optional lib (tiktoken/boto3/redis/asyncpg/fastmcp/...) imported lazily inside a `try/except ImportError`/`MissingExtraError`
  guard that prints a short skip note and continues — never a top-level import of a forbidden-at-import library.
- Standalone script shape with `main()` and `if __name__ == "__main__": main()`; print a skip message + `return` when a
  prerequisite (env var, extra, unimplemented src API) is absent, so the harness stays green.
- No FAILURE_MARKER substring on a normal path. A deliberately-shown error must print a line containing `Expected`.
- ruff-clean (sorted imports, no unused imports; rules E,F,I,N,W,UP) and black-formatted at line length 100.

---

- [ ] 1. Create `examples/base/` with `content_chunks.py` and `errors.py` (both Live).
      `content_chunks.py`: build/inspect `ContentChunk` (text, metadata, chunk_id, source; `str(chunk)`) and
      `StreamChunk` (id, delta, finish_reason, index); show accumulating stream deltas into text. `errors.py`: raise
      and catch each `SkyeError` subclass with its real constructor signature, catching `SkyeError` as the umbrella;
      raise `MissingExtraError("postgres", "asyncpg")` to show the absent-extra message (print it, no marker/`Expected`).
      Files: examples/base/content_chunks.py, examples/base/errors.py
      Verify: `uv run pytest tests/examples -q -k base` passes; `uv run ruff check examples/base examples/README.md` and
      `uv run black --check examples/base` clean.

- [ ] 2. Create `examples/models/` with the five model examples.
      Live: `token_counting.py` (`TokenCounter.count_tokens`/`count_message_tokens`; note tiktoken-exact path needs the
      `openai` extra and show the stdlib approximate numbers that run offline), `cost_tracking.py`
      (`CostCalculator.calculate_cost`, `add_custom_pricing`, `get_pricing`, per-request cost from a real
      `skye.provider("openai")` response's `usage`). Proposed-interface guarded: `cohere.py` (docstring: cohere is an
      embedding provider today; show the intended `skye.provider("cohere")` completion call behind a guard that detects
      cohere is not a registered model provider via `ProviderRegistry` and returns), `decision_model.py` (import the
      `DecisionModel`/`DecisionResult` Port, define a tiny local `Runnable`-style decider satisfying the Port to show the
      call shape, note no concrete decision model ships yet), `retry_and_errors.py` (show catching real `ProviderError`
      and the SkyeError hierarchy; note retry policy is configured at the router level — reference `examples/routing`).
      Files: examples/models/token_counting.py, cost_tracking.py, cohere.py, decision_model.py, retry_and_errors.py
      Verify: `uv run pytest tests/examples -q -k models` passes; ruff+black clean on `examples/models`.

- [ ] 3. Create `examples/auth/` with `credential_sources.py` and `custom_credential_source.py` (both Live).
      `credential_sources.py`: construct `BedrockApiKeyAuthenticator(api_key=...)` and `SigV4Authenticator(region, service,
      AwsCredentials(...))` from `skye.auth.aws`; call `.apply("GET", url, {})` to show the returned signed headers;
      mention env/file/IMDS sources via `CredentialProvider` without hitting the network (pass explicit/static creds so
      no metadata call fires — IMDS is refused by the fake anyway). `custom_credential_source.py`: define a user class
      implementing `AuthenticationInterface` (`apply(method, url, headers, body=b"") -> dict[str,str]`), assert it is an
      instance of the runtime-checkable Port, and use it to add an `Authorization` header.
      Files: examples/auth/credential_sources.py, examples/auth/custom_credential_source.py
      Verify: `uv run pytest tests/examples -q -k auth` passes; ruff+black clean on `examples/auth`.

- [ ] 4. Create `examples/store/` with `backends.py` and `custom_backend.py` (both Live).
      `backends.py`: use `InMemoryBackend` and `FileSystemBackend` (core) async API end to end (`connect`, `set`, `get`,
      `increment`, `get_multiple`); for DynamoDB/Redis/PostgreSQL, construct them inside a `try/except
      (ImportError, MissingExtraError)` that prints a skip note (boto3/redis/asyncpg are absent). Use `asyncio.run(main())`.
      `custom_backend.py`: implement a new `StorageBackend` subclass (all abstract async methods) backed by a dict and
      exercise it. Clean up any temp file the FS backend creates (use `tempfile`).
      Files: examples/store/backends.py, examples/store/custom_backend.py
      Verify: `uv run pytest tests/examples -q -k store` passes; ruff+black clean on `examples/store`.

- [ ] 4b. (part of the store step) ensure no DynamoDB/Redis/Postgres module is left imported — the harness already strips
      forbidden modules, but the example must not import them at top level.

- [ ] 5. Create `examples/tools/` with `registry.py` (Live), `mcp_fastmcp.py` and `mcp_prompts_and_resources.py`
      (live built-in path, guarded extra). `registry.py`: build a `CapabilityRegistry`, `register` two `@capability`
      functions, `list_all`, `search("...")`, `execute(name, {...})` → show the `CapabilityMessage`. `mcp_fastmcp.py`:
      follow `examples/capabilities/mcp_client.py`; call `create_mcp_client(url, impl="fastmcp")` inside a
      `try/except (ImportError, MissingExtraError)` printing a skip note (fastmcp is the `mcp` extra, absent), and show
      that `impl="builtin"` returns the same types against the fake `/mcp`. `mcp_prompts_and_resources.py`: use the
      built-in client's `list_prompts`/`get_prompt` (→ base messages) and `list_resources`/`read_resource` (→ `Resource`);
      guard cleanly if the fake server advertises none. Import `MCPPrompt`, `MCPPromptArgument`, `Resource` to show the types.
      Files: examples/tools/mcp_fastmcp.py, examples/tools/mcp_prompts_and_resources.py, examples/tools/registry.py
      Verify: `uv run pytest tests/examples -q -k tools` passes; ruff+black clean on `examples/tools`.

- [ ] 6. Create `examples/memory/` with `conversation_memory.py` and `custom_memory.py` (both proposed-interface, guarded).
      Define a `@dataclass` entry satisfying `MemoryEntryLike` (id, content, memory_type, embedding, metadata, created_at)
      — NOT pydantic, do not import `MemoryEntry`. Implement `MemoryInterface` (`store/retrieve/get_by_id/delete`) in a
      small in-memory class and exercise it. Top-of-file docstring: states that a concrete memory store is not in src yet
      and this shows the intended Port-level shape. `conversation_memory.py` focuses on store/retrieve of conversation
      turns; `custom_memory.py` focuses on the extension point (user subclass of `MemoryInterface`).
      Files: examples/memory/conversation_memory.py, examples/memory/custom_memory.py
      Verify: `uv run pytest tests/examples -q -k memory` passes; ruff+black clean on `examples/memory`.

- [ ] 7. Create `examples/guard/safety_filters.py`, `examples/policy/authorizer.py`,
      `examples/observe/telemetry.py`, `examples/observe/custom_exporter.py` (Ports are real; examples define their own impls).
      `guard/safety_filters.py`: implement `SafetyFilterInterface` (`validate_input`/`validate_output`/`get_policies`)
      returning `SafetyResult`, run a safe and an unsafe input (print the unsafe verdict without a FAILURE_MARKER).
      `policy/authorizer.py`: implement `AuthorizerInterface.authorize(principal, action, resource) -> Decision`, show a
      permit and a forbid. `observe/telemetry.py`: implement `ObserverInterface` (log_event with `EventType`, record_metric,
      start/end trace) and drive it. `observe/custom_exporter.py`: implement `EventHandlerInterface` as a custom exporter
      and fire a few lifecycle hooks. Each file states at top whether it's Live/Port-level.
      Files: examples/guard/safety_filters.py, examples/policy/authorizer.py, examples/observe/telemetry.py, examples/observe/custom_exporter.py
      Verify: `uv run pytest tests/examples -q -k "guard or policy or observe"` passes; ruff+black clean on those dirs.

- [ ] 8. Create `examples/gateway/mcp_server.py` (proposed-interface, guarded).
      Top docstring: targets the planned gateway "Skye as an MCP server" API (R44-48), not yet in src. Build the intended
      shape from real parts: a `CapabilityRegistry` of exposed capabilities plus a user `AuthorizerInterface` that is
      consulted on each list/call, printing permit/forbid. Guard-return before any not-yet-existing gateway entry point.
      Files: examples/gateway/mcp_server.py
      Verify: `uv run pytest tests/examples -q -k gateway` passes; ruff+black clean on `examples/gateway`.

- [ ] 9. Create `examples/agents/` with `custom_agent_type.py` (Live), `react_agent.py` and `agent_with_hooks.py`
      (proposed-interface, guarded). `custom_agent_type.py`: define a `Runnable` factory, `register_agent_type("echo", ...)`,
      `create_agent("echo")`, `await agent.invoke(...)`, show `list_agent_types()`. `react_agent.py`: use `create_agent(REACT, ...)`
      to show the factory, but do NOT call the placeholder `.invoke` (it raises `NotImplementedError`) — guard with a note
      that the ReAct loop ships with the future agents spec. `agent_with_hooks.py`: show the intended injection of
      memory/guard/observe services (built from the Ports in steps 6-7) into an agent factory, guarded likewise.
      Register under a unique name and the harness restores the agent registry per-script (only the provider registry is
      restored by the harness, so use `register_agent_type(..., replace=True)` or a name unlikely to collide, and prefer a
      name local to the script).
      Files: examples/agents/custom_agent_type.py, examples/agents/react_agent.py, examples/agents/agent_with_hooks.py
      Verify: `uv run pytest tests/examples -q -k agents` passes; ruff+black clean on `examples/agents`.

- [ ] 10. Create `examples/teams/team_of_runnables.py` and `examples/flows/sequential_flow.py` (proposed-interface, guarded).
      Both built purely from the real `Runnable` Port: define two or three tiny user `Runnable`s. `team_of_runnables.py`:
      show composing them with free-string roles toward a shared objective (a small local coordinator), docstring noting the
      planned `teams` API. `sequential_flow.py`: chain them in order (output→input), and demonstrate cycle detection with a
      small local check that prints an `Expected` line when a cycle is configured. Guard-return before any not-yet-existing
      `teams`/`flows` orchestration call.
      Files: examples/teams/team_of_runnables.py, examples/flows/sequential_flow.py
      Verify: `uv run pytest tests/examples -q -k "teams or flows"` passes; ruff+black clean on those dirs.

- [ ] 11. Update `examples/README.md`: add a short category entry for each new directory (base, models, auth, store,
      tools additions, memory, guard, policy, observe, gateway, agents, teams, flows), noting for each whether its
      examples are Live or proposed-interface/guarded, to keep Requirement 24.1 satisfied. Do NOT rewrite the stale
      `prompts/` section or the pydantic examples (out of scope).
      Files: examples/README.md
      Verify: `uv run pytest tests/examples -q` → all pass (new count ≈ 87 + 24 new scripts); `uv run ruff check examples/README.md` clean.

- [ ] 12. Final integration check across all new examples.
      Run the full examples suite and scoped lint/format on every new path.
      Files: (none — verification only)
      Verify: `uv run pytest tests/examples -q` passes; `uv run ruff check examples/base examples/models examples/auth
      examples/store examples/tools examples/memory examples/guard examples/policy examples/observe examples/gateway
      examples/agents examples/teams examples/flows examples/README.md` reports no errors; `uv run black --check` on the
      same new dirs reports nothing to reformat. (Whole-tree `ruff check examples/` and `black --check examples/` fail on
      pre-existing out-of-scope files — see the gap note in "What I verified".)

## Digest

For each file the plan creates. All are NEW files (no existing block to change). Exact signatures the coder must use,
taken from source I read; the test that covers them is `tests/examples/test_examples.py` (auto-discovers every new
`examples/**/*.py`). Baseline verified: `uv run pytest tests/examples -q` → 87 passed today.

### Shared API facts (read; do not re-open these files to edit)
- `skye.provider(name, **config) -> ModelInterface | VectorEncoderInterface`; `provider_type="embedding"` for an embedder.
  (`src/skye/__init__.py`.)
- `skye.base.messages`: `UserMessage/AssistantMessage/SystemMessage(content=...)`, `CapabilityMessage(content, capability_id,
  capability_name)`, `ContentChunk(text, metadata={}, chunk_id=None, source=None)` with `__str__`→text.
- `skye.base.completion`: `StreamChunk(id, delta, finish_reason=None, index=0)`, `TokenUsage(prompt_tokens, completion_tokens,
  total_tokens)`, `CompletionResponse.usage/.content/.get_output()/.to_message()/.has_capability_calls()`.
- `skye.base.exceptions`: `SkyeError(message, details=None)`; `ProviderError(message, provider, status_code=None, **kw)`;
  `ConfigurationError(message, details=None)`; `ValidationError(message, field, value, **kw)` (also `ValueError`);
  `CapabilityExecutionError(message, capability_name, **kw)`; `MissingExtraError(extra, missing, package=None)` (also `ImportError`).
- `skye.models`: `TokenCounter.count_tokens(text, model)->int`, `count_message_tokens(list[SkyeMessage], model)->int`;
  `CostCalculator.calculate_cost(model, usage, custom_pricing=None)->float`, `.add_custom_pricing(model, prompt, completion)`,
  `.get_pricing(model)`, `.list_models()`; `ProviderRegistry.register_model_provider(name, cls)`, `BaseModelProvider`.
- `skye.auth.aws`: `SigV4Authenticator(region, service, credentials)`, `BedrockApiKeyAuthenticator(api_key=None)`,
  `bedrock_authenticator(region, *, api_key=None, ...)`, `CredentialProvider(...)`, `AwsCredentials(access_key, secret_key,
  session_token=None, expires_at=None)`; all authenticators have `.apply(method, url, headers, body=b"")->dict[str,str]`.
  Port: `skye.base.interfaces.authentication.AuthenticationInterface` (runtime-checkable Protocol).
- `skye.store`: `StorageBackend` (abstract async `connect/get/set(key,data,ttl=None)/increment(key,amount=1,ttl=None)/
  get_multiple(keys)/set_multiple(data,ttl=None)`); concrete `InMemoryBackend`, `FileSystemBackend` (core),
  `DynamoDBBackend/RedisBackend/PostgreSQLBackend/DurableFunctionBackend` (need optional libs).
- `skye.tools`: `capability` decorator (`@capability`, `.get_schema()`, `.execute()/.aexecute()`), `CapabilityRegistry()`
  (`register/get/list_all/search(query)/execute(name, args)->CapabilityMessage`), `create_mcp_client(target, impl="builtin"|"fastmcp")`,
  `MCPPrompt`, `MCPPromptArgument`, `Resource(uri, name, mime_type=None, description=None, text=None, data=None)`.
  MCP client Port methods: `list_tools/call_tool/list_prompts/get_prompt/list_resources/read_resource` (all async).
- `skye.base.interfaces.memory`: `MemoryInterface` (abstract `store(entry)->str`, `retrieve(query, limit=10, filters=None)`,
  `get_by_id(id)`, `delete(id)->bool`), `MemoryEntryLike` Protocol (id, content, memory_type, embedding, metadata, created_at).
  NOTE: `skye.memory.MemoryEntry` is pydantic — do not use it as the user shape.
- `skye.base.interfaces.safety`: `SafetyFilterInterface` (`validate_input/validate_output(content)->SafetyResult`,
  `get_policies()->list[str]`), `SafetyResult(is_safe, violations=[], confidence=1.0, metadata={})`.
- `skye.base.interfaces.authorizer`: `AuthorizerInterface.authorize(principal, action, resource)->Decision`,
  `Decision.PERMIT/Decision.FORBID`.
- `skye.base.interfaces.observer`: `ObserverInterface` (`log_event(EventType, dict)`, `record_metric(name, value, tags=None)`,
  `start_trace(name, metadata=None)->str`, `end_trace(trace_id, metadata=None)`), `EventType` enum.
  `skye.base.interfaces.event_handler.EventHandlerInterface` (8 lifecycle hooks: on_model_invoke_start/end/error,
  on_capability_invoke_start/end/error, on_execution_step, on_execution_complete).
- `skye.base.interfaces.runnable.Runnable` (runtime-checkable Protocol, `async invoke(input)->output`).
- `skye.base.interfaces.decision`: `DecisionModel` Protocol (`async decide(prompt, options)->DecisionResult`),
  `DecisionResult(choice, probabilities={})`.
- `skye.agents`: `REACT`, `ReActAgent` (placeholder; `invoke` raises NotImplementedError — do not call it),
  `create_agent(name, **opts)`, `register_agent_type(name, factory, *, replace=False)`, `get_agent_type`, `list_agent_types`.

### Files
- examples/base/content_chunks.py — Live. Uses `ContentChunk`, `StreamChunk`. Covered by test_examples (offline, no client).
- examples/base/errors.py — Live. Uses the full `SkyeError` hierarchy + `MissingExtraError`. No client.
- examples/models/token_counting.py — Live. `TokenCounter`; tiktoken-exact guarded (openai extra absent → approx path runs).
- examples/models/cost_tracking.py — Live. `CostCalculator` + a real `skye.provider("openai")` response's `.usage`.
- examples/models/cohere.py — Proposed-interface, guarded. Guard on `ProviderRegistry` not having a cohere *model* provider.
- examples/models/decision_model.py — Proposed-interface, guarded. `DecisionModel`/`DecisionResult` Port + local decider.
- examples/models/retry_and_errors.py — Proposed-interface, guarded. Real `ProviderError`; retry lives at router level.
- examples/auth/credential_sources.py — Live. `SigV4Authenticator`/`BedrockApiKeyAuthenticator`/`AwsCredentials`, `.apply`.
- examples/auth/custom_credential_source.py — Live. User impl of `AuthenticationInterface`; `isinstance(..., Port)` check.
- examples/store/backends.py — Live. `InMemoryBackend`+`FileSystemBackend` async; DynamoDB/Redis/Postgres guarded.
- examples/store/custom_backend.py — Live. User `StorageBackend` subclass.
- examples/tools/registry.py — Live. `CapabilityRegistry` register/search/execute with `@capability`.
- examples/tools/mcp_fastmcp.py — Live built-in path; `impl="fastmcp"` guarded (mcp extra absent).
- examples/tools/mcp_prompts_and_resources.py — Live built-in path; `MCPPrompt`/`Resource` types; guard if none advertised.
- examples/memory/conversation_memory.py — Proposed-interface, guarded. `MemoryInterface` impl + dataclass `MemoryEntryLike`.
- examples/memory/custom_memory.py — Proposed-interface, guarded. Extension-point `MemoryInterface` subclass.
- examples/guard/safety_filters.py — Live (Port-level). `SafetyFilterInterface`+`SafetyResult`.
- examples/policy/authorizer.py — Live (Port-level). `AuthorizerInterface`+`Decision`.
- examples/observe/telemetry.py — Live (Port-level). `ObserverInterface`+`EventType`.
- examples/observe/custom_exporter.py — Live (Port-level). `EventHandlerInterface` as a custom exporter.
- examples/gateway/mcp_server.py — Proposed-interface, guarded. `CapabilityRegistry`+`AuthorizerInterface`, guard planned API.
- examples/agents/custom_agent_type.py — Live. `register_agent_type`/`create_agent`/`list_agent_types` + a `Runnable`.
- examples/agents/react_agent.py — Proposed-interface, guarded. `create_agent(REACT)`; do not invoke the placeholder.
- examples/agents/agent_with_hooks.py — Proposed-interface, guarded. Service injection shape via Ports.
- examples/teams/team_of_runnables.py — Proposed-interface, guarded. Built from `Runnable` Port + free-string roles.
- examples/flows/sequential_flow.py — Proposed-interface, guarded. `Runnable` chain + local cycle-detection (`Expected` line).
- examples/README.md — add one category entry per new directory (R24.1). Modify only; do not touch the prompts section.

### Verification (real project commands)
- Build/compile + run: `uv run pytest tests/examples -q` (discovers and runs every new file offline; must stay green).
- Lint: `uv run ruff check <new dirs> examples/README.md` (rules E,F,I,N,W,UP; must be clean on new paths).
- Format: `uv run black --check <new dirs>` (line length 100; must report nothing to reformat).
- Scope caveat recorded above: the task's whole-tree `ruff check examples/` / `black --check examples/` cannot pass
  without editing out-of-scope pre-existing files; verification for THIS task is scoped to the new paths.
