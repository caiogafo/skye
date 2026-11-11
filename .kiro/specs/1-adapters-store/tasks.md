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

- [x] 2. Conformance suite
  - [x] 2.1 Shared test cases for the Port promises: set then get, absent key is `None`, expiry, `get_multiple` keys and order, `set_multiple`, atomic `increment` under concurrent tasks
    - Evidence (2026-11-11): `src/skye/store/conformance.py`, public (D98): `check_key_value`, `check_counter`, `check_scan` and `check_backend`, with a `FakeClock` so expiry is checked without sleeping. Every promise is named in its assertion message. The suite also covers the D95 rejections, keys containing `%`, `_`, `*`, `?` and `[`, and 50 concurrent increments. `tests/unit/store/test_conformance.py::test_the_suite_is_not_blind` shows that a backend which keeps expired values fails the suite.
    - _Requirements: 12.1, 12.5, 12.6, 23_
  - [x] 2.2 Run the suite against the memory and file backends
    - Evidence: `tests/unit/store/test_conformance.py::test_backend_conforms[memory]`, `[file]` and `[durable_function]`. The durable function backend is checked for key-value and counter only, because it has no scan (D98).
    - _Requirements: 12.1, 23_
  - [x] 2.3 Run the suite against DynamoDB, Redis and PostgreSQL with fake clients, offline
    - Evidence: `tests/unit/store/fakes.py` provides three fakes:
      - a boto3 DynamoDB resource that rejects floats, pages `Scan` and defers one `BatchGetItem` key;
      - a `redis.asyncio` client with expiry on the clock, the increment script and `SCAN`;
      - a SQL executor that implements each named statement, and checks that every parameter is in the SQL and no value is.
      The tests are `test_backend_conforms[dynamodb]`, `[redis]` and `[postgres]`. Not verified: the SQL text against a real PostgreSQL server, and the Lua script against a real Redis.
    - _Requirements: 12.1, 23_

- [x] 3. Fixes the suite exposes
  - [x] 3.1 One meaning of the time to live, checked on read by every backend
    - Evidence: D95. `check_ttl` in `src/skye/base/interfaces/storage.py` accepts `None` or a positive `int` and raises `ValidationError` before any write. Every backend checks the expiry on read; DynamoDB does so before its own TTL deletion. Checked by conformance `check_key_value`.
    - _Requirements: 12.5; D95_
  - [x] 3.2 Raise `MissingExtraError` naming the extra when a driver is absent
    - Evidence: each backend calls `missing_extra(..., extra=...)`:
      - `dynamodb.py` names `aws`;
      - `redis.py` names `redis`;
      - `postgres.py` names `aws`, `postgres` or `postgres-asyncpg`. When no driver is available, `choose_driver` names `postgres` and adds a note about `postgres-asyncpg` and the Data API.
      Tests in `tests/unit/store/test_drivers_and_errors.py`: `test_missing_boto3_names_the_aws_extra`, `test_missing_redis_names_the_redis_extra` and `test_no_driver_names_the_extras`.
    - _Requirements: 7.3, 12.2; D99_
  - [x] 3.3 Move the blocking calls (boto3, pg8000, file I/O) out of the event loop with `asyncio.to_thread`
    - Evidence: `dynamodb.py`, `file.py`, and in `postgres.py` the `DataApiExecutor` and `Pg8000Executor`.
    - _Requirements: 12.1; Python rules of `00-rules`_
  - [x] 3.4 Make `increment` atomic under concurrent tasks
    - Evidence, per backend:
      - memory, file and durable function: a lock. The file backend documents that it is not atomic across processes.
      - DynamoDB: one `UpdateItem` with `ADD`; an expired counter restarts through a condition.
      - Redis: one Lua script.
      - PostgreSQL: one `INSERT ... ON CONFLICT ... RETURNING`.
      Checked by conformance `check_counter` (50 concurrent increments).
    - _Requirements: 12.1_
  - [x] 3.5 Wrap client errors in `ProviderError` with the backend name and the operation; never log a value, a password or a credential
    - Evidence: `provider_errors` in `src/skye/store/_common.py` raises the message `"<backend>: <operation> failed (<error type>)"` and keeps the original error as `__cause__`; test `test_client_errors_become_provider_errors_without_secrets`. Every PostgreSQL statement takes its values as parameters, never in the SQL text (the old `set_multiple` built the SQL from keys and values), and the table name is checked as an identifier.
    - _Requirements: 18.1_
  - [x] 3.6 Remove the silent default region `us-east-1` of `DynamoDBBackend`
    - Evidence: `region_name=None` falls back to the AWS configuration; test `test_dynamodb_has_no_default_region`.
    - _Requirements: 12.1, 20_

- [x] 4. Choosing a backend (D97, D98; replaces the default durable backend)
  - [x] 4.1 `backend(name, **config)`, `register_backend(name, factory)` and `available_backends()`; the library never picks a durable backend by itself
    - Evidence: `src/skye/store/factory.py`. The built-in backends are registered by module path, so naming one imports only that module. Tests `test_backend_by_name` and `test_register_backend`. The planned `default_durable_backend()` is not built (D97).
    - _Requirements: 12.2, 12.6; D97, D98_
  - [x] 4.2 The router keeps `InMemoryBackend` as its default
    - Evidence: `src/skye/router` is unchanged (D97); `docs/store/index.md` says when to pass a durable backend.
    - _Requirements: 12.2; D97_
  - [x] 4.3 Capability Ports in `base`: `KeyValueStore`, `CounterStore` and `ScanStore`; `StorageBackend` is key-value plus counter
    - Evidence: `src/skye/base/interfaces/storage.py`:
      - a new `delete` method;
      - `connect` and `close` are optional;
      - `get_multiple` and `set_multiple` have default implementations.
      Every backend implements the Ports it can: all but the durable function implement `ScanStore`. Checked by `tests/unit/test_port_signatures.py`.
    - _Requirements: 12.4; D98_
  - [x] 4.4 PostgreSQL driver chain: RDS Data API, then pg8000, then asyncpg
    - Evidence: `src/skye/store/postgres.py`: `choose_driver`, `DataApiExecutor`, `Pg8000Executor`, `AsyncpgExecutor`, and one set of statements with `:name` parameters. Tests:
      - `test_data_api_comes_first_when_the_arns_are_given`, `test_pg8000_then_asyncpg`, `test_forced_driver`;
      - `test_data_api_executor_types_the_parameters`, `test_pg8000_executor_passes_named_parameters_and_maps_columns`, `test_asyncpg_executor_uses_positional_parameters`;
      - `test_positional_numbers_each_name_once`, `test_connection_arguments`.
    - _Requirements: 12.2; D100_

- [x] 5. Packaging and budgets
  - [x] 5.1 Importing `skye.store` loads no third-party library; the budget tests for the `store` modules pass
    - Evidence: `tests/unit/store/test_structure.py::test_importing_the_store_loads_no_driver`. Files updated:
      - `pyproject.toml`: one extra per backend (`redis`, `postgres`, `postgres-asyncpg`, `aws`); `memory` is empty;
      - `budgets.toml`: `[extras.redis]`, `[extras.postgres]` (to be measured) and `[extras.postgres-asyncpg]`; `aws` is not gated, because boto3 is preinstalled in Lambda;
      - the matrix of `.github/workflows/budgets.yml`;
      - `tests/budget/test_extras_footprint.py` and `tests/budget/test_boundary_rule.py`.
    - _Requirements: 7.3, 12.1, 12.2; D99_
  - [x] 5.2 No component outside `store` implements a storage Port
    - Evidence: `tests/unit/store/test_structure.py::test_only_store_implements_the_storage_ports`.
    - _Requirements: 12.1_
  - [x] 5.3 Correct the PostgreSQL and `DurableFunctionBackend` lines of Requirement 12.1 and of the "Store layout" table in steering
    - Evidence:
      - steering: D96 to D100 in `12-decisions.md`, Requirements 12.1 to 12.6 and 52.2 in `10-requirements.md`, and the "Store layout" table of `11-design.md`;
      - docs and examples: `docs/store/index.md`, `docs/getting-started.md`, `README.md` and `examples/store/backends.py`.
    - _Requirements: 12.1, 15.4; D96_

- [x] 7. Redis and Valkey (D102)
  - [x] 7.1 One `RedisBackend` for Redis and Valkey: valkey-py when installed, else redis-py; `driver=` forces one; `backend("valkey", ...)` is a second name
    - Evidence (2026-11-11): `src/skye/store/redis.py` (`choose_driver`); `src/skye/store/factory.py`; extras `valkey` and `redis` in `pyproject.toml`, `[extras.valkey]` in `budgets.toml` (to be measured) and the workflow matrix. Tests in `tests/unit/store/test_drivers_and_errors.py`: `test_valkey_then_redis` (four cases), `test_missing_redis_and_valkey_names_the_valkey_extra` and `test_valkey_is_a_second_name_for_the_redis_backend`. The vector store is open decision O58.
    - _Requirements: 12.2; D102_

- [x] 6. Final checkpoint
  - [x] 6.0 Validate the code against every criterion this spec points to (`requirements.md`: Requirements 12.1 to 12.6 of `10-requirements.md`, and decisions D95 to D100 and D102). Also check 52.2: the `memory` extra declares no driver. For each criterion, write one evidence line: the file or function that realizes it and the test that checks it. A criterion with no code or no test is a finding.
    - Evidence (2026-11-11, by reading code and tests; no test was run): R12.1 to R12.6, R52.2, D95 to D100 and D102 each map to a file or function and a test in `.agents/tasks/1-adapters-final-checkpoint-2026-11-11.md`. All have code. Findings: S1, R12.2 and D97 had no test of the in-memory default; closed by `tests/unit/router/test_router_exports.py::test_the_default_backend_is_in_memory_and_the_store_picks_no_durable_one` (`ModelRouter`, `ModelHealth`, `RateLimitTracker`, no `default_durable_backend`). S3, `test_importing_the_store_loads_no_driver` did not list `valkey`; closed (`DRIVERS` in `tests/unit/store/test_structure.py`). Both files: 5 passed. Open: S2, R12.3 is a process rule with no code and no test.
  - [x] 6.1 Run `uv run pytest tests/unit/store tests/unit/router tests/budget -q`, the store doctests and `make budget`. Measure the `postgres` (pg8000) and `valkey` extras in the footprint job and set their numbers in `budgets.toml`.
    - Evidence (2026-11-11): `uv run pytest tests/unit/store tests/unit/router tests/budget -q` → 502 passed, 11 deselected (the 11 are the `budget` marker, which `make budget` runs: 11 passed); `uv run pytest tests/budget -q` → 318 passed. Doctests of `src/skye/store/*.py` and `src/skye/base/interfaces/storage.py` (with `ELLIPSIS | NORMALIZE_WHITESPACE`, as `tests/unit/test_docstrings.py`; plain `python -m doctest FILE` puts the file folder first on `sys.path` and breaks `import http`) → 59 examples with `prompt_parts` and `cost`, 0 failed. Two fixes: the `check_ttl` doctest in `storage.py` expected the message without the `| Details:` part of `ValidationError`; the first example of `store/postgres.py` needs a driver and now carries `# doctest: +SKIP`. `make differential` → 23 passed. Measured with `make budget` on macOS arm64 (not Linux x86_64; the footprint job confirms): `postgres` +1.7 MB, 6 packages, 0 compiled; `valkey` +1.1 MB, 2 packages, 0 compiled (`redis` +2.6 MB for comparison). `budgets.toml`: `[extras.postgres]` 4 → 3 MB (target 2), `[extras.valkey]` 13 → 3 MB (target 2); no limit went up. Clean venv (Python 3.11, `uv build --wheel` then `uv pip install` of `skyeai-0.1.1-py3-none-any.whl`, run outside the repo): `import skye.store` loads none of boto3, botocore, redis, valkey, pg8000, asyncpg; `backend("memory")` returns `InMemoryBackend`; `check_backend(lambda c: InMemoryBackend(clock=c))` → `['key_value', 'counter', 'scan']`, and no driver loaded after it.
    - _Requirements: 12, 7.10_
