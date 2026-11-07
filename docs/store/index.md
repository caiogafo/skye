---
title: "store"
codename: "lake"
status: current
last_updated: 2026-11-02
---

# store

*codename: lake*

External state: in-memory, file, DynamoDB, Redis, PostgreSQL.

## Router state in a store

A router keeps the health, cooldown and rate-limit usage of each model. Pass a store to keep that state between the invocations of a
serverless function: `ModelRouter({"chat": ["openai/gpt-4o-mini"]}, storage=backend)`. Import every backend from `skye.store`.

```python
from skye.store import DynamoDBBackend, FileSystemBackend, PostgreSQLBackend, RedisBackend

RedisBackend(redis_url="redis://localhost:6379", key_prefix="skye:prod:")        # extra: pip install skyeai[memory]
DynamoDBBackend(table_name="skye-router-state", region_name="us-east-1")          # AWS
PostgreSQLBackend(...)                                                            # extra: pip install skyeai[postgres]
FileSystemBackend(base_path="/tmp/skye_router_state")                             # a local directory
```

Inside an AWS Lambda with the Durable Execution SDK, `DurableFunctionBackend(context)` keeps the state across the steps and retries of a
workflow. The runnable example is `examples/serverless/serverless_router_example.py`.
