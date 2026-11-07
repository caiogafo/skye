Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Ports, Store layout, Extras and budgets)

# Design Document: store

## Overview
`store` is the adapters layer-1 component (codename lake). It is the one place for state backends: each backend is a module that
implements the `StorageBackend` Port of `base`, and no other component keeps a copy of a backend (Requirement 12.1). Durable state is
external (`00-rules`, "Serverless first"), so a backend never relies on a cache or a pool surviving between invocations. `store`
imports only `base` and `auth` (`11-design.md`, "Allowed imports"); credentials come through `auth`, with `boto3` as the one runtime
library the serverless environment already provides. The layer, the allowed imports, the Port rules and the extras policy are in the
steering sections named above and are not restated here.

## Current state
Seven files exist in `src/skye/store/`, moved from the old `routes/storage_backends.py`: `memory.py`, `file.py`, `dynamodb.py`,
`redis.py`, `postgres.py`, `durable_function.py` and `__init__.py`. The Port in `base` has five methods, all asynchronous: `connect`,
`get`, `set` (with a time to live), `increment` (atomic, with a time to live), `get_multiple` and `set_multiple`. The only user is the
router (`ModelRouter` and the health tracker). No test exercises any backend directly: the only test that mentions them is
`tests/unit/router/test_router_exports.py`. The example `examples/store/backends.py` and the page `docs/store/index.md` exist.

## Architecture
```
store/
  memory.py            InMemoryBackend       core, standard library
  file.py              FileSystemBackend     core, standard library
  dynamodb.py          DynamoDBBackend       boto3, lazy; first-choice durable backend
  redis.py             RedisBackend          extra `memory` (`redis.asyncio`), lazy
  postgres.py          PostgreSQLBackend     extra `postgres` (`asyncpg`), lazy (D30)
  durable_function.py  DurableFunctionBackend  takes a DurableContext from the caller, no import of the SDK
```
Each module is reached only through the Port. A new backend is one new module (extension-point table of `11-design.md`).

### Contract every backend meets (Requirement 12.1, Port footer)
A value is a JSON-like dictionary. `get` of an absent or expired key returns `None` and never raises; an expired entry is absent.
`increment` is atomic and stores the counter under the field `count`; `get_multiple` returns every requested key, with `None` for
the absent ones; `set_multiple` writes the keys with one time to live. An unreachable backend raises `ProviderError`; invalid data
raises `ValidationError`. One shared conformance suite runs the same cases against every backend that can run offline (memory, file)
and against the others with a fake client, so the Port promises are tested once and not per module.

### Time to live
A `ttl` of `None` means no expiry. Today the memory and file backends treat a `ttl` of `0` as no expiry (they test truthiness), while
DynamoDB stores an expiry attribute that only takes effect when the table's TTL is enabled and is not checked on read. The shared
suite fixes one meaning (assumption: `ttl=None` is no expiry, and a positive number of seconds is an expiry that every backend also
checks on read, so an entry past its time is absent even before the service removes it); the zero case follows the owner's answer in
the open points.

### Lazy imports and missing extras
`boto3`, `redis` and `asyncpg` are imported inside the method that first needs them, never at module import time (`00-rules`,
"Dependencies"). A missing library raises `MissingExtraError` naming the extra, as the rest of the library does (invariant 8 of the
correctness properties in `11-design.md`); today the three modules raise a plain `ImportError`, which is a gap.

### Async and blocking
`00-rules` says never to block in an async function. `DynamoDBBackend` calls the synchronous `boto3` resource inside `async def`
methods, and `FileSystemBackend` does synchronous file I/O. Both move the blocking call to a worker thread with
`asyncio.to_thread` (a thread inside one invocation, no background thread, no process). The worker thread does not outlive the call.

### Default durable backend (Requirement 12.2)
Requirement 12.2 says that where a durable backend is needed and none is declared, the library defaults to DynamoDB, and to the
pure-Python driver where a backend has two. Today the router defaults to `InMemoryBackend` when it gets no storage argument, and no
function chooses a durable default. Where that default is applied (a factory in `store`, or the caller) and what "declared" means
(an argument, a configuration key, an environment variable) is not stated in steering and is listed under "Open points".

### Identity and credentials
`DynamoDBBackend` uses the default `boto3` credential chain of the runtime, and the table name is a required argument. The hardcoded
default region `us-east-1` is a gap: the region comes from the caller or from the runtime configuration, with no silent default.
`RedisBackend` and `PostgreSQLBackend` take their URL or connection string from the caller (`${VAR}` substitution is the caller's
configuration layer, Requirement 20.4). No backend logs a key's value, a URL with a password, or a credential.

## Data Models
No new model is needed. A stored value is a `dict[str, Any]`; the expiry is kept beside it by the backend (`_ttl` in a file, a tuple in
memory, the `ttl` attribute in DynamoDB), and the backend strips its own metadata on read.

## Error Handling
A backend wraps its client's exceptions in `ProviderError` with the backend name and the operation (`raise ... from e`) and lets a
missing key be a normal `None`. Connection failures surface at `connect` or at the first call, not at construction.

## Testing Strategy
Tests are in `tests/unit/store/`: the shared conformance suite for memory and file, the same suite with a fake DynamoDB resource, a
fake Redis client and a fake asyncpg pool, the expiry on read, atomic `increment` under concurrent tasks (`asyncio.gather`), the
missing-extra error for the three lazy libraries, and that importing `skye.store` imports none of them (the lazy-import budget).
The example `examples/store/backends.py` keeps running under `tests/examples`. Property-based tests fit the set and get round-trip.

## Correctness Properties
1. `set(k, v)` then `get(k)` returns `v` until it expires (every backend).
2. `get` of an absent or expired key is `None` and never raises.
3. N concurrent `increment(k, 1)` calls return N distinct values and the final count is N (atomicity, Port footer).
4. `get_multiple(keys)` has exactly the requested keys, in the order asked, with `None` for the absent ones.
5. `set_multiple` followed by `get_multiple` returns what was written.
6. A backend's library is imported only when that backend is first used; its absence raises `MissingExtraError` naming the extra.
7. Importing `skye.store` imports no third-party library.
8. No component outside `store` defines a class that implements `StorageBackend` for production use (Requirement 12.1).

## Open points (not decided here)
- Requirement 12.1 lists four backends (in-memory, file, DynamoDB, Redis). The code also has `PostgreSQLBackend` (extra `postgres`, D30)
  and `DurableFunctionBackend`. The "Store layout" table of `11-design.md` says PostgreSQL is "used by `memory`" under the extra
  `memory`, which D30 supersedes. The steering lists need a correction (Requirement 12.1 and the table) before the spec claims them;
  the owner also decides whether `DurableFunctionBackend` stays.
- Where the default durable backend of Requirement 12.2 is applied and what "declared" means.
- Whether `ttl=0` means "no expiry" or "already expired".
- Whether `memory` needs a delete or a prefix query on the Port (Requirement 12.3 requires the Port first); decided with the `memory` spec.
