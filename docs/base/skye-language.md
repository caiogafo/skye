---
title: "The .skye language"
codename: "stratus"
status: current
last_updated: 2026-11-07
---

# The .skye language

One small, readable language for routers, flows and prompts, in files with the extension `.skye` (decisions D50 to D61, Requirement 54).
The parser is in `skye.base.dsl`, written in the standard library; it takes text, not a path, and never uses `eval`. A file may hold several
blocks, in any order; each file is self-sufficient in version 1 (no `include`).

Check a file with `skye check app.skye`; start a new one with `skye new flow my_flow` (see [Tools](#tools)).

## Grammar

```text
file        = { block } ;
block       = KIND [ LABEL ] "{" { attribute | statement | block } "}"
            | KIND LABEL "=" value                       (* shorthand: route "fast" = [ ... ] *)
            | KIND LABEL ;                               (* no body: placeholder "history" *)
attribute   = NAME "=" value ;
statement   = "set" NAME "=" value                       (* inside a step or a branch *)
            | "emit" STRING ;
when        = "when" expression "{" body "}" ;           (* choice branch, prompt condition *)
else        = "else" "{" body "}" ;
each        = "each" NAME "in" expression "{" body "}" ; (* prompt loop *)
LABEL       = STRING | name ;                            (* message turn.role { ... } *)
value       = string | number | bool | list | map | typecall | reference | expression ;
string      = '"' text '"' | '"""' multi-line text '"""' ;
number      = digits [ "." digits ] [ ("e" | "E") [ "+" | "-" ] digits ] ;
bool        = "true" | "false" ;
list        = "[" [ value { "," value } [ "," ] ] "]" ;
map         = "{" [ NAME "=" value { "," NAME "=" value } [ "," ] ] "}" ;
typecall    = TYPE [ "(" [ value ] ")" ] ;               (* string("x"), number(0), list *)
TYPE        = "string" | "number" | "bool" | "list" | "map" ;
duration    = STRING matching digits ("s" | "m" | "h" | "d") ;   (* "30s", "5m", "24h" *)
reference   = name ;
name        = IDENT { "." IDENT } ;
comment     = "#" { any character but newline } ;
```

Items of a body are separated by a new line or by a comma. Inside `[ ]`, `{ }` of a value and `( )` a new line is just a space. A string
escapes `\n`, `\t`, `\r`, `\"` and `\\`; the text of a `"""` string loses its first new line and its common indentation.
Lines and columns count from 1 in every message.

## Block kinds

| Kind | Where | What it holds |
|---|---|---|
| `router ["name"]` | top level | global fields, `route`, `retry_policy`, `allowed_fails_policy` |
| `flow "name"` | top level | `context`, `step`, `parallel`, `choice` |
| `prompt "name"` | top level | `variables`, `allow_missing`, `message`, `placeholder`, `each`, `when` |

Version 1 reads these three. A file that holds anything else is rejected with `unknown block`.

### router

Field names are those of today's router configuration. A field that ended in `_seconds` drops the suffix and takes a duration string:
`cooldown_seconds` is now `cooldown = "60s"`, `retry_after_seconds` is `retry_after = "5s"`.

```skye
router "main" {
  strategy               = "rate_limit_aware"
  cooldown               = "60s"
  enable_pre_call_checks = true

  route "gpt-4" {
    strategy          = "round_robin"
    fallback_on_error = true
    fallback          = ["claude"]          # if this route fails, try these routes in order
    target {
      model    = "gpt-4"
      provider = "openai"
      api_key  = env.OPENAI_API_KEY         # becomes the text ${OPENAI_API_KEY}
      tpm      = 100000
      rpm      = 1000
      timeout  = "30s"
      tags     = ["premium"]
      metadata = { region = "us-east-1" }
    }
  }
  route "claude" = ["anthropic/claude-haiku", "openai/gpt-4o-mini"]   # shorthand

  retry_policy "RateLimitError" { max_retries = 3, retry_after = "5s", exponential_backoff = true }
  allowed_fails_policy "RateLimitError" { allowed_fails_per_minute = 100 }
}
```

In the shorthand `route "x" = ["provider/model", ...]` the first entry is the primary target and the others are its fallbacks, in order; an
entry may be a map `{ model = "provider/model", api_key = env.X, rpm = 60 }`. Strategies: `simple_shuffle`, `round_robin`, `least_busy`,
`rate_limit_aware`, `latency_based`, `cost_based`, `weighted`, `priority_based`. Targets of one route are alternatives picked by the strategy;
`fallback` names other routes.

### flow

```skye
flow "triage" {
  context { ticket = string, priority = number(0) }

  step "Classify" {
    run   = registry.classifier
    input = { text = context.ticket }
    next  = "Route"
  }

  choice "Route" {
    when step.Classify.output.label == "bug" and context.priority >= 3 { next = "Escalate" }
    else                                                                { next = "General" }
  }

  step "Escalate" { run = registry.oncall_agent,  next = end }
  step "General"  { run = registry.support_agent, next = end }
}
```

- `context { name = type(default) }` declares the typed fields: `string`, `number`, `bool`, `list`, `map`. No default means required.
- `step "Name"`: `run` (a `registry.NAME`, `flow.NAME` or `router.NAME`), `input` (a map), `next`, `on_error`, `on_timeout`, `timeout`,
  `retry`, `max_visits`, `foreach`, and the statements `set field = expr` and `emit "event"`, which run when the step finishes with success.
  `next = end` finishes the flow. A step with no `next` is an error; with no `on_error` it goes to the default error end.
- `retry = { max = 3, after = "2s", backoff = true }`; `retry = 3` means `{ max = 3 }`.
- A step with no `run` is allowed when it has `set`, `emit` or `foreach`.
- `choice "Name"`: `when <expression> { ... }` branches checked in order, and a mandatory `else`.
- `parallel "Name"`: `step` branches, `join = "all" | "any"`, `on_branch_error = "cancel" | "continue"`, `next`, `on_error`. There is no timeout
  on the whole block; each step keeps its own.
- A step that can be entered again (a loop) needs `max_visits = N` on at least one step of the loop. A flow that contains itself is rejected.
- `foreach = context.items` runs the step once for each item; inside it `item` is the current element. It is the only loop over data.
- The first step, parallel or choice in the file is where the flow starts; any other one that cannot be reached is an error.

### prompt

```skye
prompt "summarize" {
  variables     = { text = string, max_words = number(100), style = string("neutral") }
  allow_missing = ["style"]

  message "system" { text = "You write short summaries." }
  placeholder "history"
  message "user" {
    text = "Summarize the text in at most {{ max_words }} words."
    when style { text = "Style: {{ style }}." }
    each line in text { text = "- {{ line }}" }
  }
}
```

Roles are `system`, `user` and `assistant` (or a loop value such as `message turn.role { ... }`). Inside a prompt the variables are written bare, as in a
template; `text` may appear several times in a message and the parts are joined in order. `{{ name }}` and `{{ name | filter }}` interpolate;
the names must be declared in `variables` (or be a loop variable). `{% %}` tags are not used: write a `when` or an `each`.

## References and prefixes

A reference always has a prefix (decision D66), except inside a prompt:

| Reference | Meaning |
|---|---|
| `registry.NAME` | a name resolved from the registry the caller passes (checked only when the caller gives the known names) |
| `flow.NAME`, `router.NAME`, `prompt.NAME` | a block of the same file |
| `step.NAME.output` | the result of an earlier step |
| `context.FIELD` | a declared context field |
| `env.NAME` | an environment variable (in a router block it becomes the text `${NAME}`) |
| `item` | the current element of a `foreach` |

`end` is the one bare word: `next = end`.

## Expressions

An expression is Python-compatible text. It is parsed with `ast.parse(mode="eval")`, checked against a whitelist and walked by a small
evaluator; it is never passed to `eval` or `exec`.

```text
expression = or_test [ "if" or_test "else" expression ] ;
or_test    = and_test { "or" and_test } ;
and_test   = not_test { "and" not_test } ;
not_test   = "not" not_test | comparison ;
comparison = arith { ("==" | "!=" | "<" | "<=" | ">" | ">=" | "in" | "not in" | "is" | "is not") arith } ;
arith      = term { ("+" | "-") term } ;
term       = factor { ("*" | "/" | "//" | "%") factor } ;
factor     = [ "-" | "+" ] atom { "." NAME | "[" expression "]" | "[" [expression] ":" [expression] "]" } ;
atom       = NUMBER | STRING | "True" | "False" | "None" | name | list | tuple | dict | call | "(" expression ")" ;
call       = FUNCTION "(" [ expression { "," expression } ] ")" ;
FUNCTION   = "len" | "min" | "max" | "abs" | "round" | "str" | "int" | "float" ;
```

Anything else is rejected: other calls (`open(...)`, `__import__(...)`, a method call), names or attributes that start with `_`, `**`, shifts,
lambdas, comprehensions, f-strings and the walrus operator. Repeating a string or list more than 10 000 times is a run error.

## Limits

A file may nest at most 100 levels in all: blocks, maps, lists, `type(default)` calls and the brackets of an expression each count one. Deeper
is one error, `file:line:column nesting is too deep (more than 100 levels)`, with the fix "Move the inner part into its own flow or prompt";
it is never a Python exception. The number is half of what the parser, the builder and the emitter survive at Python's default recursion
limit (about 490 levels), rounded down; the recursion limit is not raised.

## Errors

`skye check` prints every error it finds, one per line, as `file:line:column message`, ready to be pasted back to a model:

```text
app.skye:12:12 unknown step "Wirte" in "next". Defined steps: A, Fan, Write. Did you mean "Write"?
app.skye:9:3 step "Fetch" has no next. Add: next = "<step>" or next = end
app.skye:30:3 choice "Decide" has no else. Add: else { next = "<step>" }
app.skye:18:3 step "Write" can be entered again (Decide -> Write) but has no max_visits. Add: max_visits = 4
app.skye:7:12 step "Plan": "plannr" is not in the registry. Known: planner, web_search. Did you mean "planner"?
app.skye:7:12 "planner" has no prefix. Use registry.planner, flow.planner or router.planner
app.skye:22:9 "context.qualty" is not declared. Declared: topic, loops, quality. Did you mean "quality"?
app.skye:41:3 step "Orphan" can not be reached from the start
app.skye:26:5 "wait" needs persistence and is not available in this version
app.skye:19:9 "quality" is number, the value is a string
app.skye:31:12 call "open(...)" is not allowed in an expression. Allowed: len, min, max, abs, round, str, int, float
app.skye:5:5 unknown field "timout" in step "Search". Did you mean "timeout"?
app.skye:9:15 timeout = 30 is not a duration. Use "30s", "5m" or "24h"
app.skye:4:13 role "bot" is not valid. Use system, user or assistant
app.skye:14:5 "cooldown_seconds" was renamed "cooldown" and takes a duration such as "60s"
app.skye:11:15 route "gpt" has no route "claud" in fallback. Did you mean "claude"?
```

A syntax error (an unclosed block, an unterminated string, a value that is missing) is reported alone: the checks that follow need a tree that
parses. In Python, `skye.base.dsl.check_text(text, filename, registry_names)` returns the same errors as `Diagnostic` objects
(`file`, `line`, `column`, `reason`, `fix`), and `build(...).raise_for_errors()` raises them together as one `SkyeSyntaxError`.

## Version 1 and version 2

| | Version 1 (built) | Version 2 (reserved) |
|---|---|---|
| Blocks | `router`, `flow`, `prompt` | `include "other.skye"` |
| Flows | sequence, `choice`, `parallel`, bounded loops, `retry`, `timeout`, `on_error`, `foreach`, `set`, `emit` | `wait`, `on_event` (waiting for events with persistence and resume), `to_mermaid()` |
| Prompts | `variables`, `message`, `placeholder`, `text`, `when`, `each`, `allow_missing` | `examples`, multimodal `content`, `output` schema, `from`/`bind`, `parts`, type `image` |

A version 2 word in a version 1 file is rejected with "is not available in this version".

## Tools

```text
skye check app.skye                  # errors as file:line:col message; exit code 1 if there are errors
skye check --registry planner,web_search app.skye
skye check --schema                  # the JSON Schema of the router, flow and prompt blocks
skye new router main                 # a starting file on stdout (templates: shorthand, full)
skye new flow my_flow --template loop -o my_flow.skye   # sequence, branch, parallel, loop, full
skye new prompt my_prompt --template chat               # basic, chat
skye new --list
```

`skye new` refuses to overwrite a file unless you pass `--force`. The text it prints passes `skye check`; the lines to edit are marked
`# CHANGE ME`. `.gitattributes` maps `*.skye` to HCL so that GitHub highlights the files.

### The Claude skill

The package ships a skill for Claude Code that teaches a model the `skye` command, the `.skye` language and the rules of the library.

```text
skye skill install                    # copies it to ~/.claude/skills/skye/
skye skill install --scope project    # ... or to ./.claude/skills/skye/
skye skill install --dir DIR          # ... or to DIR/skye/
skye skill install --force            # replace files that differ (for example after upgrading the package)
skye skill print [NAME]               # print SKILL.md, or references/NAME.md; skye skill path shows where it is installed
skye skill status                     # up to date, outdated (the package changed) or edited by hand; exit 1 if not up to date
```

After you upgrade the package, `skye skill status` tells you whether the installed copy is behind; `skye skill install` brings it up to date
when nobody edited it (the installer keeps a record of what it wrote in `.skye-skill.json`), and keeps a file you edited unless you pass `--force`.

The skill has the official layout of a Claude skill: a minimal `SKILL.md` that says what to do first and which reference to read, and one
small file per topic in `references/` (`cli`, `language`, `router`, `flow`, `prompt`, `python-api`, `rules`), so a model loads only what the
task needs. The folder is `src/skye/utils/claude_skill/skye/`; its `evals/` folder (`evals.json`, `trigger_evals.json`) holds the test
prompts and is not installed. The files are updated in the same change as the command line, the grammar, the public API or the rules, and a
test fails when one names something that does not exist or shows an example that does not pass `skye check`.

## Writing `.skye` from objects

The opposite of `build` is `to_text`: it writes a router, flow or prompt model (or a whole document) back as `.skye` text that passes
`skye check` and builds an equal model again; defaults are left out and comments are not kept (so there is no `skye fmt`, which would delete
them). A router built in Python or by an older program can be moved to a file:

```python
router = ModelRouter({"fast": ["openai/gpt-4o-mini", "anthropic/claude-haiku"]})
Path("router.skye").write_text(router.to_skye("main"), encoding="utf-8")     # the router block
config = router.to_config()                                                    # or the dictionary that from_config_dict reads
```

**Secrets are not written.** A key written as `env.NAME` (or `${NAME}`) comes back as `env.NAME`; a key that was given in clear is left out and the
target reads its provider's standard variable (`OPENAI_API_KEY`, ...); pass `include_secrets=True` to write it, for example to a private file.
Only the retry and cooldown policies that differ from the defaults are written, and a route's strategy only when it differs from the router's.

## Loading from Python

```python
import skye
from skye.flows import Flow                      # also skye.Flow
from skye.router import ModelRouter

document = skye.load("app.skye")                  # the Document: routers, flows, prompts; ConfigurationError if the file has mistakes
router = ModelRouter.from_file("app.skye", name="main")
flow = Flow.from_file("app.skye", name="research", registry={"planner": planner})   # `registry.NAME` must be a key of the dictionary
flow.check()                                      # the mistakes now (empty when valid); flow.to_text() writes the block back
```

`skye.load(path, *, registry_names=None)` raises a `ConfigurationError` that lists every mistake as `file:line:column reason fix`. `name` is
optional when the file holds one block of the kind. `Flow.from_text(text, name=None, registry=None, filename=None)` reads a text.
**Running a flow is not built yet:** `flow.run(...)` raises `NotImplementedError` and points to the spec `3-runtime-flows`. There is no
`skye.Router` (decision D39): use `ModelRouter`.

## Loading is cached

Parsing and checking is the costly part of reading a `.skye` file, so it is done once per process. `skye.base.dsl.build_cached(text)` keeps the
built document in a bounded in-memory cache keyed by the SHA-256 of the text; `skye.utils.skye_files.load_document(path)` also skips the read
when the file's modification time and size did not change, and keeps the document when the time changed but the hash did not. The router
loader uses it. A cached document is **read-only**; `clear_cache()` and `clear_files_cache()` forget everything, and `use_cache=False` reads
and parses every time. Nothing depends on the cache for correctness: a new process parses once. Keeping the result on disk is not decided
(open decision O37).

See also: [Configuration](configuration.md) for how a router reads its file.
