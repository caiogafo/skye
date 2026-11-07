---
component: none (cross-cutting: the public surface a user touches)
previous_name: uxui
---

# Design Document: uxui
Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Ports, Composition, Public API and lazy imports, The `.skye` language, Extension points, Correctness properties, Testing).
The system view (facades, the Port rules, the execution primitive and `ToolProvider`, the router shorthand, the new checks) is in those sections.
This file holds the detail of this spec: the baseline of the audit, the mechanism of each check, where each lives, and which open decision blocks
which task.

## Overview
The work has three parts, taken from the audit of 2026-11-03: the examples a newcomer runs (findings 1 to 12), the names and imports a user types
(13 to 24) and the contracts of the Ports an extension author implements (25 to 35). Three follow-up reports of 2026-11-04 (familiarity,
simplicity, tools), reconciled in `.agents/tasks/uxui-reconciliation.md`, add the execution primitive, the `ToolProvider` Port, the router
shorthand, the typed `provider()` and the guessability aliases (the "Follow-up reports" section below). The import paths are done (decision D34);
everything else is open. The design adds no runtime feature to the library. It adds checks (tests that fail on the thing the audit found), repairs the defects the
checks reveal, and rewrites the examples to the standard of Requirement 24. Two choices hold for all of it:
- A rule is enforced by a test where it can be, with an allowlist that **only shrinks** (the pattern of `known_leaks` in `budgets.toml`): the
  test is written first, fails on the known cases, and each repair removes its entry.
- A fix that belongs to one component is a task here, marked with the component it touches, because the audit is the one place that sees the
  whole surface. A fix that another spec already tracks stays there (`models:8.2` for the pydantic structured-output examples, `prompts:5`
  for the stale `examples/prompts/`).

## Baseline: the 35 findings
Level P1 blocks or misleads a user, P2 costs time, P3 is polish. "Done" means the work exists and a test guards it. Task numbers are in `tasks.md`.

| # | Finding | Level | Requirement | Task | Open decision |
|---|---|---|---|---|---|
| 1 | The first examples end in "skipping": nothing runs offline | P1 | 24.4 | 5.3, 5.4 | D38 |
| 2 | Install lines are wrong after the extras changes | P1 | 24.6 | 5.5 | |
| 3 | Examples end in a raw traceback | P1 | 24.4 | 5.2, 5.4 | |
| 4 | `providers/router_example.py` is empty | P1 | 24.5 | 5.1 | |
| 5 | `examples/prompts/` is stale (Jinja2, `sys.path`) | P1 | D20, 30.9 | `prompts:5` | |
| 6 | READMEs name files and commands that do not exist | P2 | 24.8 | 5.6 | |
| 7 | Overlapping examples (function calling three times, YAML twice) | P2 | 24.5 | 5.7 | |
| 8 | Large files hide the point (nine over 300 lines) | P2 | 24.5 | 5.8 | |
| 9 | Placeholder keys reach the real network | P2 | 24.4 | 5.2, 5.3 | D38 |
| 10 | The value proposition (one prompt, several providers, fallback) is not shown | P2 | 24.2 | 5.10 | |
| 11 | Banners, emoji and `print` walls | P3 | 24.7 | 5.9 | |
| 12 | No learning path | P3 | 24.8 | 5.6 | |
| 13 | The package docstring shows `response.text`, which does not exist | P1 | 15.9 | 6.1, 6.2 | D39 |
| 14 | The commonest imports need `skye.base.*` | P1 | 7.14 | 1.1 to 1.3 (done) | |
| 15 | Three `CapabilitySchema`, two `CapabilityExecutionError` | P1 | 22.4 | 2.1 to 2.3 | |
| 16 | `Interface`, "Port", `Runnable`, `DecisionModel`, `StorageBackend`, `MCPClientPort` | P2 | 22.3 | 4.1, 4.2, 3.10 | D37, D40 |
| 17 | Capability, tool and function call used interchangeably | P2 | 22.1, 22.3 | 4.1, 4.3 | D39 |
| 18 | Import depth is inconsistent | P2 | 7.14 | 1.1 to 1.3 (done) | |
| 19 | The same names exported from `skye.router` and `skye.store` | P2 | 22.4 | 4.5 | D40 |
| 20 | Sync and async naming: `invoke` without `ainvoke` | P2 | 22.5 | 4.1, 4.3 | D39 |
| 21 | Verbs without a rule (`get_`, `list_`, `set_`, `register_`, ...) | P3 | 22.5 | 4.1, 4.3 | D39 |
| 22 | File and class names in `models/` and `tools/` | P3 | 22.6 | 4.4 | dropped: names stay |
| 23 | Empty packages look public; stale install text in the docstring | P3 | 22.6, 15.9 | 4.6, 6.1 | D40 |
| 24 | Import cost is not predictable from the name (pydantic in `router`, `tools`) | P3 | 7.4 | 6.4 | D49 |
| 25 | `ModelInterface` does not describe the call users make | P1 | 16.6 | 3.5 | D36 |
| 26 | `ModelInterface.astream` is typed as an `Iterator` and awaited | P1 | 16.6 | 3.3 | |
| 27 | `select_model` is sync in the router Port, `async` in the router | P1 | 16.6 | 3.4 | |
| 28 | Two ways to be a Port (20 abstract bases, 4 `Protocol`s) | P2 | 16.7 | 3.10 | D37 |
| 29 | The compliance checker compares names only | P2 | 16.7 | 3.1, 3.2 | |
| 30 | Six Ports have an implementation that does not satisfy them | P2 | 16.9 | 3.6 | D41 |
| 31 | Thirteen abstract Ports have no inheriting implementation; five have no test or example | P2 | 16.9 | 3.8 | |
| 32 | Error contracts are missing (`Raises:` in 8 of 23 Port modules) | P2 | 16.8 | 3.7 | |
| 33 | Overlapping Ports (two storage Ports, `Runnable` and `ModelInterface`) | P3 | 16.9 | 3.6, 3.9 | D41 |
| 34 | Uneven Port size (1 to 22 methods) | P3 | 16.9 | 3.9 | D41 |
| 35 | A user cannot find which Port to implement | P3 | 15.10 | 6.3, 4.1 | |

## From the 27 rules to the requirements
The audit ended in 27 rules (`.agents/tasks/uxui-audit-rules.md`). Each is now a criterion of steering; none is stated only here.

| Rules | Subject | Criterion |
|---|---|---|
| 1 to 4, 8 | at most two levels, never through `base`, never into a module inside a component, the fixed public paths, the shortest working import in examples | 7.14, D34 |
| 5, 12 | short names for new modules; a file named after its one idea | 22.6 |
| 6 | one name, one home | 22.4 |
| 7 | facades only re-export | 7.15 |
| 9 | verbs, nouns, `x` and `ax`, `get_`, `list_`, `set_`, `register` | 22.5 |
| 10, 11 | `*Interface` and its exceptions; capability, tool and function call explained once | 22.3, 22.1 |
| 13, 14 | a Port has the signature and the `def` form of the real call | 16.6 |
| 15 | the error contract of a Port | 16.8 |
| 16 | conformance checked on signatures, one test for all built-in implementations | 16.7 |
| 17, 18 | no export without an implementation and a test; large Ports split by role | 16.9 |
| 19 | every example runs with no key | 24.4 |
| 20, 21 | one idea, about 80 lines, no empty file, no duplicate | 24.5 |
| 22 | install lines are true | 24.6 |
| 23 | plain output | 24.7 |
| 24, 25 | a README per folder that matches it; a reading order | 24.8 |
| 26 | the first docstring runs | 15.9 |
| 27 | docs use the same import paths as the examples | 7.14 |

## Mechanisms
Each check is a deterministic test under `tests/` that needs no network.

### Facades only re-export (task 1.4)
`tests/budget/test_public_imports.py` already scans `examples/`, `docs/` and `README.md`. A second test parses each facade module with `ast`
(`skye/interfaces.py`, `data.py`, `messages.py`, `completion.py`, `exceptions.py`, `config.py`) and fails on a `def`, a `class` or an assignment
other than `__all__` and lazy-name tables, and on a name in `__all__` that its source module does not define.

### One name, one home (task 2.1)
`tests/budget/test_unique_names.py` walks `src/skye` with `ast`, collects the `class` definitions whose name has no leading underscore, and fails
when one name is defined in two modules. A re-export (an `import`) is not a definition. An allowlist `KNOWN_DUPLICATES` starts with
`CapabilitySchema` (three modules) and `CapabilityExecutionError` (two) and may only shrink; an entry that is no longer a duplicate fails the
test, as `known_leaks` does. The home of each name is the lowest layer that defines it: for both, `base`. The repair (2.2, 2.3) replaces the
others with a re-export; the pydantic `CapabilitySchema` of `tools` leaves with the pydantic removal of `0-base-structure` (group 14).

### Port conformance by signature (tasks 3.1, 3.2, 3.8)
`utils/validation.validate_interface_compliance` today requires `issubclass` and checks that the abstract method names exist. The new form takes
a class and a Port and compares, for every public method of the Port:
- the parameter names and kinds, in order (positional, keyword, `*args`, `**kwargs`), ignoring `self` and `cls`; a default is not compared;
- the form: `def`, `async def`, async generator (`inspect.iscoroutinefunction`, `inspect.isasyncgenfunction`);
- the return annotation by name, only when both sides have one.
A method the implementation adds is allowed; a method it omits, a parameter it renames or a `def` it makes `async def` fails. For a `Protocol`
the methods are read from the protocol's own members, so the same function serves both kinds (decision D37 does not change the checker).
`tests/unit/test_port_compliance.py` gets one parametrized case per pair (built-in implementation, Port) and, for each exported Port that has
none, a reference implementation of a few lines kept in the test (Requirement 16.9). Known mismatches (`ModelInterface` against
`BaseModelProvider`, `ModelRouterInterface.select_model`) are listed in `KNOWN_MISMATCHES`, which only shrinks. The comparison done for the audit
took 30 lines, so the checker stays small.

### Port docstring footer (task 3.7)
Each Port module docstring ends with a footer of three labelled lines: `Raises:`, `Missing:` (what is returned when the key or item is absent) and
`Concurrency:` (threads and tasks; for a hook or an observer, "exceptions are logged and swallowed"). A test reads the exported Ports and fails
on a Port whose docstring lacks the three labels. The wording of each contract comes from reading the implementations, not from guessing.

### Examples (tasks 5.1 to 5.10)
- **Offline run, no traceback (5.4).** `tests/examples` runs each example in a subprocess with the provider variables removed and sockets
  refused, and fails on a non-zero exit code or on `Traceback` in the output. It complements the existing in-process run against the fake network.
- **Size and plain output (5.8, 5.9).** One test counts lines per example and fails above the limit (about 80) unless the file is in
  `KNOWN_LONG`; another fails on a banner row (`"=" * 60`) or an emoji. Both lists only shrink.
- **README against folder (5.6).** A test lists the `*.py` files of each example folder and fails when the folder's README omits one, names a file
  that is not there, or names a command whose file does not exist. `examples/README.md` carries the numbered reading order.
- **Install lines (5.5).** A test finds every `pip install skyeai[...]` in `examples/`, `docs/` and `README.md`, and fails when an extra does not
  exist in `pyproject.toml` or is listed in `known_empty` of `budgets.toml` (it installs nothing).
- **Offline demo model (5.3).** Decided in D38. The examples keep their two modes: with a key they call the service; without one they use the
  demo model and print which one they use. Until 5.3 is done, 5.2 makes the missing-key and missing-server branches print guidance and a
  sample of the output, so no example ends in a traceback.

### Docstrings (tasks 6.1, 6.2)
`tests/unit/test_docstrings.py` runs `doctest` on the package docstring and on each Port module docstring, with `# doctest: +SKIP` on lines that
need a network or a key. A Port docstring example is a real, offline call.

### Extension page (task 6.3)
`docs/` gets one page, in the `base` section, with a table whose rows are the "Extension points" table of `11-design.md` extended to every
exported Port: kind, Port, registry or place to register, example file, and status (implemented or not yet). A docs test fails when a name in
`skye.interfaces.__all__` is missing from the page.

## Follow-up reports (familiarity, simplicity, tools)
Three reports of 2026-11-04 looked at the same surface from three angles: how close it is to what a user knows (familiarity), how much a user
must write and decide (simplicity), and the low-level tool-call path and what an agent needs from it (tools). They proposed different fixes to
the same problem in eight places; `.agents/tasks/uxui-reconciliation.md` gives the single answer used in each case. The decisions they settled
are rules now in steering; the questions they left open (O24 to O33) are taken as D36 to D48 (O24 to O33 as D36 to D45; D46 to D48 added after the review). The work they add, beyond the 35 findings:

### The execution primitive (tools report L2, A1; steering 16.10)
One function in `base`, next to the capability Port, runs a single call: it never raises and returns a `CapabilityMessage` whose outcome says ok,
error, denied or skipped (`CapabilityStatus`, D42). `CompletionResponse.execute_capability_calls`, the executable call, the registry and `CapabilityCallHandler`
delegate to it, so the four execution paths and three result types of today collapse to one behaviour; `registry.execute` stays the one path that
raises, documented as "I called it myself". Living in `base` lets `agents`, `teams` and `flows` use it without importing `tools` (the layer
table). A change to it (a timeout, the outcome field) reaches the agent, the manual loop and the single call at once — the reason it is built
first (task 3.11).

### The `ToolProvider` Port (tools report A5, A6; steering 16.11)
A Port in `base/interfaces` with three methods — list the schemas for an operation, run one call with a context, optionally close. The capability
registry implements it and the gateway client implements it, so an agent takes its toolset one way (Requirement 42.1). The context carries the
scope token and the operation description (42.3) and is a separate argument, never folded into the model's `**arguments` where a key could clash
(task 3.12). Capability registration is decided (D44); who writes the operation description stays with the existing O12.

### The router shorthand (simplicity report S1; steering 22.8)
`ModelRouter({"alias": ["provider/model", ...]})` builds the same `RouteConfig`, `ModelTarget` and `FallbackConfig` as the full form (first entry
primary, the rest fallbacks); the provider is read from the `"provider/model"` string and the API key from the provider's standard variable.
One syntax only: the `from_list` form the familiarity report first proposed is dropped (reconciliation 2). `skye.Router` is not added (D39).
The full form (strategy, retry policies, explicit `FallbackConfig`, YAML) stays first-class and documented;
an explicit value always wins over a default (task 4.7).

### Typed `provider()` (simplicity report S2; steering 22.9)
`@overload` so the default returns the model client and `provider_type="embedding"` the embedding client, and the quickstart type-checks with no
cast. A combined client type that exposes both `complete` and `encode` is a larger option the simplicity report raises; it is **not** decided
here (not added, D40) (task 4.8).

### Guessability aliases (familiarity report C1 to C5; steering 22.7, decision D39)
Thin aliases that store no second value: `CompleteResponse.text` → `content`, `CapabilityRegistry.list()` → `list_all`, `Runnable.ainvoke` beside
`invoke`. These three are added. `tool_choice`/`tools`, `kind=`, `skye.Router`, `skye.tool` and `Validated.model_dump`/`model_validate`/
`model_json_schema` are not added: the documentation names the word that exists (one vocabulary, Requirement 22.1; one name per thing, 22.4).
`content` is the text of the reply; a non-text output will get its own field when it exists, and `text` stays the text part.
`skye.completion(...)` as a callable module is rejected: a facade may only re-export (Requirement 7.15). A test records each name as `exists`
or `known_missing`, the list only shrinking (task 4.9, steering property 20).

## The `.skye` language (not built yet)
**Status: the parser is not written, and none of the examples below has been run through a parser.** The syntax was drafted with the owner in
two interviews (decisions D49 to D61) and the reference examples were written by hand. This spec owns the public surface of the language (the
syntax a user types, the load calls, the error messages); the parser and the grammar belong to `base`, the flow engine to `3-runtime-flows`,
the router mapping to the router spec and the bundled prompts to `prompts:4`. System view: `11-design.md`, section "The `.skye`
language"; requirements: Requirement 54 of steering.

### Syntax in one page
```
file        = block*
block       = KIND [LABEL] "{" (attribute | block)* "}"          KIND: router | flow | prompt (and, inside a flow: step, parallel, choice, context)
attribute   = NAME "=" value                                      one per line, or comma-separated on one line
value       = string | number | bool | list | map | reference | expression | duration
string      = "text" | """multi-line text"""
duration    = "30s" | "5m" | "24h"                                a string with a unit; a bare number is a load error (D58)
reference   = registry.NAME | flow.NAME | router.NAME | prompt.NAME | step.NAME.output | context.FIELD | env.NAME | item     (D57)
expression  = comparison, and / or / not, + - * /, in, names from the context, and len min max abs round str int float     (D55; checked with ast)
comment     = # to end of line
```
- A step moves on with attributes: `next = "X"`, `on_error = "Y"`, `on_timeout = "Z"`; `next = end` finishes (D54). A step with no `next` is a load
  error. Without `on_error` the step goes to the default error end; without `on_timeout` a timeout is an error.
- `choice` holds `when <expr> { ... }` branches and a mandatory `else` (D55). `parallel` has `join` (`all`|`any`) and `on_branch_error` (`cancel`|`continue`) (D56).
- `foreach = <list>` runs a step or a sub-flow for each element and `item` is the current one; a step that can be re-entered has `max_visits = N` (D56).
- `set field = expr` and `emit "event"` live inside the step and run when it finishes with success; a step with no `run` is allowed when it has `set`,
  `emit` or `foreach` (D58). `retry` is a map, `retry = { max = 3, after = "2s", backoff = true }`, and `retry = 3` is the short form (D54).
- The `router` block uses the field names of today's YAML and `ModelTarget`, except that a name ending in `_seconds` drops the suffix because its value
  is a duration (`cooldown`, `retry_after`); `fallback = [...]` is written inside the route; `route "x" = ["provider/model", ...]` is the shorthand (D59).
- The `prompt` block of version 1 has `variables`, `message "<role>"` (`system`, `user`, `assistant`), `placeholder`, `text`, `when`, `each` and `{{ }}`;
  inside it the variables are written bare, the one exception to the prefixes of D57 (D60).

### Load-time errors the checker must report
Each row is a short file and the message `skye check` prints; together they are the conformance cases of the parser and the examples a model learns from.
| Mistake | Message (file:line:column omitted) |
|---|---|
| `next = "B"` with no step `B` | unknown step "B" in "next". Defined steps: A, Fan, Write. Did you mean "Write"? |
| A step with no `next` | step "Fetch" has no next. Add: next = "<step>" or next = end |
| A `choice` with no `else` | choice "Decide" has no else. Add: else { next = "<step>" } |
| A loop with no bound | step "Write" can be entered again (Decide -> Write) but has no max_visits. Add: max_visits = 4 |
| `run = registry.plannr` not in the registry | step "Plan": "plannr" is not in the registry. Known: planner, web_search, ... |
| A reference with no prefix | "planner" has no prefix. Use registry.planner, flow.planner or router.planner |
| A context field not declared | "context.qualty" is not declared. Declared: topic, loops, quality |
| An unreachable step | step "Orphan" can not be reached from the start |
| `wait` or `on_event` in a version 1 file | "wait" needs persistence and is not available in this version |
| A wrong type in `set` | "quality" is number, the value is a string |
| A call outside the allowed list | call "open(...)" is not allowed in an expression. Allowed: len, min, max, abs, round, str, int, float |
| A typo in a field name | unknown field "timout" in step "Search". Did you mean "timeout"? |
| A bare number as a duration | timeout = 30 is not a duration. Use "30s", "5m" or "24h" |
| An invalid prompt role | role "bot" is not valid. Use system, user or assistant |
| An old router field | "cooldown_seconds" was renamed "cooldown" and takes a duration such as "60s" |
| A `fallback` naming a missing route | route "azure-gpt4" has no route "claud" in fallback. Did you mean "claude"? |
| An `env.NAME` with no value at run time | ConfigurationError: env.OPENAI_API_KEY is not set (router "main", route "gpt-4", target 1) |

### Scope and the reference set
Version 1 covers routers, flows (sequence, condition, parallel, bounded loop, retry, timeout, error branch, `foreach`, typed context with `set` and
`emit`, an agent, a team, a model through the router or a sub-flow as a step) and the reduced `prompt` block. Version 2 is written and not built:
waiting for events with persistence and resume, `to_mermaid()`, `include`, and in prompts the examples, multimodal content, output schema and the
partial; the delivery guarantee of persistence is open decision O34 and the fate of `prompts/engine.py` O35. The full reference set (four routers, seven
prompts, nine flows) was drafted in `.agents/tasks/uxui-dsl-examples.md`, a working file that is not versioned; task 8.1 turns it into fixtures under
`tests/fixtures/skye/` so the conformance suite lives in the repository.

### Loading
```python
import skye
from skye.flows import Flow
from skye.router import ModelRouter

spec   = skye.load("app.skye")                                   # parses and validates; returns the blocks by kind and name
router = ModelRouter.from_file("app.skye", name="main")
flow   = Flow.from_file("app.skye", name="research", registry={"planner": planner, "web_search": web_search})
result = flow.run({"topic": "mermaid state machines"})
```
**Naming to settle with the owner before task 8.4.** D61 writes `Router.from_file`, D52 writes `skye.Flow`, and the reference examples write
`skye.Router.from_file`. The router class that exists is `ModelRouter`, and D39 records `skye.Router` as `known_missing` (not added). The block above
uses the component paths, which need no new top-level name; whether `Router` and `Flow` become top-level names is a question for the owner, not
decided here.

## Decisions taken and the tasks they unblock
The owner took O24 to O33 as D36 to D45 (`.kiro/steering/12-decisions.md`). None blocks a task any more.
| Decision | Taken | Task |
|---|---|---|
| D36 (O24) | the model Port takes `messages`, `model` and options or one request; `CompleteRequest`/`CompleteResponse`; module stays `skye.completion` | 3.5 |
| D37 (O25) | `Protocol` for Ports implemented as plain classes, abstract base for Ports with default behaviour | 3.10 |
| D38 (O26) | a scripted model only in `examples/`; the real provider when a key exists | 5.3, 5.10 |
| D39 (O27) | aliases `text`, `list()`, `ainvoke`; no others | 4.3, 4.9 |
| D40 (O28) | drop the router storage re-exports, `MCPClientInterface`, `ImportError` in placeholder packages, no combined client type | 4.2, 4.5, 4.6 |
| D41 (O29) | per-Port reconciliation, `StorageAdapterInterface` removed, `ModelInterface` does not extend `Runnable`, large Ports split by role | 3.6, 3.9 |
| D42 (O30) | `CapabilityStatus` enum on `CapabilityMessage` | 3.11 |
| D43 (O31) | `execute_capability_calls` sync plus `aexecute_capability_calls` | 3.11 |
| D44 (O32) | no implicit global registry | 3.12 |
| D45 (O33) | one `CapabilityCall` type with `execute()` | 3.11 |
| D46 | non-text output as typed content blocks (Converse-like, Python types) | not built; first non-text adapter |
| D47 | gateway client not written here; contract noted in the gateway spec | none |
| D48 | `CapabilityCallHandler`, `Runnable.ainvoke`, `get_instance()` stay as known debt | none |
| D50 | one declarative language, `.skye`, for routers, flows and prompts; parser in `base` taking text | 8.1 to 8.4 |
| D59 | the `router` block is the reference format; fields 1:1 with today's YAML; `fallback` inside the route; the shorthand is additive | 8.4, 8.6 |
| D61 | the written grammar, the JSON Schema, `skye check`, `.gitattributes`, and the loading API `Flow.from_file`, `Router.from_file`, `skye.load` | 8.2 to 8.5 |
| D62 | the library reads no YAML: no parser, no `yaml` extra, no PyYAML; a `.yaml` file is rejected with a message naming `.skye` and JSON | 9.1 to 9.5 |
Related and not blocking: D49 (taken: the core has no third-party dependency) closes O4, so the pydantic copy of `CapabilitySchema` leaves with the code
migration, which is a separate task, and the budget tests fail by design until it is done; O20 (examples first) is the practice this spec follows for the
extension points.

## Correctness Properties

### Property 1: Public paths are short
For any `from skye... import` or `import skye...` in `examples/`, `docs/` or `README.md`, the module path has at most two levels and no
`base` or inner-module segment.
**Validates: Requirement 1 (Requirement 7.14 of steering)**

### Property 2: Facades only re-export
For any facade module, the set of names it defines equals the set it re-exports from its source module, and it contains no function or class.
**Validates: Requirement 1 (Requirement 7.15 of steering)**

### Property 3: A public class name is defined once
For any two modules of `src/skye`, no public class name is defined in both, except the entries of `KNOWN_DUPLICATES`, which only shrinks.
**Validates: Requirement 2 (Requirement 22.4 of steering)**

### Property 4: A built-in implementation conforms to its Port by signature
For any built-in implementation and the Port it declares, every Port method exists with the same parameter names and kinds and the same `def`
or `async def` form, except the entries of `KNOWN_MISMATCHES`, which only shrinks.
**Validates: Requirement 5 (Requirements 16.6 and 16.7 of steering)**

### Property 5: Every Port states its contract
For any exported Port, its docstring has the labels `Raises:`, `Missing:` and `Concurrency:`.
**Validates: Requirement 6 (Requirement 16.8 of steering)**

### Property 6: Every exported Port is implemented and tested
For any name in `skye.interfaces.__all__`, a built-in implementation or a reference implementation in the tests passes Property 4.
**Validates: Requirement 7 (Requirement 16.9 of steering)**

### Property 7: Examples run with no key
For any example, running it with no provider variable and no network exits with code 0 and prints no traceback.
**Validates: Requirement 8 (Requirement 24.4 of steering)**

### Property 8: Examples are small and plain
For any example not in `KNOWN_LONG`, the file is not empty and has at most the line limit; for any example not in the plain-output allowlist,
it prints no banner row and no emoji.
**Validates: Requirement 9 (Requirements 24.5 and 24.7 of steering)**

### Property 9: Install lines name real extras
For any `pip install skyeai[extra]` in `examples/`, `docs/` or `README.md`, the extra exists and is not in `known_empty`.
**Validates: Requirement 10 (Requirement 24.6 of steering)**

### Property 10: A README matches its folder
For any example folder, its README lists exactly the `*.py` files of the folder, and `examples/README.md` numbers a reading order.
**Validates: Requirement 11 (Requirement 24.8 of steering)**

### Property 11: The first docstring runs
For the package docstring and each Port docstring, every example that is not marked as needing a network runs and gives the printed result.
**Validates: Requirement 12 (Requirement 15.9 of steering)**

### Property 12: The extension page is complete
For any name in `skye.interfaces.__all__`, the extension page has a row for it.
**Validates: Requirement 13 (Requirement 15.10 of steering)**

### Property 13: One execution behaviour
For the same capability call, `response.execute_capability_calls()`, the executable call's `execute()` and the primitive all return an equal
`CapabilityMessage`, and a tool whose own result is the text `"Error: ..."` has the outcome `ok`, not a failure.
**Validates: Requirement 15 (Requirements 16.10 and 16.12 of steering)**

### Property 14: The router shorthand builds the full form
For a shorthand `ModelRouter({"alias": [...]})`, the router it builds equals the one the explicit `RouteConfig`/`ModelTarget`/`FallbackConfig`
form builds for the same aliases, and an explicitly set field is never overwritten by a default.
**Validates: Requirement 17 (Requirement 22.8 of steering)**

### Property 15: A guessable alias adds no behaviour
For each guessable-name alias, it returns the value of the name it delegates to and stores no second value; the test's known-missing list only
shrinks.
**Validates: Requirement 18 (Requirements 22.7 and 22.9 of steering)**

### Property 16: The load API is the same for every kind
For any `.skye` file, `Flow.from_file`, `Router.from_file` and `skye.load` accept the same `path` and report an error with the file, the line and
the column; for a file that holds one block of the requested kind, `name` may be left out.
**Validates: Requirement 19 (Requirements 54.3 and 54.9 of steering)**

### Property 17: A `.skye` example in the documentation passes `skye check`
For any `.skye` block shown in `docs/`, `examples/` or `README.md`, `skye check` reports no error.
**Validates: Requirement 19 (Requirements 54.1 and 54.8 of steering)**

## Superseded (history)
- The folder was `.kiro/specs/uxui/` with, at first, two files — `report.md` (the audit, three parts) and `rules.md` (27 rules and their status) —
  and later four more: `familiarity-report.md`, `simplicity-report.md`, `tools-report.md` and `reconciliation.md`. All were exempted from the spec
  tests by name. They are now under `.agents/tasks/` as `uxui-audit-report.md`, `uxui-audit-rules.md`, `uxui-familiarity-report.md`,
  `uxui-simplicity-report.md`, `uxui-tools-report.md` and `uxui-reconciliation.md`, and their content is in steering (requirements, decisions D36
  to D45), in the tables above and in `tasks.md`.
- Three more working files were in the folder for the `.skye` language: `dsl-decisions.md` (the decisions, with working numbers), `dsl-examples.md` (the
  reference examples) and `kiro-handoff-dsl.md` (the instruction to bring the specs in line). They are now `.agents/tasks/uxui-dsl-decisions.md`,
  `uxui-dsl-examples.md` and `uxui-kiro-handoff-dsl.md`. The decisions are D49 to D61 and O34, O35 in steering (the working numbers D54 to D76 map to the
  official ones in the first lines of `uxui-dsl-decisions.md`); the syntax, the error table and the scope are in "The `.skye` language" above.
- Rules 1 to 4, 7 and 8 were applied before this spec (facades, decision D34, Requirement 7.14, `tests/budget/test_public_imports.py`); they are
  tasks 1.1 to 1.3, ticked.

## Task Dependency Graph
```json
{
  "waves": [
    { "id": 0, "tasks": ["1.4", "2.1", "3.1", "3.3", "3.4", "5.1", "5.2", "6.1"] },
    { "id": 1, "tasks": ["2.2", "2.3", "3.2", "3.7", "4.1", "4.7", "4.8", "5.5", "5.6", "5.7", "5.9", "6.2", "6.4"] },
    { "id": 2, "tasks": ["3.8", "4.4", "5.4", "5.8", "6.3"] },
    { "id": 3, "tasks": ["3.5", "3.6", "3.9", "3.10", "3.11", "3.12", "4.2", "4.3", "4.5", "4.6", "4.9", "5.3", "5.10"] },
    { "id": 4, "tasks": ["7.1"] },
    { "id": 5, "tasks": ["8.2", "8.3", "8.5"] },
    { "id": 6, "tasks": ["8.1", "8.4"] },
    { "id": 7, "tasks": ["8.6"] }
  ]
}
```
Wave 3 follows the decisions D36 to D45; wave 2 follows the tests of wave 1 because it removes entries from their allowlists. Waves 5 to 7 are the
`.skye` language: the grammar, the checker and `.gitattributes` first, the conformance suite and the loading API once the parser exists, the
conversion of the router examples and YAML tests last.
