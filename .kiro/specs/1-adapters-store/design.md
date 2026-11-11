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
Rebuilt on 2026-11-11 after decisions D95 to D100. `src/skye/store/` holds the six backends, `_common.py` (clock, expiry, error
wrapping), `factory.py` (`backend`, `register_backend`, `available_backends`) and `conformance.py` (the public suite). The Ports are
in `src/skye/base/interfaces/storage.py`. The router is still the only user; `memory` and the agents archive (D93) will use the scan
capability.

## Architecture
```
base/interfaces/storage.py  KeyValueStore, CounterStore, ScanStore (Protocols); StorageBackend (ABC: key-value + counter);
                            check_ttl, check_key
store/
  _common.py           clock, expiry_of / is_expired, provider_errors, check_data / check_items / check_limit
  memory.py            InMemoryBackend         key-value, counter, scan   no extra (the default, D97)
  file.py              FileSystemBackend       key-value, counter, scan   no extra
  dynamodb.py          DynamoDBBackend         key-value, counter, scan   boto3 (extra `aws` outside Lambda)
  redis.py             RedisBackend            key-value, counter, scan   valkey-py (`valkey`), else redis-py (`redis`); D102
  postgres.py          PostgreSQLBackend       key-value, counter, scan   Data API (boto3), pg8000 (`postgres`), asyncpg (`postgres-asyncpg`)
  durable_function.py  DurableFunctionBackend  key-value, counter         the caller's durable context
  factory.py           backend(name, **config), register_backend, available_backends
  conformance.py       check_backend and the three checks, FakeClock (public, D98)
```
Each module is reached only through the Ports. A new backend is one new module, or a backend outside Skye added with
`register_backend` and checked with `check_backend` (D98).

### Contract every backend meets (Requirement 12, Port footer)
A value is a JSON-like dictionary. `get` of an absent or expired key returns `None` and never raises; `delete` returns whether a live
value was there. `increment` is atomic, stores `{"count": n}`, starts an absent or expired counter at 0, and sets (or with `None`
removes) the expiry. `get_multiple` returns every requested key in the order asked; `set_multiple` validates every item before writing
any. `keys(prefix, limit)` returns the live keys that start with the prefix, sorted, the prefix matched literally. An unreachable
backend raises `ProviderError`; invalid input raises `ValidationError`. The public conformance suite checks all of this once, against
every backend (offline, with fakes for the external stores).

### Time to live (D95)
`ttl` is `None` (no expiry) or a positive `int` of seconds; anything else raises `ValidationError` before a write (`check_ttl`). Every
backend computes the absolute expiry from its clock and checks it on read, so an expired value is absent even where the service deletes
it later (DynamoDB TTL); Redis uses its own `EX`. Backends take a `clock` argument (Redis: its client), so the suite checks expiry with
a fake clock and no sleep.

### Lazy imports and missing extras (D99)
Drivers are imported with `missing_extra(module, extra=...)` inside the method that first needs them, so `import skye.store` loads none
and a missing one raises `MissingExtraError` naming the extra of that backend. Extras belong to backends, never to components.

### Async and blocking
`boto3`, pg8000 and file I/O run in `asyncio.to_thread` (a thread inside one call, nothing outliving it). The pg8000 and asyncpg drivers
hold one connection per backend under a lock; the Data API has none.

### PostgreSQL (D100)
`choose_driver` picks the Data API when `cluster_arn` and `secret_arn` are given, else pg8000, else asyncpg, else `MissingExtraError`;
`driver=` forces one. `statements(table)` writes each operation once with `:name` parameters and no `::` cast (pg8000 and the Data API
read `:name`; asyncpg gets `$n` through `positional`, which skips quoted strings). The table name is checked as an identifier and every
value is a parameter. The expiry is a `DOUBLE PRECISION` of seconds, computed in Python from the backend's clock.

### No implicit durable backend (D97)
The library defaults to `InMemoryBackend` and never chooses a durable backend; the router keeps that default. In pure serverless the
caller passes the durable function backend or an external store, directly or with `backend(name, **config)`.

### Identity and credentials
`DynamoDBBackend` and the Data API use the default `boto3` credential chain; there is no default region (D97 era fix, task 3.6).
`RedisBackend` and `PostgreSQLBackend` take their URL or connection string from the caller (`${VAR}` substitution is the caller's
configuration layer, Requirement 20.4). No backend logs or puts in an error a stored value, a URL with a password, or a credential.

## Data Models
No new model is needed. A stored value is a `dict[str, Any]`; the expiry is kept beside it by the backend (`_skye_expires_at` in a
file, a tuple in memory, the `ttl` attribute in DynamoDB, `expires_at` in PostgreSQL and the durable context), and the backend strips
its own metadata on read.

## Error Handling
A backend wraps its client's exceptions in `ProviderError` with the backend name and the operation (`raise ... from e`) and lets a
missing key be a normal `None`. Connection failures surface at `connect` or at the first call, not at construction.

## Testing Strategy
Tests are in `tests/unit/store/`: the public conformance suite against all six backends (fakes in `fakes.py` for DynamoDB, Redis
and the SQL executor), the three PostgreSQL drivers with fake clients, the factory and registry, the missing-extra errors, wrapped
errors without secrets, and the structure rules (no driver at import, no backend outside `store`).
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
- ~~The backends of Requirement 12.1 and the "Store layout" table~~: settled by D96.
- ~~Where the default durable backend applies~~: settled by D97 (none is picked by the library; the caller chooses).
- ~~What `ttl=0` means~~: settled by D95 (rejected).
- Which further operations `memory` needs on the Ports (a vector store, D41): decided with the `memory` spec; `delete` and `keys` by
  prefix exist (D98).
