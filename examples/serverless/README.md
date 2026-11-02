# Serverless examples

Skye is built for serverless architectures, where the size of the library and its cold start make a difference: the core is the standard
library, and a user installs only the extras they need.

- `lambda_handler.py`: a handler that creates its client once, outside the handler, so a warm invocation pays nothing.
- `serverless_router_example.py`: a router whose state (health, rate limits) lives in an external store, because a serverless process does
  not survive between invocations. Redis and PostgreSQL come with the `memory` extra; DynamoDB needs `boto3`.

Run one with `python examples/serverless/lambda_handler.py` (the tests in `tests/examples` run every example offline).
