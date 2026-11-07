Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, Optional services, Store layout, Extras and budgets)

# Design Document: memory

## Overview
`memory` is the services layer-2 component (codename dew). It gives an agent conversation memory and state memory behind the memory
Port of `base`, and persists through the storage Port, so it owns no backend (Requirement 52.1, 12.1). It imports only `base`, `store`
and `auth` (`11-design.md`, "Allowed imports"). Runtime components never import it: they receive a `MemoryInterface` by injection or
through the memory hook points (Requirement 52.3, 4.1; D9). Everything durable is external (`00-rules`, "Serverless first"): nothing
survives between invocations in the process. The layer, the allowed imports, the Ports and the extras policy are in the steering
sections named above and are not restated here.

## Current state
`src/skye/memory/__init__.py` holds only `MemoryEntry` (id, content, memory_type, embedding, metadata, created_at), a `Validated`
dataclass that satisfies `MemoryEntryLike`. There is no memory implementation, no conversation store and no test of the component. The
Port `MemoryInterface` in `base` has four methods, all synchronous: `store`, `retrieve(query, limit, filters)`, `get_by_id` and
`delete`. The storage Port is asynchronous and has `get`, `set`, `increment`, `get_multiple` and `set_multiple` only: no delete, no
listing by prefix. The extra `memory` declares `redis`; Requirement 52.2 says `redis` and `asyncpg`, and D30 moved `asyncpg` to the
extra `postgres`. Those three facts shape the design and are listed under "Open points".

## Architecture
```
memory/
  entry.py          MemoryEntry (exists in __init__.py today)
  conversation.py   ConversationMemory: append and load the messages of a session, with a window
  state.py          StateMemory: named state of a session (key to JSON value), versioned
  entries.py        EntryMemory: implements MemoryInterface over a StorageBackend (store, retrieve, get_by_id, delete)
  index.py          the keys and the index layout in the storage backend (below)
```

### Two kinds of memory (Requirement 52.1)
Conversation memory keeps the ordered messages of a session (`SkyeMessage` and its role variants from `base`) and returns the last N
or the messages that fit a token budget. State memory keeps a small JSON document per session or per name, for what an agent must
remember between invocations that is not a message (for example the `AgentState` checkpoint is the agent's own and goes straight to
the storage Port; state memory is for application facts). Entry memory is the `MemoryInterface` form: typed entries (episodic,
semantic, persona) retrieved by query.

### Layout in the storage backend
All keys start with `memory:<namespace>:` so that a namespace is the unit of isolation (one namespace per user, tenant or agent, chosen
by the caller). A session's messages are stored as a list under one key per page of fixed size, with a counter incremented through
`increment` to give the next position atomically; appending writes a new page entry and never rewrites the others. Reading the last N
reads the last pages with `get_multiple`. A page size and a window are arguments with no hidden default beyond what is documented.
Entries are stored one per key, `memory:<ns>:entry:<id>`.

### Retrieval
`retrieve(query, limit, filters)` needs to find entries without scanning. The storage Port cannot list keys, so entry memory keeps an
index document per namespace and per memory type (`memory:<ns>:index:<type>`) holding the entry ids with a short text for keyword
scoring. Keyword retrieval (lexical ranking in the standard library) is the default and needs nothing else. When the caller passes a
`VectorEncoderInterface` (from `base`), entries are embedded at `store` time and retrieval ranks by cosine similarity, still in the
standard library over the stored vectors; no vector database is required. Both paths return entries ordered by relevance (Port
contract). An index document that grows without bound is a serverless risk, so it is capped by an argument and the oldest ids leave it.

### Sync and async
The Port today is synchronous and the storage Port asynchronous. The component implements the async forms `astore`, `aretrieve`,
`aget_by_id`, `adelete` as the real ones (the `a` prefix rule, `00-rules`), and the synchronous names run them to completion with the
same helper the router uses (`asyncio.run`, or a worker thread when a loop is already running). Whether the Port in `base` gains the
async names is a Port change and is listed under "Open points".

### Optional services and agents
An agent gets memory through the memory hook points (memory read, memory write; Requirement 39.5) with a `MemoryInterface` it was
given. `memory` never imports `agents`, and `agents` never imports `memory`.

## Data Models
`MemoryEntry` (exists). `ConversationMemory` and `StateMemory` hold a namespace, a session id and the backend; they are plain classes
with no hidden global. Stored values are JSON dictionaries: messages through the `base` message serialization (the same one the
`AgentState` uses, D45).

## Error Handling
A backend failure surfaces as the `ProviderError` of `store`. An invalid entry raises `ValidationError` (Port contract). A missing id
returns `None` for `get_by_id` and `False` for `delete`, and an unmatched query returns an empty list (Port footer). Concurrent appends
use `increment` for the position so that two tasks never write the same slot.

## Testing Strategy
Tests in `tests/unit/memory/` run against `InMemoryBackend` and `FileSystemBackend`: append and load a conversation, the window and
the token budget, concurrent appends from `asyncio.gather` with no lost message, state read and write, entry store then retrieve by
keyword, retrieval with a fake `VectorEncoderInterface`, a capped index, the namespace isolation, and `get_by_id` and `delete` for an
unknown id. A Port-compliance test runs `EntryMemory` through the shared compliance checker (Requirement 16.7).

## Correctness Properties
1. Messages appended to a session are returned in the order they were appended, with none lost under concurrent appends.
2. A window of N never returns more than N messages, and returns the last N.
3. `store` then `get_by_id` returns an equal entry; after `delete`, `get_by_id` is `None` and `delete` is `False`.
4. `retrieve` never returns an entry from another namespace or one that does not match the filters.
5. With no encoder, retrieval is lexical and needs no model; with an encoder, results are ordered by similarity.
6. The component keeps no state outside the backend: a new instance over the same backend sees the same data.
7. `memory` imports no component outside `base`, `store` and `auth`, and no runtime component imports `memory`.

## Open points (not decided here)
- The storage Port has no delete and no listing by prefix. Entry memory works around it with an index document, which is a design cost
  (size cap, rewrite on every store). Adding `delete` and a prefix `list` to the storage Port is a Port change; Requirement 12.3 says
  the Port is defined first. The owner decides which way before task 3.
- The memory Port is synchronous and the storage Port asynchronous; whether the Port gains `astore`, `aretrieve`, `aget_by_id` and
  `adelete` (the `a` prefix rule).
- Requirement 52.2 names `asyncpg` in the `memory` extra; D30 moved it to the extra `postgres`; the extra `memory` today declares only
  `redis`, which the `store` module `redis.py` imports. The requirement or the extras table needs one correction in steering.
- Whether the first release ships entry memory with retrieval, or conversation and state memory only.
