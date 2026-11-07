---
inclusion: always
---

# Project rules (Skye)

Binding, project-wide rules for every change. They are enforced by `tests/budget/test_steering.py` and the `budgets` CI
workflow: removing or weakening one needs a reviewed, owner-approved change to that test (see CODEOWNERS).
The requirements, the design and the owner's decisions are in `10-requirements.md`, `11-design.md` and `12-decisions.md`
(load them when you need them). Conventions for steering and specs are in `20-repo.md`.

## Architecture in one paragraph
Components sit in four layers (ordinal 0 to 3); a component imports only from lower layers plus `base`, never sideways, and a
same-layer contract is a Port in `base`. Runtime components compose work only through the `Runnable` Port and get optional services
(`policy`, `guard`, `observe`, `memory`) through Ports, never by import. The exact allowed-imports matrix is in `11-design.md` and is
enforced by `tests/budget/test_import_matrix.py`; do not restate it elsewhere. Each component has a codename, a watermark that
appears in four sanctioned places and never in a path, import, file name or class name (`tests/budget/test_codenames.py`).

## Serverless first
- Skye is built for serverless architectures, where the size of the library and its cold start make a difference. Install only what is needed: the core is the standard library, and nothing forces a third-party library on the user.
- No multiprocessing, no background threads, no long-lived processes.
- All durable state is **external** (DynamoDB first; Redis where used). Do not rely on in-process caches or connection pools
  surviving between invocations.

## Dependencies, in order of preference
1. the Python standard library;
2. libraries the serverless runtime already provides (on AWS Lambda: boto3, botocore, urllib3, ...);
3. pure-Python packages (`py3-none-any` wheel), only when 1 and 2 cannot do the job;
4. **never** a compiled (C/Rust) package in the core.

`boto3` is optional, not a core dependency. Provider SDKs and optional libraries are imported **lazily** (LazyImporter), never at
module import time. Prefer thin REST adapters over SDKs. Core dependencies are governed by `budgets.toml`, not restated here.

## Budgets only go down
Size and load budgets live in `budgets.toml` and are enforced by `tests/budget` and the `budgets` workflow on every pull request.
A budget may only shrink; raising a number needs a reason in the PR and a review from the file owner (`.github/CODEOWNERS`).

## One package, extras
Skye is a **single package** (`skyeai`) with optional **extras**, versioned together. The base install carries the always-present
components; optional components install via their own extra. Each extra declares **exactly** the third-party libraries its
component imports; an extra that imports none is empty and listed in `known_empty` in `budgets.toml`. One extra never pulls another.

## Python
- Always run commands through **uv** (`uv run pytest`, `uv run ruff check`, `uv run mypy`, `uv run black`); never plain `pytest`,
  `python` or `pip`. **Black** formats, **Ruff** lints, **mypy** runs in strict mode; configuration lives in `pyproject.toml`.
- Minimum **Python 3.11** (`target-version = py311`, D49). Modern type hints: `list[str]`, `dict[str, Any]`, `X | None`, not `List`,
  `Dict` or `Optional[...]`. All public APIs are fully type-hinted. Python only; the library is I/O bound.
- **Dataclasses, not pydantic.** New data structures use `dataclasses`; do not add pydantic models. Pydantic and tenacity are
  removed from the core (D49: `dependencies = []`); code that still imports them is legacy being migrated. Steering must never present pydantic as the standard.
- I/O provides sync and async forms; async methods are prefixed with `a` (`acomplete`, `aencode`). Never block in an async function.
- Errors use the `SkyeError` hierarchy and keep context (`raise ... from e`). Use context managers for resources.
- Public APIs have Google-style docstrings; a component's package docstring ends with `Codename: <name>.`.
- Log with structure (message plus `extra={...}`), not f-string interpolation; use the standard levels.

## Naming
- Interfaces follow `{Concept}Interface` (`ModelInterface`, `CapabilityInterface`, `VectorEncoderInterface`,
  `EventHandlerInterface`, `ContentReaderInterface`).
- Create the client of a provider with `<pkg>.provider(name, **config)`, in the style of `boto3.client`; name the variable `client`, and use no alias.
- **Capability, not Tool**, in type names: `CapabilityCall`, `CapabilityResult`, `CapabilityCallHandler`. The MCP wire terms stay as
  MCP defines them, and the component folder is literally `tools`.
- Messages: `SkyeMessage`, `UserMessage`, `AssistantMessage`, `SystemMessage`, `CapabilityMessage`; `ContentChunk`;
  `CompleteRequest`, `CompleteResponse`.
- **Avoid LangChain-style names**: no `BaseMessage`, `HumanMessage`, `AIMessage`, `Document`/`DocumentLoader`, `Embeddings`,
  `OutputParser`, `Callback`/`CallbackHandler`.

## Workflow
- Features go through Kiro specs in order, **requirements → design → tasks**, each approved before the next. Requirements and high-level
  design are written in `10-requirements.md` and `11-design.md` and only cited by the spec; tasks live only in the spec (see `20-repo.md`).
- One component = one spec folder = one package = one docs section = one budget entry, all with the same short name (`^[a-z]{3,7}$`).
- `docs/` is a wiki with one section per component; see `20-repo.md`.

## Licence
MIT. Do not copy code from other projects without attribution, and never from LiteLLM `enterprise/` (see `CONTRIBUTING.md`).
