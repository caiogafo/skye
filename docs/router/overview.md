---
title: "Router overview (load balancing, YAML, health, fallbacks)"
status: current
last_updated: 2026-11-02
---

# Advanced Features

## Load Balancing and Routing

The router is the main entry point for load balancing across multiple providers and deployments:

```python
from skye.base.messages import UserMessage
from skye.router import ModelRouter, ModelTarget, RouteConfig
from skye.base.interfaces.router import RoutingStrategy

# Create router with multiple targets for an alias
router = ModelRouter(routes=[
    RouteConfig(
        alias="gpt-4",  # Use this alias as the model name
        targets=[
            ModelTarget(
                model="gpt-4",
                provider="openai",
                api_key="${OPENAI_API_KEY}",
                tpm=100000,
                rpm=1000,
                weight=2.0
            ),
            ModelTarget(
                model="gpt-4",
                provider="azure",
                api_key="${AZURE_API_KEY}",
                api_base="${AZURE_API_BASE}",
                tpm=80000,
                rpm=800,
                weight=1.0
            )
        ],
        strategy=RoutingStrategy.WEIGHTED
    )
])

# Use the router directly - it handles provider instantiation
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"  # This is the alias, router picks the best target
)

# Or use tag-based selection
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    tags=["premium", "paid"]
)

# Or combine both (model must have all specified tags)
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4",
    tags=["premium"]
)
```

## Router Configuration from YAML

```python
from skye.router import ModelRouter

# Load router from YAML file with environment variable substitution
router = ModelRouter.from_yaml("router_config.yaml")

# Use the router
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-3.5-turbo"  # Alias defined in YAML
)

# Or use tag-based selection
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    tags=["fast", "cheap"]
)
```

Example YAML configuration:
```yaml
# router_config.yaml
routes:
  - alias: "gpt-3.5-turbo"
    strategy: "rate_limit_aware"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 200000
        rpm: 2000
        tags: ["fast", "cheap", "general"]
      - model: "gpt-3.5-turbo"
        provider: "azure"
        api_key: "${AZURE_API_KEY}"
        api_base: "${AZURE_API_BASE}"
        tpm: 100000
        rpm: 1000
        tags: ["fast", "cheap", "general", "enterprise"]
  - alias: "gpt-4"
    strategy: "least_busy"
    targets:
      - model: "gpt-4"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 100000
        rpm: 500
        tags: ["smart", "expensive", "reasoning"]

fallbacks:
  - primary: "gpt-4"
    fallbacks: ["gpt-3.5-turbo"]

retry_policies:
  - error_type: "RateLimitError"
    max_retries: 3
```

## Flexible Model Selection

The router supports flexible model selection with both model names/aliases and tag-based filtering:

```python
# Use specific model or alias
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4"
)

# Use tag-based selection (router picks best model with these tags)
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    tags=["fast", "cheap"]
)

# Combine both (model must have all specified tags)
response = router.complete(
    messages=[UserMessage(content="Hello!")],
    model="gpt-4",
    tags=["premium"]  # Ensures gpt-4 has premium tag
)

# Async version
response = await router.acomplete(
    messages=[UserMessage(content="Hello!")],
    tags=["reasoning", "multilingual"]
)
```

## Rate Limiting and Health Tracking

The router automatically tracks rate limits and health metrics:

```python
# Check model health
health = router.get_model_health("gpt-4:openai:gpt-4")
print(f"Success rate: {health.success_rate:.1%}")
print(f"Average latency: {health.average_latency_ms:.1f}ms")

# Check usage stats
stats = router.get_usage_stats("gpt-4:openai:gpt-4")
print(f"TPM used: {stats.tpm_used}/{stats.tpm_limit}")
print(f"RPM used: {stats.rpm_used}/{stats.rpm_limit}")

# Check models in cooldown
cooled_down = router.get_cooldown_models()
for info in cooled_down:
    print(f"{info.model_id} cooled down until {info.cooldown_until}")
```

## Fallbacks and Retry Policies

```python
from skye.router import ModelRouter, FallbackConfig, RetryPolicyConfig

router = ModelRouter(
    routes=[...],
    fallbacks=[
        FallbackConfig(
            primary="gpt-4",
            fallbacks=["gpt-3.5-turbo", "claude-3-sonnet"]
        )
    ],
    retry_policies=[
        RetryPolicyConfig(error_type="RateLimitError", max_retries=3),
        RetryPolicyConfig(error_type="TimeoutError", max_retries=2)
    ]
)
```

## Serverless Support with External Storage

For serverless environments, use external storage backends:

```python
from skye.router import ModelRouter
from skye.store import RedisBackend, DynamoDBBackend

# Redis backend for persistent state
redis_storage = RedisBackend("redis://localhost:6379")
router = ModelRouter(
    routes=[...],
    storage=redis_storage
)

# DynamoDB backend for AWS Lambda
dynamodb_storage = DynamoDBBackend(
    table_name="skye-router-state",
    region="us-east-1"
)
router = ModelRouter(
    routes=[...],
    storage=dynamodb_storage
)
```
