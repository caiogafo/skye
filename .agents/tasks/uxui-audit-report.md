# UX audit of `examples/`

Date: 2026-11-03. Scope: every file under `examples/` (66 Python files, 7 READMEs, 2 YAML files), read and run the way a new user
would: from `examples/`, with no API keys and no network access, as well as by reading the code. Perspective: someone who ran
`pip install skyeai` and wants to be productive in ten minutes. This is a report with recommendations; nothing in `examples/` was
changed by it.

## Summary

The examples are strongest where they are small and self-contained (`auth/`, `base/`, `store/`, `memory/`, `models/decision_model.py`,
`advanced/custom_providers.py`): they run with no key, print something meaningful and teach one idea. They are weakest where a user
first looks: the first command a newcomer runs usually prints "OPENAI_API_KEY not set, skipping" and nothing else, the install
instructions are out of date, and several larger files bury the one idea under banners, repeated setup and 300 to 600 lines.

Ratings use three levels. **P1**: a user is blocked, misled, or sees a stack trace. **P2**: friction that costs minutes or trust.
**P3**: polish.

| # | Finding | Level |
|---|---|---|
| 1 | The first thing a newcomer runs ends in "skipping": no example shows a result offline | P1 |
| 2 | Install instructions are wrong or misleading after the extras changes (`skyeai[openai]` installs nothing) | P1 |
| 3 | Four examples end in a raw traceback instead of a clear message | P1 |
| 4 | `providers/router_example.py` is an empty file | P1 |
| 5 | `examples/prompts/` is stale: `sys.path` hacks, `MockPromptBuilder`, Jinja2 wording, 2,361 lines | P1 |
| 6 | READMEs name files and commands that do not exist | P2 |
| 7 | Three `function_calling` examples overlap, as do two YAML examples and two `message_roles` files | P2 |
| 8 | Large files repeat the same setup per function and hide the point | P2 |
| 9 | Provider examples with a placeholder key hit the real network and wait | P2 |
| 10 | No example shows the one thing the library sells: the same code on several providers, and the failure modes | P2 |
| 11 | Banner emoji and `print` walls make output hard to scan; style differs file to file | P3 |
| 12 | No learning path; the categories are by topic, not by what a user wants to do | P3 |

## What works well

- **Offline, runnable, short.** `auth/credential_sources.py`, `auth/custom_credential_source.py`, `base/errors.py`, `base/content_chunks.py`,
  `store/backends.py`, `memory/conversation_memory.py`, `models/decision_model.py`, `advanced/custom_providers.py`,
  `providers/bring_your_own_adapter.py` and `tools/registry.py` each run in a blink with no key and print a result. These are the
  model of what every example should be.
- **One client line.** `skye.provider("openai", api_key=...)` in `basic/quickstart.py` is easy to read and the comment under it
  shows the same call for Anthropic and Bedrock. This is the library's best first impression.
- **Honest degradation.** `models/token_counting.py` prints the missing-extra message with the exact `pip install skyeai[tokens]`
  command and then shows the stdlib fallback. `models/cohere.py` says what is and is not supported.
- **Drift protection.** `tests/examples` runs every example against a fake network, so the code in them keeps working. (It does not
  check that the prose around the code is true; see 2 and 6.)

## Findings

### 1. Nothing runs offline where a newcomer starts (P1)

`basic/quickstart.py`, `async_and_streaming.py`, `models/cost_tracking.py`, `advanced/function_calling.py`, `advanced/streaming.py`,
`advanced/structured_output.py` and `routing/fallbacks_and_health.py` all start with
`if not api_key: print("OPENAI_API_KEY not set, skipping"); return`. Run without a key, the user sees one line and learns nothing:
not the shape of the response, not what streaming looks like, not what a structured result is.

The library already has what is needed. `tests/examples/fake_network.py` answers every provider. A user-facing equivalent would let
each example have two modes: with a key it calls the real service; without one it runs against a built-in local stand-in and says so
("no key found: using the offline demo model; set OPENAI_API_KEY to call OpenAI"). `advanced/custom_providers.py` and
`providers/bring_your_own_adapter.py` already show the pattern with a tiny adapter that echoes text.

Recommendation: provide a public `skye.testing` (or `examples/_demo.py`) demo provider and make the "skipping" branch use it.
At minimum, print what the output would look like (a short sample) instead of nothing.

### 2. Install instructions are out of date (P1)

- `examples/README.md` lines 11 to 17 say `pip install skyeai[openai]` "with OpenAI support", `[openai,anthropic,bedrock]` for multiple
  providers, and lines 326 to 328 repeat it. Since decision D33 `openai` is an empty extra; the OpenAI adapter needs no extra, and
  exact token counts are `skyeai[tokens]`. `anthropic`, `bedrock`, `google` and `cohere` are empty too. A user following the README
  installs nothing extra and may conclude something is missing.
- `providers/openai_example.py` line 206 troubleshoots with "Installed skyeai[openai]". `providers/google_example.py` and
  `capabilities/mcp_server.py` carry the same kind of instruction.
- `capabilities/README.md` suggests `pip install fastmcp>=0.1.0`, a version range that does not match the `fastmcp>=2.0` of the extra.
- The tests run the code but nobody checks these strings.

Recommendation: one sentence at the top of `examples/README.md`: "`pip install skyeai` is enough for every provider; extras are only
for exact token counts (`tokens`), YAML (`yaml`), Redis (`memory`), PostgreSQL (`postgres`), MCP with fastmcp (`mcp`) and RS256 (`auth`)."
Add a test that every `pip install skyeai[...]` string in `examples/` and `docs/` names an existing extra that declares a library.

### 3. Raw tracebacks (P1)

Run with no server or credentials, four examples print a Python traceback, which tells a newcomer they did something wrong:

- `capabilities/mcp_client.py` and `tools/mcp_fastmcp.py`: `ProviderError: Transport error: Connection refused`, then a 20-line chain.
  They need an MCP server; they should check first and print "start a server (see `capabilities/mcp_server.py`) or set MCP_SERVER_URL".
  `tools/mcp_prompts_and_resources.py` already prints a graceful message and then runs on; the others should follow it.
- `serverless/serverless_router_example.py`: `ConfigurationError: Environment variable '${OPENAI_API_KEY}' not found`, a traceback through
  `base/config.py`. The error text is good, the example should catch it or set a placeholder as `routing/yaml_config_example.py` does.
- `routing/yaml_config_example.py` sets a placeholder key and then makes a real call, so the user sees an HTTP 401 with OpenAI's
  JSON body. Better: stop after showing the loaded router, or print "this call needs a real key".
- `providers/bedrock_example.py`, `providers/embeddings_example.py` and `serverless/lambda_handler.py` print several
  `ProviderError`/`ConfigurationError` lines (the same message twice, once raw and once wrapped as "Provider call failed: ...") and,
  without credentials, wait on the network ("timed out", "Host is down", "No route to host"). See 9.

### 4. An empty example (P1)

`examples/providers/router_example.py` is a zero-byte file. A user who opens it concludes the project is unfinished. Delete it or
move a real router example there. The routing content already lives in `examples/routing/`.

### 5. `examples/prompts/` is stale (P1)

Twelve files, 2,361 lines, eight of them with `sys.path` manipulation, the others with `MockPromptBuilder`, "Jinja2" wording and
"mock Pydantic" schemas. The prompt engine is the standard-library one (D20): no macros, inheritance or includes. A user copying
from these learns an API and a feature set that do not exist. `advanced/prompt_engineering.py` (84 lines) is the right size and
style and should replace most of the folder. This is already task 3 of `.kiro/specs/prompts-support/tasks.md`; this audit confirms
it is the largest single quality problem in `examples/` and suggests deleting rather than rewriting file by file:
`run_all_examples.py`, `simple_agent_test.py`, `working_agent_showcase.py` and `message_roles_complete.py` carry no idea the
others lack.

### 6. READMEs describe things that are not there (P2)

- `basic/README.md` tells the user to run `python examples/basic/streaming_example.py`; the file is `async_and_streaming.py`.
- `examples/README.md` says "Welcome to the Skye examples directory" and lists categories, but the folders `auth/`, `base/`, `memory/`,
  `models/`, `prompts/`, `store/` and `tools/` have no README, and several are not in the top README's categories.
- `serverless/README.md` has ten lines and no setup; the examples assume Lambda concepts without saying which parts run locally.
- Commands are written as `python examples/...`; the user's working directory matters (`routing/yaml_config_example.py` reads
  `router_config.yaml` from its own folder, which works) but the READMEs never say what to expect on screen.

Recommendation: each folder gets a five-line README (what you learn, command, what you will see, what you need). Generate the
file list from the folder in a test so a rename cannot leave the README behind.

### 7. Overlap and duplication (P2)

- `function_calling` exists three times: `advanced/function_calling.py` (70 lines, current style), `capabilities/function_calling_example.py`
  (403 lines) and `providers/function_calling_example.py` (428 lines). Their docstrings use different words for the same thing
  ("capability use" and "tool use"). The library calls it a capability; the user searching for "tools" finds `tools/` which is about
  registries and MCP. A glossary line in the README (capability = tool = function call) would remove the confusion.
- `routing/yaml_config.py` (586 lines) and `routing/yaml_config_example.py` (85 lines) teach the same thing at two scales; only the
  second is approachable. `routing/router_config.yaml` (422 lines) and `router_config_simple.yaml` likewise.
- `prompts/message_roles.py` and `message_roles_complete.py`; `prompts/template_showcase.py`, `simple_template_demo.py` and `basic_usage.py`.

Recommendation: keep the short one of each pair, link to the long one as "reference" or delete it.

### 8. Size and structure hide the point (P2)

Nine files exceed 300 lines (`routing/yaml_config.py` 586, `capabilities/function_calling_example.py` 403, `routing/basic_routing.py` 401,
`providers/structured_output_example.py` 402, `providers/multimodal_example.py` 386, `capabilities/remote_api.py` 353,
`prompts/multimodal_content.py` 355, `serverless/serverless_router_example.py` 333, `providers/embeddings_example.py` 336). Typical shape:
a banner, then six functions each repeating the key check, the client creation and `print("=" * 60)`. The idea (one line of
`response_schema=...`) is a few lines inside a 400-line file. Compare `advanced/structured_output.py` at 63 lines that shows nested
objects, an enum, an optional field and the validation error: it teaches more.

Recommendation: examples under about 80 lines, one idea each; move the exhaustive variants to docs where they can be searched.

### 9. Placeholder keys reach the real network (P2)

Examples that build a client with `"your-api-key"` or no credentials and then call `complete` contact `api.openai.com` or AWS. The user
waits for DNS or timeouts (observed `timed out`, `Host is down`) and sees provider errors that are accurate but look like a library
fault. A guard before the call (`if not creds: print how to set them; return`) is the pattern the basic examples use; the provider
examples should follow it consistently and use the demo provider from finding 1.

### 10. The value proposition is not demonstrated (P2)

The library's pitch is a single interface across providers, with a small core. No example shows the same few lines run against two
providers and compare, none shows the failure modes a production user fears (a 429, a timeout, a failed provider and the
fallback), and none shows what the offline token estimate costs in accuracy. `routing/fallbacks_and_health.py` is the closest and is
skipped without a key. A 40-line "one prompt, three providers, fallback when one fails" example, runnable against the demo
provider, would carry more weight than any of the 400-line files.

### 11. Output style (P3)

Large examples open with a row of 20 emoji and a title, then `print("=" * 60)` per section, mixed with `⚠️` warnings. Emoji differ per file
(cloud, wrench, brain, globe). In a terminal this is noise, in CI logs it is unsearchable, and it is not repeated in the small
current-style files. Pick one: plain section titles, no banners. Also `basic/configuration.py` shows
the column-aligned output style that reads best (label, value).

### 12. No learning path (P3)

Folders are by topic (`advanced`, `basic`, `capabilities`, `providers`, `routing`, ...); `advanced` holds both `custom_providers.py`
(an extension point) and `streaming.py` (a basic feature); `basic` has `simple_completion.py` with 315 lines. A newcomer cannot tell
what to read second. Suggested order, as a numbered list in `examples/README.md`:
1. `basic/quickstart.py` (one call)
2. `basic/async_and_streaming.py`
3. `advanced/structured_output.py`
4. `advanced/function_calling.py`
5. `routing/fallbacks_and_health.py`
6. `auth/credential_sources.py`
7. `advanced/custom_providers.py`

## Recommended order of work

1. Fix the P1 items that are one-line or deletions: empty `router_example.py` (4); the install strings and the README paragraph (2);
   the `streaming_example.py` reference (6); catch the four tracebacks (3). About an hour.
2. Add the offline demo provider and use it in the "skipping" branches (1, 9). It is the change that most improves the first ten minutes.
3. Replace `examples/prompts/` with the short style (5), already tracked by `prompts-support` task 3.
4. Merge or delete duplicates (7) and split or cut the large files (8).
5. Add tests that keep this true: install strings name real extras, README file lists match the folder, no example exceeds a line
   limit, every example exits 0 without a key (so "skipping" never ends in a traceback).
6. Add the "one prompt, three providers, fallback" example (10) and the reading order (12).

## Limits of this audit

- Read and run offline only. Behavior against live providers was not exercised; a user with real keys may meet other friction
  (rate limits, model names that have been retired, such as `gpt-4-vision` in `providers/multimodal_example.py`).
- Timings were not measured beyond noticing which examples wait on the network.
- No user was observed. These are the findings of a reviewer acting as a newcomer, so ordering by severity is a judgment.

---

# Part 2: names and imports

Scope: the public surface a user touches. Method: read the `__init__.py` of every package, list the `__all__` and public callables of
the main classes, compare the import lines used by the 66 examples and the docs, import each package in a fresh interpreter to
measure time and what it drags in. Same levels as Part 1 (P1 blocks or misleads, P2 costs time, P3 polish).

## Summary

The one-line entry (`skye.provider(...)`) and the message and error modules are good: short, predictable, light (`import skye` takes
about 27 ms and loads no pydantic). The trouble starts one step later. The user has to know the internal layer (`skye.base.*`) to
import the most common objects, three different classes share the name `CapabilitySchema`, the same word means three things
(capability, tool, function call), the first docstring a user reads shows an attribute that does not exist, and the sync and async
method families follow different patterns in different classes.

| # | Finding | Level |
|---|---|---|
| 13 | The package docstring (`skye/__init__.py`) shows `response.text`, which does not exist (the field is `content`) | P1 |
| 14 | The 4 commonest imports need the internal path `skye.base.*`; `from skye import UserMessage` fails | P1 |
| 15 | Three classes named `CapabilitySchema`, two named `CapabilityExecutionError`, in different modules | P1 |
| 16 | `Interface` suffix in code, "Port" in docs and steering, `Runnable`/`DecisionModel`/`StorageBackend` with neither | P2 |
| 17 | Capability, tool and function call are used interchangeably across names, docs and folders | P2 |
| 18 | Import paths are inconsistent in depth: `skye.models` exports some things, others need `skye.models.transport.multimodal` | P2 |
| 19 | The same names are exported from two packages (`skye.router` and `skye.store` backends) | P2 |
| 20 | Sync and async method families follow different naming patterns | P2 |
| 21 | Methods mix verbs and prefixes (`get_`, `list_`, `set_`, `register_`, `enable_`, `mark_`) without a rule | P3 |
| 22 | File and class names in `models/` do not follow one scheme (`openai_compatible.py` holds `OpenAIProvider`, `google_provider.py`) | P3 |
| 23 | Empty or half-built packages are importable and look public; docstring install lines are stale | P3 |
| 24 | Heavy imports are not predictable: `skye.router` and `skye.tools` load pydantic, `skye.models` does not | P3 |

## What works well

- **`skye.provider(name, **config)`** is a name a user guesses on the first try, and it matches the `boto3.client` habit the docs
  invoke. `skye.provider("openai", provider_type="embedding")` is the one place where the argument is less obvious (see 21).
- **Top level is small and lazy.** `skye.__all__` has six names; `import skye` loads neither a provider nor an optional library
  (checked: 27 ms, no pydantic). `messages`, `completion`, `exceptions` and `config` come as modules, so `skye.messages.UserMessage`
  works without a deep path.
- **Message and error names.** `UserMessage`, `SystemMessage`, `AssistantMessage`, `CapabilityMessage`, `SkyeError`, `ProviderError`,
  `ConfigurationError`, `ValidationError`, `MissingExtraError`: role- and cause-based, easy to remember, one umbrella `SkyeError`.
- **Provider classes.** `OpenAIProvider`, `AnthropicProvider`, `BedrockProvider`, `AzureOpenAIProvider`, `GoogleProvider` read the
  same way; embeddings follow with `*EmbeddingProvider`.
- **Verb consistency in the core call.** `complete`, `stream` and the `a`-prefixed `acomplete`, `astream` are the same on every
  provider and on the router (`ModelRouter.complete`, `acomplete`).

## Findings

### 13. The first docstring is wrong (P1)

`src/skye/__init__.py`, the example in the package docstring, ends with `print(response.text)`. `CompletionResponse` has `content`
and `get_output()`, no `text`. A user who copies it gets `AttributeError` at the first line of the first example they read (it is
what `help(skye)` shows). The same docstring says `pip install skyeai[bedrock]  # + Bedrock provider`; the extra is empty. Nobody
runs docstrings: the repo has no doctest gate for it.

Recommendation: fix both; consider adding `CompletionResponse.text` as a read-only alias of `content`, since `text` is what most
other libraries call it and the guess is natural. Run package docstrings through doctest (with `+SKIP` for network calls) in CI.

### 14. Common names need the internal layer (P1)

Counted over the examples: `from skye.base.messages import UserMessage` 24 times, `skye.base.completion` 6, `skye.base.interfaces.*` 25
across 11 distinct modules. `skye.base` is named like an internal layer ("base" in the architecture), but the user needs it on line 2
of every program. At the same time:

- `from skye import UserMessage` fails (only the modules are re-exported), so the user must learn two spellings:
  `skye.messages.UserMessage` or `from skye.base.messages import UserMessage`.
- `skye.base` itself exports nothing (`__all__` is absent, 6 public attributes that are submodules).
- `RoutingStrategy`, needed by every router user, lives in `skye.base.interfaces.router`, while `ModelRouter` is in `skye.router`.
  Four examples and six docs import it from the deep path.
- Port classes for extension (`MemoryInterface`, `AuthenticationInterface`, `ObserverInterface`) are reached through
  `skye.base.interfaces.<module>`, one module per port; `skye.base.interfaces.__all__` has 30 names, so
  `from skye.base.interfaces import MemoryInterface` works but no example uses it.

Recommendation: decide the one blessed spelling and use it everywhere. The least disruptive: re-export the ten names a beginner
needs from the top level, lazily (`__getattr__`, as `provider` already is lazy): `UserMessage`, `SystemMessage`, `AssistantMessage`,
`CompletionRequest`, `SkyeError`, `ProviderError`, `ValidationError`, `provider`, plus `skye.router.RoutingStrategy` re-exported from
the router package. Then the examples read `from skye import UserMessage`. Keep the deep paths working.

### 15. Same name, different class (P1)

- **`CapabilitySchema`** is defined three times: `skye.base.interfaces.capability` (a `Validated` dataclass),
  `skye.base.capability_schema` (a plain class, which also defines `CapabilityRegistryLike`) and `skye.tools.schema` (a pydantic
  model). `skye.tools.CapabilitySchema is skye.base.interfaces.CapabilitySchema` is `False`, and `from skye.tools import CapabilitySchema`
  (what the examples do) gives the pydantic one, the other the dataclass. A schema built with one is not the type another expects.
- **`CapabilityExecutionError`** is defined in `skye.base.exceptions` and again in `skye.tools.exceptions`. `except` on one does not
  catch the other; `tests/differential/test_mcp_differential.py` already imports the tools one for this reason.
- **`CapabilityCall`** is fine (one class, re-exported), but `skye.tools` also exposes `CapabilityCallHandler`,
  `CapabilityResult` (pydantic) next to `skye.base.completion.ExecutableCapabilityCall`: the pairs are hard to tell apart by name.

Recommendation: one definition per name, the others become re-exports; the pydantic migration of `tools` (D24, `0-base-structure`
group 14) is the natural moment to do it. Add a test: no class name is defined twice in `src/skye` among public names.

### 16. Three words for the contract (P2)

Code: `ModelInterface`, `MemoryInterface`, `AuthenticationInterface`, `ObserverInterface` (suffix `Interface`), but `Runnable`,
`DecisionModel`, `StorageBackend` (no suffix) and `MCPClientPort` (suffix `Port`). Docs, steering and decisions use "Port" everywhere
("one Port `AuthenticationInterface`"). A reader of the docs will search for `AuthenticationPort` and find nothing. Several of the
`Interface` classes are `Protocol`s, not abstract base classes, which the suffix hides.

Recommendation: pick one. Cheapest honest choice: keep `*Interface` in code (renaming is a breaking change for any extension
author) and state in the docs the sentence "a Port is a class named `*Interface`". Rename `MCPClientPort` to `MCPClientInterface`;
settle `Runnable`, `DecisionModel` and `StorageBackend` as the three documented exceptions (a verb-like protocol, a noun, and a
concrete family).

### 17. Capability, tool, function call (P2)

The library's word is **capability** (`CapabilityRegistry`, `@capability`, `CapabilityMessage`, `capabilities=` on the request),
the package is **tools** (`skye.tools`), the OpenAI-shaped data is `tool_calls`, examples call it "function calling" and "tool use",
and the MCP side is `MCPToolCapability`. The user searching the docs for how to give the model a function will try three words. The
request argument `capability_choice` has no counterpart anyone else uses (`tool_choice`).

Recommendation: one sentence in the README glossary (capability = tool = function), and a docstring line on `@capability` and on
`skye.tools` saying so. Naming the package `capabilities` would be cleaner but is a larger break; do it only if renaming is cheap
at this stage (the project is at 0.1.0).

### 18. Import depth is inconsistent (P2)

`skye.models` exports `ImageHandler`, `TokenCounter`, `CostCalculator`, `ProviderRegistry`, `JevDecisionModel`, but the examples import
`ImageHandler` from `skye.models.transport.multimodal` and `BaseModelProvider` from `skye.models.base`, and `create_mcp_client` from
both `skye.tools` and `skye.tools.mcp_client`. `skye.models.llm.openai_compatible` is a file name a user would never guess for
`OpenAIProvider`. Also `skye.models.transport` is an implementation word; for the user, `ImageHandler` and the retry or token
tools are "utilities of models", not "transport". The result: one name, two or three working spellings, and the docs pick
different ones.

Recommendation: the rule "import from the package, never from a module inside it" stated in the README and enforced by a test over
`examples/` and `docs/` (every `from skye.X.Y import` where `skye.X` already exports the name fails). It also frees the project to
move files later.

### 19. Same names from two packages (P2)

`skye.router.__all__` re-exports six storage backends (`InMemoryBackend`, `RedisBackend`, ...) which also live in `skye.store`
(`skye.router.StorageBackend is skye.store.StorageBackend` is `True`). Both paths work and the examples use both
(`serverless_router_example.py`, `store/backends.py`). A user cannot tell which is the real home.

Recommendation: `skye.store` is the home (the store is its own component); drop the re-export from `skye.router` at 0.1.0, or keep
it and document it as an alias.

### 20. Sync and async naming (P2)

- Providers and the router: `complete` / `acomplete`, `stream` / `astream` (prefix `a`). Consistent.
- Router metrics: `get_model_health` / `aget_model_health`, `get_usage_stats` / `aget_usage_stats`, `get_cooldown_models` /
  `aget_cooldown_models`: the `a` prefix goes before `get`, a reasonable rule.
- Embeddings: `encode` / `aencode`, `encode_batch` / `aencode_batch`; consistent.
- Registry: `execute` / `aexecute` on `CapabilityRegistry`; but `invoke` exists only on the sync side (`Runnable.invoke`), with no
  `ainvoke`.
- `provider.stream` yields chunks synchronously while the examples need `async for` on `astream`; the docs never state it.

Mostly consistent; the gap is `invoke` without `ainvoke` and the lack of one sentence describing the rule.

### 21. Verb vocabulary (P3)

`ModelRouter` has 24 public callables mixing `set_*` (7), `get_*` (4, plus 4 `aget_*`), `list_aliases`, `register_model`, `enable_pre_call_checks`,
`mark_model_failed`, `select_model`, `is_alias`, `from_yaml`, `from_config_dict`. `CapabilityRegistry` has `register` and
`unregister`, `exists` and `get`, `list_all`, `search` and `search_by_name`, `count`, `clear`, `reset_instance`.
`ProviderRegistry` has `get_model_provider` and `get_embedding_provider`, while the top-level function is `provider(...)` and takes
`provider_type="embedding"` for the same choice. A user guessing `router.list()` or `registry.list()` fails; `list_all` and
`list_aliases` are the spelling.

Recommendation: no renames now. Write the convention in `python-standards` steering (`get_x` reads one thing, `list_x` many,
`set_x` configures, `register` adds, verbs for actions) and apply it to new code. Two cheap aliases would help guessability:
`CapabilityRegistry.list()` for `list_all`, `skye.provider(name, kind="embedding")` as the friendlier spelling of `provider_type`.

### 22. File and class names in `models/` (P3)

`models/llm/openai_compatible.py` holds `OpenAIProvider` and `AzureOpenAIProvider` (the file names the family, the classes the
vendors); `google_provider.py` has the suffix while `anthropic.py` and `bedrock.py` do not; embeddings are `*_embeddings.py` with
`*EmbeddingProvider`. `skye.tools` has `mcp_client`, `mcp_server_client`, `mcp_fastmcp`, `mcp_capability`, `mcp_boundary`,
`mcp_resource`: six files for one concept with names that do not say which to read. Because users should import from the package
(18), these are less urgent, but contributors and stack traces show them.

### 23. Empty packages and stale install text (P3)

`import skye.gateway`, `skye.flows`, `skye.teams`, `skye.policy` succeed and expose nothing (no `__all__`); `skye.observe` and
`skye.guard` have `__all__ = []`. A user who lists `skye.*` in an IDE sees sixteen packages, six of which (`flows`, `gateway`, `guard`, `observe`, `policy`, `teams`) are empty placeholders for
components still on the roadmap. The package docstring still shows `pip install skyeai[agents,memory]` and `skyeai[bedrock]` as
if they add things.

Recommendation: raise a clear `ImportError("skye.gateway is planned, not available yet")` from the placeholders (a module-level
`__getattr__`) so an IDE completion or a typo gives a message rather than an `AttributeError`; fix the docstring.

### 24. Predictable import cost (P3)

Measured in fresh interpreters: `skye` 27 ms, `skye.models` 68 ms, `skye.prompts` 86 ms, `skye.router` 80 ms (loads pydantic),
`skye.tools` 156 ms (loads pydantic). The budgets are met, but the differences are not visible from the name. This resolves itself
when the pydantic removal (D24, `0-base-structure` 14.1) reaches `router` and `tools`; until then, say in `docs/budgets.md` which
packages load pydantic.

## Recommended order of work (names and imports)

1. P1, an hour: fix the docstring (13), add `CompletionResponse.text` if accepted, and add a docstring doctest gate.
2. P1: decide the blessed import spelling and re-export the beginner names at the top level, lazily (14).
3. P1, together with `0-base-structure` 14.1: make each public name one class (15), with a test that rejects duplicates.
4. P2, documentation only: one glossary for Port/Interface (16) and capability/tool (17); the "import from the package" rule with a
   test over `examples/` and `docs/` (18).
5. P2: decide whether `skye.router` keeps its storage re-exports (19); add `ainvoke` or document why not (20).
6. P3: conventions in steering (21), file naming for new modules (22), placeholders raise a clear error (23).

## Limits of this part

- The names were judged by reading and by trying imports; no user tried to guess them, so the guessability claims are the
  reviewer's judgment.
- Breaking renames were not costed; at version 0.1.0 with no published users they may be cheap, which is a decision for the owner.
- Method counts come from `inspect` on the classes as of 2026-11-03 and change with every release.

---

# Part 3: contract analysis

Scope: the Ports of `skye.base.interfaces` (30 exported names, 2,872 lines in 23 modules): what each promises, whether the code that
claims to implement it keeps the promise, and whether a user who writes an extension can rely on it. Method: classify every
exported name (`Protocol`, abstract base class, enum, dataclass), compare each Port with its implementation by signature and by
`async`-ness through `inspect`, search `src`, `tests` and `examples` for implementers and users, read the compliance checker
(`utils/validation.py`) and the contract sentences in `10-requirements.md` (Requirements 3, 4, 16). Same levels as Parts 1 and 2.

## Summary

The small Ports are sharp and well specified: `AuthenticationInterface`, `AuthorizerInterface`, `DecisionModel`, `Runnable` are
one-method `Protocol`s whose docstring says what goes in and out, and they are checkable at runtime. The large ones are the
problem. The main user-facing Port, `ModelInterface`, does not describe the call the user actually makes (the Port takes a
`request`; every implementation takes `messages, model, ...`), the router Port disagrees with the router on `async`, the streaming
signature is wrongly typed, six Ports have a ready implementation that does not declare it, and 13 of the 20 abstract Ports have no implementation
that inherits them (five of those have no test and no example). Two mechanisms (abstract base class, `Protocol`) guard conformance, only one of which the compliance checker can handle,
and it checks method names, not signatures.

| # | Finding | Level |
|---|---|---|
| 25 | `ModelInterface` does not match the call users make: Port `complete(request)`, implementation `complete(messages, model, ...)` | P1 |
| 26 | `ModelInterface.astream` is typed `async def ... -> Iterator`; the real one is an async generator | P1 |
| 27 | `ModelRouterInterface.select_model` is sync; `ModelRouter.select_model` is `async` | P1 |
| 28 | Two conformance mechanisms (20 abstract base classes, 4 `Protocol`s); the checker handles only the first | P2 |
| 29 | `validate_interface_compliance` checks names only: wrong parameters or `async`-ness pass | P2 |
| 30 | Six Ports have a working implementation that does not satisfy them (`isinstance` is false or methods are missing) | P2 |
| 31 | Thirteen abstract Ports have no inheriting implementation in `src`; five have no test and no example either | P2 |
| 32 | Error contracts are missing from most Ports: `Raises:` appears in 8 of 23 modules | P2 |
| 33 | Overlapping Ports: two storage Ports, two token and cost classes, a registry Port with no registry | P3 |
| 34 | Port size is uneven: from 1 method to 22 (`PromptBuilderInterface`) and 16 (`ModelRouterInterface`) | P3 |
| 35 | Docs call the contract a Port, the code an Interface, and examples show it only for four Ports | P3 |

## What works well

- **The one-method Ports.** `AuthenticationInterface.apply(method, url, headers, body) -> dict`, `AuthorizerInterface.authorize(principal,
  action, resource) -> Decision`, `DecisionModel.decide(prompt, options) -> DecisionResult`, `Runnable.invoke`. Each is a
  `runtime_checkable` `Protocol`: a user's class satisfies it without inheriting, `isinstance` verifies it, and the
  docstring states the invariants (the input headers are not modified; the decision is exactly permit or forbid; probabilities sum
  to one). `SigV4Authenticator` passes `isinstance(..., AuthenticationInterface)` (checked). These are the model of a good contract.
- **Closed outcomes are typed.** `Decision` and `EventType` are enums, `DecisionResult` and `SafetyResult` are dataclasses: a user
  cannot return a free string where the library expects one of two values.
- **No I/O, no component import in the Ports** (Requirement 3.4) is enforced by `tests/budget/test_import_matrix.py`; `base`
  imports only the standard library.
- **`StorageBackend`, `CapabilityInterface`, `ModelInterface`, `VectorEncoderInterface` have real implementers** (six, five, one family,
  one family) and tests; the extension story for them is credible. `custom_providers.py` and `bring_your_own_adapter.py` show it
  working.
- **Port docstrings carry examples** where they are long (`prompt.py` 24, `router.py` 10): a contract with a worked example is
  the easiest to implement.

## Findings

### 25. The model Port does not describe the call (P1)

`ModelInterface.complete(self, request: CompletionRequest) -> CompletionResponse`. `BaseModelProvider.complete(self, messages=None,
model=None, router=None, temperature=None, max_tokens=None, **kwargs)`, and that is the call every example makes
(`client.complete(messages=[...], model="gpt-4")`). Both `complete` and `stream` have the same split; `acomplete` too. Compared
through `inspect`, all four sync and async entry points differ from the Port by parameter list. The base class accepts a
`CompletionRequest` as its first argument, so both work at run time, but:

- A user who implements the Port exactly (`def complete(self, request)`) writes an adapter that cannot be called the way the docs
  teach (`client.complete(messages=...)`), so the example `custom_providers.py` has to inherit `BaseModelProvider`, not the Port.
- mypy reports the incompatibility (`Signature of "acomplete" incompatible with supertype ModelInterface`); it is hidden by
  `# type: ignore[misc,override]` on the base class, which says the type checker already knew.
- A caller typed against `ModelInterface` can pass only a request; a caller typed against the class can pass messages. The Port
  is thus not the contract callers use.

Recommendation: the Port must say what the callers do. Either make the Port `complete(messages_or_request, model=None, **options)` (the
real shape, one `Protocol`), or declare that the Port is the low-level form and give `skye.provider(...)` a return type that says
so. The first is the honest one. Add a test that compares signatures (see 29) so this cannot drift again.

### 26. `astream` is typed as an `Iterator` and awaited (P1)

The Port declares `async def astream(self, request) -> Iterator[StreamChunk]`. An `async def` that returns an `Iterator`
means "await it, then iterate synchronously"; the implementation is an async generator (it contains `yield`) and the examples use
`async for chunk in client.astream(request)`. The correct return type is `AsyncIterator[StreamChunk]` with a plain `def`
(or an `async def` generator). The docstring example in the Port repeats the wrong annotation, and the implementation carries the
`type: ignore[misc,override]` mentioned above. A user who writes an adapter from the Port's text writes a coroutine that returns a
list iterator and then fails with `async for requires __aiter__`.

### 27. The router Port and the router disagree on `async` (P1)

`ModelRouterInterface.select_model` is a normal function; `ModelRouter.select_model` is `async def`. A caller that follows the Port
gets a coroutine object where it expects a `str`, and no exception; it fails later when the object is used as a model name.
The Port's other 15 methods match; this one is the single signature mismatch found.

### 28. Two ways to be a Port (P2)

Of the 24 contract classes (the other exported names are enums and dataclasses), 20 are abstract base classes (`ABC` with
`@abstractmethod`) and 4 are `@runtime_checkable` `Protocol`s (`AuthenticationInterface`, `AuthorizerInterface`, `DecisionModel`,
`Runnable`). The two behave differently for a user:

| | ABC | Protocol |
|---|---|---|
| must inherit | yes | no |
| `isinstance` on a class that did not inherit | false | true (names only) |
| `validate_interface_compliance` | works | raises (it takes `type[ABC]` and tests `issubclass`) |
| `Runnable` requirement 7.1 ("adapters, agents, teams implement it") | n/a | works for any class with `invoke` |

The split follows no stated rule: the one-method Ports are protocols, the others are ABCs, so a small Port such as
`TokenCounterInterface` (two methods) is an ABC while `Runnable` (one method) is a Protocol. A user extending the library cannot predict whether inheriting is
required.

Recommendation: write the rule in `python-standards` steering. Suggested: Ports that third parties implement as plain classes
(authentication, authorizer, decision, runnable, observer, safety, memory) are `Protocol`s; Ports that carry default behavior
(`BaseModelProvider`'s retry, health) stay as abstract bases and are implemented by inheriting.

### 29. The compliance checker checks names only (P2)

`validate_interface_compliance(implementation, interface)` requires `issubclass`, then checks that each abstract method name exists
and is not abstract. It does not compare parameters, defaults, `async`-ness or return type. Requirement 16.2 says a Port is validated
at initialization; in practice a class that defines `complete(self)` (no `request`) or `async def select_model` where the Port says
sync passes. The three mismatches in 25 to 27 would all pass it, which is why they went unnoticed. It also rejects Protocols
(`type[ABC]`, `issubclass` of a non-ABC protocol raises `TypeError` for non-runtime-checkable members), so the four Protocol Ports
have no equivalent check (`isinstance` against them does work).

Recommendation: extend the checker to compare parameter names, kinds, `async`-ness and (optionally) annotations by name, and make it
accept Protocols. Use it in one test that checks every built-in implementation against its Port (the comparison done for this
audit took 30 lines). This is the cheapest way to make the Ports real.

### 30. Implementations that do not declare their Port (P2)

| Port | Implementation in `src` | Result |
|---|---|---|
| `TokenCounterInterface` | `models.TokenCounter` (classmethods) | same method names; `isinstance` is false |
| `CostCalculatorInterface` | `models.CostCalculator` | same method names; `isinstance` is false |
| `ConfigLoaderInterface` | `base.config.ConfigLoader` | misses `load_from_env`, `load_from_file` |
| `MultimodalHandlerInterface` | `models.ImageHandler` | misses all five methods; different design (static converters) |
| `ErrorHandlerInterface` | `models.transport.error_mapping` (static functions) | not a class implementing the Port |
| `RouteRegistryInterface` | none | router implements part of it inside `ModelRouter` |

The first two are one `register` or one base class away from being real. The other four show a Port written before the code and
never reconciled: the spec called for a design, the implementation took another. A user reading the Port to learn what the library
offers is told about capabilities (`get_image_dimensions`, `validate_image`, `load_from_env`) that do not exist.

Recommendation: for each row, decide: make the implementation satisfy the Port, change the Port to what exists, or delete the
Port until there is an implementation. Port names that nothing implements should not be in `__all__`.

### 31. Ports with no implementer, no test, no example (P2)

Searching `src`, `tests` and `examples` for each name: no class in `src` inherits `RouteRegistryInterface`, `MemoryInterface`,
`StorageAdapterInterface`, `SafetyFilterInterface`, `ObserverInterface`, `EventHandlerInterface`, `PluginInterface`,
`ContentReaderInterface`, `MultimodalHandlerInterface`, `CostCalculatorInterface`, `TokenCounterInterface`, `ErrorHandlerInterface` or
`ConfigLoaderInterface` (13 abstract Ports). The four Protocol Ports are satisfied structurally (the authenticators, `Runnable`
providers, Jev) and so do not show up in an inheritance search. Of these, `MultimodalHandlerInterface`,
`CostCalculatorInterface`, `TokenCounterInterface`, `ErrorHandlerInterface` and `ConfigLoaderInterface` are named by neither a test
nor an example, so nothing proves they can be implemented (the first group below belongs to components not yet built). Most of the first group belongs to components that are not built yet
(`policy`, `guard`, `observe`, `memory`), which is legitimate; the point is that their contracts are untested until then.

Recommendation: each Port gets one reference implementation in the tests (a few lines, in-memory), run through the compliance
test of 29, so the contract is exercised before a component is built on it. `tests/unit/test_port_compliance.py` does this for
some Ports; extend it to all.

### 32. Error contracts are not stated (P2)

`Raises:` appears in 8 of the 23 Port modules. Not stated: what `AuthenticationInterface.apply` raises when a credential is
missing (the implementations raise `LoginRequiredError` or `ConfigurationError`, the Port does not say), what a `DecisionModel`
does when the endpoint fails, what `StorageBackend.get` returns for a missing key (the examples show `None`), what
`MemoryInterface.retrieve` does on an empty store, whether `ObserverInterface` methods may raise (a failing exporter must not break a
model call), whether `EventHandlerInterface` hooks are awaited or fire and forget. The rule of Requirement 18 (errors derive from
`SkyeError`) is not repeated where an implementer needs it.

Recommendation: a standard footer in each Port docstring: "Raises", "Thread and async safety", "Idempotency". For hooks and
observers state explicitly that exceptions are swallowed and logged.

### 33. Overlap and orphans (P3)

- **Two storage Ports.** `StorageBackend` (six `async` key-value methods, used by `store` and the router) and
  `StorageAdapterInterface` (`save`, `query`, `vector_search`, `delete`, sync, no implementation). The second looks like the
  vector-store design of `memory`; the names do not say so.
- **`Runnable` and `ModelInterface`.** Requirement 7.1 says adapters implement `Runnable`; `BaseModelProvider.invoke` does, but
  `ModelInterface` does not extend `Runnable`, so a function typed `Runnable` accepts models only by structure.
- **`CapabilitySchema` in three places** (already in Part 2, #15) lives partly in the Ports: `interfaces/capability.py` and
  `base/capability_schema.py`.
- **`ProviderRegistryInterface`** is implemented by the class `ProviderRegistry`, yet users create clients through the function
  `skye.provider`, which the Port does not describe.

### 34. Uneven size (P3)

Methods per Port: 1 (four Ports), 2 to 5 (fifteen), 8 (`EventHandlerInterface`), 16 (`ModelRouterInterface`), 22
(`PromptBuilderInterface`, 611 lines). A 22-method abstract class is not a contract an outsider will implement; it is a base class
disguised as one. `ModelRouterInterface` mixes selection, health, usage, cooldowns, rate limits and registration (the router's whole
surface), so any implementation must provide all of it.

Recommendation: split the large ones by role (selection, health reporting, configuration) as `Protocol`s a caller needs only in part,
following "interface segregation": a function that only selects takes `Selector`, not the whole router.

### 35. Naming and discoverability (P3)

Ports are named `Interface` in code and "Port" in docs (Part 2, #16). Beyond that, a user wanting to extend the library must read
`base/interfaces/` (23 files) or the architecture document to learn which Ports exist; the examples show custom classes for only a few
(`AuthenticationInterface`, `MemoryInterface`, `ObserverInterface`, `AuthorizerInterface`, `SafetyFilterInterface`, `EventHandlerInterface`,
`StorageBackend`, `Runnable`, `DecisionModel`); fourteen Ports never appear in an example. No index says "to add X, implement this Port, register here" except the requirement table (Requirement 11.1:
one Port, one registry, one owner per integration kind).

Recommendation: a one-page table in the docs: kind of extension, Port, registry, example file, status (implemented or not yet).

## Recommended order of work (contracts)

1. P1, small, mechanical: fix `astream` typing (26); align `select_model` (27); make the model Port match the real call (25).
2. P2, one test: compare every implementation with its Port by parameters and `async`-ness and accept Protocols (28, 29). It
   should have failed on the three P1 items; run it first to confirm, then fix them.
3. P2, decisions: for the six unreconciled Ports (30), choose per row to fix the implementation, fix the Port, or remove the Port;
   remove un-implemented Ports from `__all__` until a component needs them (31).
4. P2, documentation: error and concurrency footer in every Port (32); the extension table (35).
5. P3: split the 16- and 22-method Ports (34); resolve the two storage Ports and relate `Runnable` and `ModelInterface` (33).

## Limits of this part

- Signatures were compared by parameter names and `async`-ness only; return annotations were not compared (several
  implementations lack them). A deeper check may find more.
- "No implementation" means none found in `src` by class inheritance or by search of the Port name; a structural implementation of a
  `Protocol` that never names it would not be found (the five protocols were checked by hand where an implementation is known).
- The counts (30 exported names, 24 contract classes, 13 abstract Ports without an inheriting implementation) come from the code on 2026-11-03; the contracts of
  components still to be built (`policy`, `guard`, `observe`, `memory`) are judged on their text only.
- Findings 25 to 27 are confirmed by running `inspect` and by the existing `type: ignore`; no user-facing failure was reproduced end to end.
