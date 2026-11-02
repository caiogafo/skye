# Implementation Plan: tools

## Overview

Milestones in build order for the `tools` component (codename updraft): the capability interface and schema first, then the
registry and the capability kinds (local function, remote API, decorator), the call handler and errors, the tri-faceted MCP
client with its single conversion boundary and its built-in/`fastmcp` implementations, and finally the open conformance work
left by the migration. Status is judged from the code in `src/skye/tools` and the tests in `tests/unit/tools` and
`tests/differential/test_mcp_differential.py`, not from the former `capability-support` checkboxes. Each task cites the
steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it honors. Task IDs
cited from other documents are `tools:N.k`.

## Tasks

- [ ] 1. Capability interface and schema
  - [x] 1.1 `CapabilityInterface` (get_schema, execute, aexecute)
    - Evidence: `src/skye/tools/interface.py`; `tests/unit/tools/test_capability_interface.py`.
    - _Requirements: 16.1, 16.2_
  - [x] 1.2 `CapabilitySchema` (name, description, parameters, returns)
    - Evidence: `src/skye/tools/schema.py`; `tests/unit/tools/test_capability_schema.py`.
    - _Requirements: 16.1_
  - [ ] 1.3 Move `CapabilitySchema` / `CapabilityResult` / `CapabilityCall` off pydantic to dataclasses (D24)
    - Note: `src/skye/tools/schema.py` (`CapabilitySchema`) and `src/skye/tools/capability_models.py` (`CapabilityResult`) are still `pydantic.BaseModel` subclasses, and `CapabilityCall` is re-exported from `src/skye/base/completion.py` (pydantic). Under D24/O4 new data structures are dataclasses and must raise `ValidationError` with field context on invalid data. Coordinate with the `base` spec (O4) before changing the shared completion models.
    - _Requirements: 16.1; D24_

- [ ] 2. Registry and capability kinds
  - [x] 2.1 `CapabilityRegistry` behind the registry Port (register, get, list, namespaces, search)
    - Evidence: `src/skye/tools/registry.py`; `tests/unit/tools/test_capability_registry.py`.
    - _Requirements: 6.1, 6.2, 16.2_
  - [x] 2.2 `LocalFunctionCapability` (signature + docstring -> schema)
    - Evidence: `src/skye/tools/local_function.py`; `tests/unit/tools/test_local_function_capability.py`.
    - _Requirements: 6.1, 6.2_
  - [x] 2.3 `RemoteAPICapability` over `base/http.py` (no third-party HTTP client)
    - Evidence: `src/skye/tools/remote_api.py` (imports `skye.base.http`); `tests/unit/tools/test_remote_api_capability.py`.
    - _Requirements: 6.1, 6.2, 7.3, 10.7_
  - [x] 2.4 `@capability` decorator
    - Evidence: `src/skye/tools/decorator.py`; `tests/unit/tools/test_capability_decorator.py`.
    - _Requirements: 6.1, 22.1_

- [ ] 3. Capability call handling and errors
  - [x] 3.1 `CapabilityCallHandler` (provider-agnostic parse/validate/execute/format)
    - Evidence: `src/skye/tools/capability_call_handler.py`, `src/skye/tools/capability_models.py` (`CapabilityResult`); `tests/unit/tools/test_capability_call_handler.py`, `test_capability_models.py`.
    - _Requirements: 9.10, 16.2_
  - [x] 3.2 `CapabilityError` hierarchy on `SkyeError` with kept context
    - Evidence: `src/skye/tools/exceptions.py`; `tests/unit/tools/test_exceptions.py`.
    - _Requirements: 18.1_
  - [x] 3.3 Capability terminology ("Capability", not "Tool") in types and exports
    - Evidence: `src/skye/tools/__init__.py` exports (`CapabilityInterface`, `CapabilityCall`, `CapabilityResult`, ...); `tests/unit/tools/test_capability_exports.py`.
    - _Requirements: 22.1, 22.2_
  - [x]* 3.4 Structured events for capability calls, results and errors
    - Evidence: structured `logger.info/error(..., extra={...})` in `src/skye/tools/registry.py` and `capability_call_handler.py`.
    - _Requirements: 18.3_

- [ ] 4. Tri-faceted MCP client and the boundary
  - [x] 4.1 `MCPClientPort` and `BuiltinMCPClient` (stdlib JSON-RPC over HTTP, consume-only)
    - Evidence: `src/skye/tools/mcp_client.py` (`MCPClientPort`, `BuiltinMCPClient`, `MCPToolCapability`); `tests/unit/tools/test_mcp_client.py`, `test_mcp_stdlib_prototype.py`.
    - _Requirements: 10.1, 10.2_
  - [x] 4.2 Single conversion boundary `mcp_boundary.py` (stdlib only, reject malformed)
    - Evidence: `src/skye/tools/mcp_boundary.py`; `tests/budget/test_boundary_rule.py` (`test_mcp_boundary_has_no_third_party_import`, `test_mcp_boundary_returns_skye_types_for_dict_and_library_objects`).
    - _Requirements: 10.1, 10.6_
  - [x] 4.3 `create_mcp_client` explicit `impl`; `FastMCPClient` behind the same Port (lazy fastmcp)
    - Evidence: `src/skye/tools/mcp_client.py` (`create_mcp_client`), `src/skye/tools/mcp_fastmcp.py` (`FastMCPClient`, lazy `missing_extra("fastmcp", extra="mcp")`).
    - _Requirements: 10.2, 10.3, 10.4; D15, D16_
  - [x]* 4.4 Differential tests keep both clients equal
    - Evidence: `tests/differential/test_mcp_differential.py` (skips when `fastmcp` absent).
    - _Requirements: 10.4_

- [ ] 5. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Migration conformance (open)
  - [ ] 6.1 Move `Resource` behind a new resource Port in `base` (D26)
    - Note: `src/skye/tools/mcp_resource.py` states "No base Port" and `Resource` is a `tools`-local dataclass; the code lags D26. Define the resource Port in `base` (list and read by URI, MIME type, text or bytes) and have the MCP client in `tools` implement it, so `prompts` and `memory` consume MCP resources through `base`. Coordinate with the `base` spec.
    - _Requirements: 10.5; D26_
  - [ ] 6.2 MCP prompt facet returns `base` messages, not `PromptBuilderInterface` (D26)
    - Note: conformance check — `get_prompt` / `to_prompt_messages` already return `base` `UserMessage`/`AssistantMessage` (`src/skye/tools/mcp_client.py`, `src/skye/tools/mcp_boundary.py`) and `tools` must not import `prompts` or implement `PromptBuilderInterface`. Add an explicit test asserting the prompt facet returns `base` messages and that `tools` imports no `prompts` symbol, so the rule is guarded.
    - _Requirements: 10.5, 10.1; D26_
  - [ ] 6.3 Remove the legacy MCP probes (`LEGACY_TOOLS_PROBES`)
    - Note: `src/skye/tools/mcp_capability.py` (`MCPCapability`) and `src/skye/tools/mcp_server_client.py` (`MCPServerClient`) import `fastmcp` to raise a probe error and carry placeholder stdio/subprocess framing; they are the only `fastmcp` importers outside `mcp_fastmcp.py`, tracked in `LEGACY_TOOLS_PROBES` in `tests/budget/test_boundary_rule.py`. Delete these two modules (superseded by the tri-faceted client), drop their exports from `src/skye/tools/__init__.py`, and remove the `LEGACY_TOOLS_PROBES` entry so `tools` imports `fastmcp` only in `mcp_fastmcp.py`.
    - _Requirements: 10.7_
  - [ ] 6.4 Fix the order-dependent MCP unit tests
    - Note: `tests/unit/tools/test_mcp_capability.py` and `test_mcp_server_client.py` set `sys.modules["fastmcp"] = MagicMock()` at module import, which leaks a fake `fastmcp` into other tests, and `test_execute_raises_not_supported_error` depends on the event loop left by test ordering. Remove the module-level `sys.modules` assignment (patch locally instead) and make the sync-`execute` test install its own loop, so selection stays per-call and `import skye` never sees a fake `fastmcp`. These tests go away with task 6.3 if those modules are deleted.
    - _Requirements: 10.4_
  - [ ] 6.5 Stop gating CI on the size of the `mcp` extra (open decision O23, owner approval first)
    - Note: the default MCP client is the built-in stdlib one (`create_mcp_client`); `fastmcp` is opt-in (`impl="fastmcp"`), so by Requirement 7.10 its weight is not gated. After task 6.3, if approved: take `mcp` out of the footprint gate (`budgets.toml`, the matrix in `.github/workflows/budgets.yml`, `tests/budget/test_workflow_matrix.py`), report its size in `docs/budgets.md` as known debt (+50.6 MB on Linux, limit 48 never raised), and keep the test that `fastmcp` is imported only through the extra.
    - _Requirements: 7.10, 7.11, 15.1; O23_

- [ ] 7. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional (tests/observability) and can be skipped for a faster path.
- Status reflects the code in `src/skye/tools` and `tests/` at migration time, not the former `capability-support` checkboxes.
- `tools` carries no third-party library; `fastmcp` is the separate `mcp` extra, imported lazily only in `mcp_fastmcp.py`
  (design "Extras and budgets"; Requirement 10.7, 7.3).
- Open items at migration: 1.3 (pydantic -> dataclasses under D24/O4), 6.1 (`Resource` behind a `base` Port, D26), 6.2
  (prompt-facet conformance), 6.3 (remove the legacy `MCPCapability` / `MCPServerClient` probes), 6.4 (order-dependent MCP
  unit tests).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3", "2.4", "1.3"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3", "3.4"] },
    { "id": 3, "tasks": ["4.1", "4.2"] },
    { "id": 4, "tasks": ["4.3", "4.4"] },
    { "id": 5, "tasks": ["6.1", "6.2", "6.3", "6.5"] },
    { "id": 6, "tasks": ["6.4"] }
  ]
}
```
