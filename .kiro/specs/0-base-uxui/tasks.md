# Implementation Plan: uxui

## Overview

This plan closes the findings of the 2026-11-03 audit of the public surface (`.agents/tasks/uxui-audit-report.md`), grouped by
mechanism: the import facades (done before this spec), name collisions, Port conformance, naming and vocabulary, the examples, and
docstrings. Each task cites the local requirement it satisfies (`N.k` of `requirements.md`) and, where useful, the steering
requirement or decision directly. A task blocked on an open decision says so and is not started before the owner decides (never
guess the answer in code). Tasks that belong to another spec (`models:8.2`, `prompts-support` task 3) are not repeated here.

## Tasks

- [x] 1. Short public import paths (decision D34, done before this spec)
  - [x] 1.1 Facades `skye.interfaces`, `skye.data`, `skye.messages`, `skye.completion`, `skye.exceptions`, `skye.config`
    - Evidence: `src/skye/interfaces.py`, `data.py`, `messages.py`, `completion.py`, `exceptions.py`, `config.py`; each only imports and re-exports its source in `skye/base`.
    - _Requirements: 1.1, 1.3_
  - [x] 1.2 66 examples and the documentation rewritten to the short paths
    - Evidence: `examples/`, `docs/` import only `skye`, `skye.interfaces`, `skye.data` or a component package; no `skye.base.*`.
    - _Requirements: 1.1_
  - [x] 1.3 `tests/budget/test_public_imports.py`
    - Evidence: scans `examples/`, `docs/`, `README.md`; fails on a path deeper than two levels or through `skye.base`.
    - _Requirements: 1.1, 1.2_
  - [ ] 1.4 Facade purity test
    - Add `tests/budget/test_facade_purity.py`: parse each facade module with `ast`; fail on a `def`, a `class`, or an assignment other
      than `__all__`/a lazy-name table; fail when a name in `__all__` is not defined by the module it re-exports from. See
      `design.md` "Facades only re-export".
    - _Requirements: 1.2; D34_

- [ ] 2. One name, one home
  - [ ] 2.1 Duplicate-name test
    - Add `tests/budget/test_unique_names.py`: walk `src/skye` with `ast`, collect public `class` definitions, fail on a name defined
      in two modules except `KNOWN_DUPLICATES` (seeded with `CapabilitySchema`: 3 modules, `CapabilityExecutionError`: 2); the list
      only shrinks, like `known_leaks`.
    - _Requirements: 2.1_
  - [ ] 2.2 Resolve `CapabilityExecutionError`
    - One definition in `base.exceptions`; `tools.exceptions` re-exports it; update the differential test that imports the `tools`
      one for the reason recorded in the audit (finding 15).
    - _Requirements: 2.1_
  - [ ] 2.3 Resolve `CapabilitySchema`
    - Three definitions (`base.interfaces.capability`, `base.capability_schema`, `tools.schema`, the last pydantic). Coordinate with
      the pydantic removal of `0-base-structure` (group 14, O4): the pydantic one is retired there, not duplicated here; this task
      makes the other two agree (one dataclass, one re-export) and removes the entry from `KNOWN_DUPLICATES` once the pydantic one
      is gone.
    - _Requirements: 2.1; O4_

- [ ] 3. Port contracts
  - [ ] 3.1 Signature-aware compliance checker
    - Extend `utils/validation.validate_interface_compliance` (or add a sibling function) to compare, per Port method: parameter
      names and kinds in order (ignoring `self`/`cls`), `def`/`async def`/async-generator form, and the return annotation by name
      when both sides declare one; accept `Protocol` Ports, not only `ABC`. See `design.md` "Port conformance by signature".
    - _Requirements: 5.2; 16.7 of steering_
  - [ ] 3.2 One test for every built-in implementation
    - `tests/unit/test_port_compliance.py`: one parametrized case per (implementation, Port) pair found in `src`, plus a short
      reference implementation for each exported Port that has none; `KNOWN_MISMATCHES` seeded with the three P1 findings below and
      only shrinking.
    - _Requirements: 5.2_
  - [ ] 3.3 Fix `ModelInterface.astream` typing
    - `async def astream(...) -> Iterator[StreamChunk]` becomes an async generator typed `AsyncIterator[StreamChunk]`; update the
      Port docstring example to `async for`.
    - _Requirements: 5.1; 16.6 of steering_
  - [ ] 3.4 Align `select_model` sync/async
    - `ModelRouterInterface.select_model` and `ModelRouter.select_model` must agree. Check the callers first, then change the one
      that costs less: the audit found the Port sync and the router `async def`, so a caller that follows the Port gets a coroutine
      where it expects a `str`.
    - _Requirements: 5.1; 16.6 of steering_
  - [ ] 3.5 The model Port's call shape — blocked on O24
    - Once O24 is decided, make `ModelInterface.complete`/`stream`/`acomplete`/`astream` match the chosen shape so `custom_providers.py`
      and `bring_your_own_adapter.py` can implement the Port directly, with no `type: ignore[misc,override]`.
    - _Requirements: 5.1; O24_
  - [ ] 3.6 Reconcile six unimplemented Ports — blocked on O29 for the per-row choice
    - `TokenCounterInterface`, `CostCalculatorInterface`, `ConfigLoaderInterface`, `MultimodalHandlerInterface`,
      `ErrorHandlerInterface`, `RouteRegistryInterface`: for each, make the implementation satisfy the Port, change the Port, or
      remove it from `__all__` until a component needs it, per the owner's choice in O29.
    - _Requirements: 7.1; O29_
  - [ ] 3.7 Port docstring footer
    - Add `Raises:`, `Missing:`, `Concurrency:` to each of the 23 Port modules under `base/interfaces/`; a test
      (`tests/unit/test_port_docstrings.py`) fails on a missing label. Content comes from reading each implementation, not guessed.
    - _Requirements: 6.1_
  - [ ] 3.8 Reference implementations for untested Ports
    - For `MultimodalHandlerInterface`, `CostCalculatorInterface`, `TokenCounterInterface`, `ErrorHandlerInterface`,
      `ConfigLoaderInterface` (named by neither a test nor an example per the audit) and any Port still bare after 3.6, add the
      small in-memory implementation that 3.2's test exercises.
    - _Requirements: 7.1_
  - [ ] 3.9 Split the largest Ports — blocked on O29 for the role boundaries
    - `ModelRouterInterface` (16 methods) and `PromptBuilderInterface` (22 methods) split by role (selection, health, configuration;
      rendering, registry, schema) once O29 settles the boundaries; a caller that needs only one role types against it.
    - _Requirements: 7.1; O29_
  - [ ] 3.10 Protocol-vs-ABC convention — blocked on O25
    - Write the rule in steering once O25 is decided (which Ports are `Protocol`, which stay abstract bases) and apply it to
      `MCPClientPort` → `MCPClientInterface` if the O28 naming choice also lands.
    - _Requirements: 7.1; O25; O28_

- [ ] 4. Naming and vocabulary
  - [ ] 4.1 Naming convention and vocabulary in the wiki
    - Add the convention of Requirement 22.5 (verbs/nouns, `x`/`ax`, `get_`/`list_`/`set_`/`register`) and the Port/Interface and
      capability/tool/function-call glossary lines (22.1, 22.3) to `docs/glossary.md`.
    - _Requirements: 3.1, 4.1, 4.2_
  - [ ] 4.2 `MCPClientPort` naming — blocked on O28
    - Rename to `MCPClientInterface` if O28 chooses that, or document it as the third exception alongside `Runnable`, `DecisionModel`,
      `StorageBackend`.
    - _Requirements: 3.1; O28_
  - [ ] 4.3 Guessability aliases — blocked on O27, one sub-task per alias
    - `CompletionResponse.text`, `CapabilityRegistry.list()`, `skye.provider(..., kind="embedding")`, `tool_choice`, `ainvoke`: add
      only the ones the owner accepts in O27, each as a thin alias with no new behavior.
    - _Requirements: 3.1; O27_
  - [ ] 4.4 File naming in `models/` and `tools/`
    - Rename for consistency (`openai_compatible.py`'s classes, the `mcp_*` files of `tools`) once 1.1 to 1.3 make the import path
      irrelevant to users; update internal imports only, no public path changes.
    - _Requirements: 3.2_
  - [ ] 4.5 `skye.router` storage re-exports — blocked on O28
    - Keep as a documented alias or drop at 0.1.0, per O28.
    - _Requirements: 2.1; O28_
  - [ ] 4.6 Placeholder packages raise a clear error — blocked on O28
    - If O28 chooses it, add a module-level `__getattr__` to `skye.flows`, `skye.gateway`, `skye.teams`, `skye.policy`, `skye.observe`,
      `skye.guard` that raises `ImportError("skye.<name> is planned, not available yet")` on an attribute a user might expect.
    - _Requirements: 3.2; O28_

- [ ] 5. Examples
  - [ ] 5.1 Delete the empty example
    - Remove `examples/providers/router_example.py` (0 bytes); routing is already covered by `examples/routing/`.
    - _Requirements: 9.3_
  - [ ] 5.2 Guard the four tracebacks
    - `capabilities/mcp_client.py`, `tools/mcp_fastmcp.py` (check for a server first, print how to start one or set
      `MCP_SERVER_URL`), `serverless/serverless_router_example.py` (catch the `${VAR}` `ConfigurationError`),
      `routing/yaml_config_example.py` (stop after showing the loaded router instead of making a real call with a placeholder key).
    - _Requirements: 8.1, 8.2_
  - [ ] 5.3 Offline demo provider — blocked on O26
    - Once O26 is decided, replace the "skipping" branches of `basic/quickstart.py`, `async_and_streaming.py`,
      `models/cost_tracking.py`, `advanced/function_calling.py`, `advanced/streaming.py`, `advanced/structured_output.py`,
      `routing/fallbacks_and_health.py` with a call to the chosen demo path, printing which mode ran.
    - _Requirements: 8.1; O26_
  - [ ] 5.4 Offline-run test
    - `tests/examples/test_examples_offline.py`: run each example in a subprocess with provider environment variables unset and
      outbound sockets refused; fail on a non-zero exit or on `Traceback` in the output.
    - _Requirements: 8.1_
  - [ ] 5.5 Install-line test and fix
    - `tests/budget/test_install_lines.py`: find every `pip install skyeai[...]` in `examples/`, `docs/`, `README.md`; fail when the
      extra does not exist or is in `known_empty`. Fix `examples/README.md` (lines about `[openai]`, `[openai,anthropic,bedrock]`),
      `providers/openai_example.py`, `providers/google_example.py`, `capabilities/mcp_server.py` (the `fastmcp` version range),
      and the package docstring (6.1 also touches this file).
    - _Requirements: 10.1, 10.2_
  - [ ] 5.6 README-matches-folder test and fix
    - `tests/budget/test_example_readmes.py`: a folder's README lists exactly its `*.py` files; fails on `basic/README.md`'s
      `streaming_example.py` reference and on folders with no README (`auth/`, `base/`, `memory/`, `models/`, `prompts/`, `store/`,
      `tools/`). Add the missing READMEs (five lines: what you learn, the command, what you see, what you need) and a numbered
      reading order in `examples/README.md`.
    - _Requirements: 11.1, 11.2_
  - [ ] 5.7 Merge or cut duplicate examples
    - Keep the short one of each pair and link the long one as "reference" or delete it: `advanced/function_calling.py` over
      `capabilities/function_calling_example.py` and `providers/function_calling_example.py`; `routing/yaml_config_example.py` over
      `routing/yaml_config.py`; the short `prompts/` duplicates are handled by `prompts-support` task 3, not here.
    - _Requirements: 9.3_
  - [ ] 5.8 Size test and split
    - `tests/budget/test_example_size.py`: fail above about 80 lines unless listed in `KNOWN_LONG` (seeded with the nine files over
      300 lines named in the audit); split or cut each, moving exhaustive variants to the docs wiki.
    - _Requirements: 9.1_
  - [ ] 5.9 Plain-output test and fix
    - `tests/budget/test_example_output_style.py`: fail on a `"=" * N` banner row or an emoji character in a `print` literal, unless
      listed; remove the banners and emoji rows, aligning labels as `basic/configuration.py` already does.
    - _Requirements: 9.2_
  - [ ] 5.10 The value-proposition example — blocked on O26 for the demo path
    - `examples/advanced/value_proposition.py` (or similar): one prompt, run against two or three providers, with a fallback when
      one fails; runnable against the demo provider once O26 lands.
    - _Requirements: 9.3; O26_

- [ ] 6. Docstrings and discoverability
  - [ ] 6.1 Fix the package docstring
    - `src/skye/__init__.py`: `response.text` → `response.content`; the stale `pip install skyeai[bedrock]` line.
    - _Requirements: 12.1_
  - [ ] 6.2 Docstring doctest gate
    - `tests/unit/test_docstrings.py`: run `doctest` on the package docstring and each Port module docstring, with
      `# doctest: +SKIP` on network-needing lines.
    - _Requirements: 12.1_
  - [ ] 6.3 Extension page
    - `docs/base/extending.md` (or similar, in the `base` wiki section): one table, kind of extension / Port / registry / example
      file / status, seeded from "Extension points" of `11-design.md` and extended to every exported Port; a docs test fails when a
      name in `skye.interfaces.__all__` has no row.
    - _Requirements: 13.1, 13.2_
  - [ ] 6.4 Document import cost per package
    - `docs/budgets.md`: one line per component package stating whether it loads pydantic, until the pydantic removal (O4) makes
      this moot.
    - _Requirements: 7.4 of steering; O4_

- [ ] 7. Checkpoint
  - [ ] 7.1 Ensure all tests pass, ask the user if questions arise
    - Run `uv run pytest tests/ -q` and `uv run pytest tests/budget -q`; confirm every new allowlist (`KNOWN_DUPLICATES`,
      `KNOWN_MISMATCHES`, `KNOWN_LONG`) is non-empty only where a real, named debt remains.

## Notes

- Tasks blocked on an open decision are not started before the owner decides; do not guess the answer in code (see `design.md`,
  "Open decisions and the tasks they block").
- `models:8.2` (pydantic structured-output examples) and `prompts-support` task 3 (stale `examples/prompts/`) are tracked in their
  own specs and are not duplicated here, even though they appear in the audit (findings behind Requirement 24's pydantic/D20
  contradictions).
- Group 1 is done; its evidence is the committed facades and `tests/budget/test_public_imports.py`.

## Task Dependency Graph

See `design.md`, "Task Dependency Graph", for the wave ordering (facades and the first tests run first; allowlist-clearing repairs
follow; decision-blocked tasks are the last wave before the checkpoint).
