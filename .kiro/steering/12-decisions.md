---
inclusion: manual
---

# Decisions

The choices the owner has made (the log) and those not yet taken (open). Requirements cite them as "D13" or "open decision O7".
A decision is never rewritten: a later one supersedes it and the old one is marked "superseded by Dn". When an open decision is
taken, it moves to the log as the next D-number, the requirement it affects is edited in `10-requirements.md`, and its entry leaves
the open list.

## Decision log
Newest last. A decision is never rewritten: a later one supersedes it and the old one is marked. Dates: the day the decision was
recorded in the repository; "n/d" where I could not recover it (check git).

| ID | Decision | Why | Supports | Touches |
|----|----------|-----|----------|---------|
| D1 | Serverless first: Lambda zip, no container, no multiprocessing, no background threads, external state | target deployment | R7, R11 | all |
| D2 | Standard library first, then libraries in the serverless runtime, then pure Python; no compiled code in the core | package size, load time | R7, R9 | all |
| D3 | Size and load budgets in `budgets.toml`, enforced by tests and CI, only going down | keep the footprint honest | R7 | all |
| D4 | One short plain name per component, shared by folder, spec, docs, budget; themed names rejected as obscure | readability | R1 | all |
| D5 | Codenames are watermarks in four places only, never identifiers | theme without cost | R8 | all |
| D6 | Layers 0–3 with a downward-only import rule and an allowed-imports matrix checked by an AST test | testable architecture | R2 | all |
| D7 | Composition through one `Runnable` Port; teams and flows never import models or each other | no import cycles | R5 | agents, teams, flows, models |
| D8 | Roles belong to `teams`, as free strings | `Runnable` stays pure | R5 | teams |
| D9 | `policy` is a service in layer 2; the authorizer Port is in `base`; runtime never imports optional services | no optional service required to run | R4 | policy, gateway, agents |
| D10 | `auth` is a component in layer 0, separate from `base` (it does I/O); `policy` is authorization, `auth` is authentication | `base` stays free of I/O | R11 | auth, models, store, tools |
| D11 | Every documented non-interactive auth mode is supported over time; extension point for others; interactive login never | breadth without prompts | R11 | auth |
| D12 | RSA signing with the pure-Python `rsa`; not `google-auth`, not `cryptography` | `cryptography` is compiled (14 MB) | R11 | auth, models |
| D13 | One implementation per provider: stdlib REST; no selector, no fallback, no SDK discovery (replaces an earlier auto-detect design) | simplicity, size | R9 | models |
| D14 | SDKs are dev dependencies and differential oracles only; compatibility at the data level; bring-your-own through `Runnable` | no SDK in production | R9 | models, tools |
| D15 | MCP client lives in `tools`, not `gateway` (replaces its first placement in `gateway`); extra `mcp` | one tool abstraction | R10 | tools, gateway |
| D16 | MCP implementation is an explicit `impl` argument, default built-in; no env or config | no selection machinery | R10 | tools |
| D17 | `tools → prompts` is forbidden (replaces an earlier allowance); MCP prompts use `base` messages | no same-layer import | R2, R10 | tools, prompts |
| D18 | Exactly three prefixed environment variables; credentials use provider-standard names | bounded surface | R11 | base, auth |
| D19 | Provider Vertex AI renamed `google` (Google renamed the product in April 2026) | accuracy | R9 | models |
| D20 | `prompts` follows liteprompt's design without Jinja2; the engine is a standard-library one (`prompts/engine.py`: `{{ }}`, `if`, `for`, filters; no `set`, `macro`, `include`) and `jinja2` is gone from the dependencies (done 2026-11-02) | Jinja2 pulls compiled code | R13 | prompts |
| D21 | Docs are a wiki, one section per component; README to shrink to a short entry | findability | R15 | docs |
| D22 | High-level requirements and design live in steering (`10`, `11`, `12`), component specs cite them; steering files are named `NN-topic.md` | one place, fits Kiro | R15 | specs, steering |
| D23 | The first project name was replaced by a second one, which was then dropped too (trademark conflicts); the new name is under choice | trademark | — | all (rename) |
| D24 | New data structures are dataclasses, not pydantic (the base spec's "use Pydantic models" criterion is superseded); existing models move later (O4) | pydantic is a core dependency being removed | R21 | base, all |
| D25 | Token counting is approximate in the core (standard library); exact counts use `tiktoken` through the optional `tiktoken` extra, imported lazily and never on the runtime path (resolves O5) | serverless footprint; no tokenizer SDK in core | R28 | models |
| D26 | MCP resources are a Port in `base` (list and read by URI, MIME type, text or bytes), implemented by the MCP client in `tools`; the MCP prompt facet returns `base` messages and does NOT implement `PromptBuilderInterface` (resolves O7) | one resource contract, reusable by prompts and memory | R10 | base, tools |

## Open decisions (not yet taken)
- **O1** The project name (replaces D23): constraints: at most 7 letters, related to air or sky, able to contain the cloud and weather codenames. Candidates seen: welkin, tropos, airmass, mizzle, zenith, aether.
- **O2** Trademark check at the registries (USPTO, TMview, WIPO; classes 9 and 42) for the chosen name. Lesson from the dropped name: a web search alone found conflicts (an AI sales-automation company claiming the same marks, a funded AI app, an open-source agent orchestrator), so the registry search comes before reserving the PyPI name.
- **O4** Moving the core models from pydantic to dataclasses, and when.
- ~~**O5** `tiktoken`: keep, drop, or make pluggable.~~ Taken as **D25** (optional `tiktoken` extra, lazy; stdlib approximate counter in core).
- **O6** Where `base/http.py` goes, given that `base` must do no I/O; and whether cloud secret managers are in scope of `auth`.
- ~~**O7** Where MCP resources live; whether the MCP prompt facet implements `PromptBuilderInterface`.~~ Taken as **D26** (resource Port in `base` implemented by the MCP client; prompt facet returns `base` messages, not `PromptBuilderInterface`).
- **O8** Whether decision models (Jev) get their own milestone in `models` and a selector in `gateway`.
- **O9** Policy: the text syntax in the first release (or JSON and TOML first), how much of the Cedar grammar, how closely Cedar compatibility is promised, and whether an official conformance suite is available and under which licence.
- **O10** Policy: how principals map from IAM roles and JWT claims (one fixed way, or defined by each application), the policy-set cache lifetime and the evaluation time limit.
- **O11** Agents: the names `BaseAgent` and `Agent` and whether the operation list misses anything (for example a streaming-chunk hook); streaming hooks on each chunk or only on the complete response; the defaults for retry limit, hook time limit, maximum steps and consecutive failure limit; the budget values.
- **O12** Agents and gateway: who writes the operation description (the agent, the calling application, or the gateway from the conversation).
- **O13** Agents: whether a tool failure goes back to the model by default or stops the run, per error type; whether checkpointing is on by default in Lambda or opt-in.
- **O14** Gateway: which MCP specification version to target and whether responses stream.
- **O15** Gateway: the registry store, DynamoDB only or also S3 or Parameter Store.
- **O16** Gateway: the default and maximum toolset size, and the budget values.
- **O17** Gateway: scope-token key management and rotation.
- **O18** Gateway: JWT signature verification in the gateway itself (RSA without a compiled library), and whether the gateway also fronts model calls (the router) or only tools.
