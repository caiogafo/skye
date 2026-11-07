# Implementation Plan: store

## Overview
Milestones in build order for the `store` component (codename lake): the backends that exist, a shared conformance suite, the fixes the
suite exposes (expiry, missing extras, blocking calls, atomicity), the default durable backend, and packaging. Status is judged from
the code in `src/skye/store` and the tests, not from any former plan; the backends exist but have no test of their own. Each task cites
the steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it honors. Task IDs cited from
other documents are `store:N.k`. A task that depends on an open point of `design.md` says so.

## Tasks
- [x] 1. Backends (what exists)
  - [x] 1.1 `InMemoryBackend` and `FileSystemBackend` on the standard library
    - Evidence: `src/skye/store/memory.py`, `src/skye/store/file.py`.
    - _Requirements: 12.1_
  - [x] 1.2 `DynamoDBBackend` (boto3, lazy), `RedisBackend` (`redis.asyncio`, lazy), `PostgreSQLBackend` (`asyncpg`, lazy)
    - Evidence: `src/skye/store/dynamodb.py`, `src/skye/store/redis.py`, `src/skye/store/postgres.py`; extras `memory` and `postgres` in `pyproject.toml`.
    - _Requirements: 12.1; D30_
  - [x] 1.3 `DurableFunctionBackend` over a caller-supplied durable context
    - Evidence: `src/skye/store/durable_function.py`.
    - _Requirements: 12.1_
  - [x] 1.4 Package exports and a runnable example
    - Evidence: `src/skye/store/__init__.py`; `examples/store/backends.py`; `docs/store/index.md`.
    - _Requirements: 12.1, 24.2_

- [ ] 2. Conformance suite
  - [ ] 2.1 Shared test cases for the Port promises: set then get, absent key is `None`, expiry, `get_multiple` keys and order, `set_multiple`, atomic `increment` under concurrent tasks
    - _Requirements: 12.1, 23_
  - [ ] 2.2 Run the suite against memory and file backends
    - _Requirements: 12.1, 23_
  - [ ] 2.3 Run the suite against DynamoDB, Redis and PostgreSQL with fake clients (a fake `boto3` resource, a fake Redis client, a fake asyncpg pool), offline
    - _Requirements: 12.1, 23_

- [ ] 3. Fixes the suite exposes
  - [ ] 3.1 One meaning of the time to live, checked on read by every backend (the zero case follows the owner's answer in the open points)
    - Note: memory and file test truthiness; DynamoDB writes an attribute and never checks it on read.
    - _Requirements: 12.1_
  - [ ] 3.2 Raise `MissingExtraError` naming the extra when `boto3`, `redis` or `asyncpg` is absent, instead of a plain `ImportError`
    - Note: `src/skye/store/dynamodb.py`, `redis.py` and `postgres.py` raise `ImportError`; `boto3` is named as an extra only if the owner adds one.
    - _Requirements: 7.3_
  - [ ] 3.3 Move the blocking `boto3` calls and the file I/O out of the event loop with `asyncio.to_thread`
    - _Requirements: 12.1; Python rules of `00-rules`_
  - [ ] 3.4 Make `increment` of the memory and file backends atomic under concurrent tasks (a lock per backend, in-process only; the file backend documents that it is not atomic across processes)
    - Note: `increment` reads then writes through `await`, which can interleave once the file I/O runs in a thread.
    - _Requirements: 12.1_
  - [ ] 3.5 Wrap client errors in `ProviderError` with the backend name and the operation; never log a value, a password or a credential
    - _Requirements: 18.1_
  - [ ] 3.6 Remove the silent default region `us-east-1` of `DynamoDBBackend`: the caller or the runtime configuration gives it
    - _Requirements: 12.1, 20_

- [ ] 4. Default durable backend
  - [ ] 4.1 A function that returns the default durable backend (DynamoDB, or the pure-Python driver where a backend has two) when none is declared, and raises a clear error naming the missing table or setting
    - Note: blocked on the open point "where the default is applied and what declared means".
    - _Requirements: 12.2_
  - [ ] 4.2 Use it where the router currently falls back to `InMemoryBackend`, only if the owner agrees that the router's default changes
    - Note: changing the router's default alters behaviour for users with no storage argument.
    - _Requirements: 12.2_

- [ ] 5. Packaging and budgets
  - [ ] 5.1 `skye.store` imports no third-party library at import time; the budget tests for the `store` modules pass
    - _Requirements: 7.3, 12.1_
  - [ ] 5.2 No component outside `store` implements `StorageBackend` for production use; add the check to the existing structure tests if none covers it
    - _Requirements: 12.1_
  - [ ] 5.3 Correct the PostgreSQL and `DurableFunctionBackend` lines of Requirement 12.1 and of the "Store layout" table in steering, with a decision line, once the owner answers the open point
    - Note: steering is changed first and this spec cites the result; blocked on the open point.
    - _Requirements: 12.1, 15.4; D30_
