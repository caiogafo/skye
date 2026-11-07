---
title: "Skye Routing Guide"
status: current
last_updated: 2026-11-02
---

# Skye Routing Guide

## Overview

Skye provides a unified, comprehensive routing solution with health tracking, rate limiting, and advanced features. All configurations use Pydantic models for type safety and validation.

## Key Features

- **Model Aliases**: Define aliases that map to multiple provider targets
- **Health Tracking**: Monitor success rates, latency, and failures per model
- **Rate Limiting**: TPM (tokens per minute) and RPM (requests per minute) limits
- **Multiple Routing Strategies**: Round-robin, least-busy, rate-limit-aware, latency-based, cost-based, weighted, priority-based
- **Fallback Chains**: Automatic fallback to alternative models on failure
- **Cooldown Mechanisms**: Temporarily disable failing models
- **Tag-Based Routing**: Route based on model tags (e.g., "premium", "fast")
- **Pre-Call Checks**: Filter out models exceeding rate limits before making calls
- **Pydantic Models**: All configurations and metrics use Pydantic for validation

## Quick Start

### Option 1: Direct Model Registration

```python
import os
import skye
from skye.router import (
    ModelRouter,
    FallbackConfig,
    RetryPolicyConfig,
    AllowedFailsPolicyConfig,
)
from skye.router import RoutingStrategy
from skye import UserMessage
from skye import CompleteRequest

# Create provider instances
gpt4 = skye.provider("openai", api_key=os.getenv("OPENAI_API_KEY"))
gpt35 = skye.provider("openai", api_key=os.getenv("OPENAI_API_KEY"))

# Create router with all configurations in constructor
router = ModelRouter(
    strategy=RoutingStrategy.LEAST_BUSY,
    cooldown_seconds=60.0,
    enable_pre_call_checks=True,
    fallbacks=[
        FallbackConfig(primary="gpt-4", fallbacks=["gpt-3.5-turbo"])
    ],
    retry_policies=[
        RetryPolicyConfig(error_type="RateLimitError", max_retries=3),
        RetryPolicyConfig(error_type="TimeoutError", max_retries=2),
    ],
    allowed_fails_policies=[
        AllowedFailsPolicyConfig(
            error_type="RateLimitError",
            allowed_fails_per_minute=100
        )
    ],
)

# Register models with rate limits and tags
router.register_model(
    "gpt-4",
    gpt4,
    tpm=100000,
    rpm=500,
    tags=["premium", "high-quality"]
)
router.register_model(
    "gpt-3.5-turbo",
    gpt35,
    tpm=200000,
    rpm=2000,
    tags=["fast", "cheap"]
)

# Route requests
response = router.complete(
    messages=[UserMessage(content="What is the capital of France?")],
    model="gpt-4"
)
print(f"Response: {response.content}")
```

### Option 2: Aliases with Auto-Instantiation

```python
import os
from skye.router import (
    ModelRouter,
    ModelTarget,
    RouteConfig,
    FallbackConfig,
    RetryPolicyConfig,
)
from skye.router import RoutingStrategy
from skye import UserMessage
from skye import CompleteRequest

# Create router with aliases - providers instantiated automatically
# All policies configured in constructor
router = ModelRouter(
    routes=[
        RouteConfig(
            alias="gpt-3.5-turbo",
            targets=[
                ModelTarget(
                    model="gpt-3.5-turbo",
                    provider="openai",
                    api_key=os.getenv("OPENAI_API_KEY"),
                    tpm=200000,
                    rpm=2000,
                    tags=["fast", "cheap"]
                ),
                ModelTarget(
                    model="gpt-35-turbo",
                    provider="azure",
                    api_key=os.getenv("AZURE_API_KEY"),
                    api_base=os.getenv("AZURE_API_BASE"),
                    api_version="2024-02-15-preview",
                    tpm=100000,
                    rpm=1000,
                    tags=["fast", "cheap", "azure"]
                )
            ],
            strategy=RoutingStrategy.RATE_LIMIT_AWARE
        ),
        RouteConfig(
            alias="gpt-4",
            targets=[
                ModelTarget(
                    model="gpt-4",
                    provider="openai",
                    api_key=os.getenv("OPENAI_API_KEY"),
                    tpm=100000,
                    rpm=500,
                    tags=["premium", "high-quality"]
                )
            ]
        )
    ],
    strategy=RoutingStrategy.LEAST_BUSY,
    cooldown_seconds=60.0,
    fallbacks=[
        FallbackConfig(
            primary="gpt-4",
            fallbacks=["gpt-3.5-turbo"]
        )
    ],
    retry_policies=[
        RetryPolicyConfig(error_type="RateLimitError", max_retries=3)
    ],
)

# Use alias in requests - router selects best target
response = router.complete(
    messages=[UserMessage(content="What is the capital of France?")],
    model="gpt-3.5-turbo"  # This is an alias with 2 targets
)
print(f"Response: {response.content}")
```

## Configuration Models

All configurations use Pydantic models for type safety:

### ModelTarget

```python
import os
from skye.router import ModelTarget

# OpenAI target
openai_target = ModelTarget(
    model="gpt-4",
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    tpm=100000,  # Tokens per minute limit
    rpm=1000,    # Requests per minute limit
    tags=["premium", "high-quality"],
    weight=1.0,  # For weighted routing
    timeout=60.0,
    max_retries=3
)

# Azure target
azure_target = ModelTarget(
    model="gpt-4",
    provider="azure",
    api_key=os.getenv("AZURE_API_KEY"),
    api_base=os.getenv("AZURE_API_BASE"),
    api_version="2024-02-15-preview",
    tpm=80000,
    rpm=800,
    tags=["premium", "high-quality", "azure"]
)

# Anthropic target
anthropic_target = ModelTarget(
    model="claude-3-sonnet-20240229",
    provider="anthropic",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    tpm=150000,
    rpm=1000,
    tags=["premium", "high-quality"]
)
```

### RouteConfig

```python
from skye.router import RouteConfig, ModelTarget
from skye.router import RoutingStrategy

route = RouteConfig(
    alias="gpt-4",
    targets=[openai_target, azure_target],
    strategy=RoutingStrategy.RATE_LIMIT_AWARE,
    fallback_on_error=True
)
```

### FallbackConfig

```python
from skye.router import FallbackConfig

fallback = FallbackConfig(
    primary="gpt-4",
    fallbacks=["gpt-3.5-turbo", "claude-3-sonnet-20240229"]
)

router.set_fallbacks([fallback])
```

### RetryPolicyConfig

```python
from skye.router import RetryPolicyConfig

policies = [
    RetryPolicyConfig(error_type="RateLimitError", max_retries=3),
    RetryPolicyConfig(error_type="TimeoutError", max_retries=2),
    RetryPolicyConfig(error_type="ServerError", max_retries=2),
    RetryPolicyConfig(error_type="AuthenticationError", max_retries=0)
]

router.set_retry_policy(policies)
```

### AllowedFailsPolicyConfig

```python
from skye.router import AllowedFailsPolicyConfig

policies = [
    AllowedFailsPolicyConfig(
        error_type="RateLimitError",
        allowed_fails_per_minute=100
    ),
    AllowedFailsPolicyConfig(
        error_type="ServerError",
        allowed_fails_per_minute=5
    ),
    AllowedFailsPolicyConfig(
        error_type="TimeoutError",
        allowed_fails_per_minute=10
    )
]

router.set_allowed_fails_policy(policies)
```

## Metrics and Monitoring

All metrics are returned as Pydantic models:

### ModelHealthMetrics

```python
health = router.get_model_health("gpt-4")

print(f"Model: {health.model_id}")
print(f"Success rate: {health.success_rate:.1%}")
print(f"Average latency: {health.average_latency_ms:.0f}ms")
print(f"Total requests: {health.total_requests}")
print(f"Failures: {health.failure_count}")
print(f"In cooldown: {health.is_in_cooldown}")
print(f"Tags: {health.tags}")
```

### UsageStats

```python
stats = router.get_usage_stats("gpt-4")

print(f"TPM used: {stats.tpm_used}/{stats.tpm_limit}")
print(f"RPM used: {stats.rpm_used}/{stats.rpm_limit}")
print(f"Active requests: {stats.active_requests}")
print(f"Total requests: {stats.total_requests}")
print(f"Total failures: {stats.total_failures}")
```

### CooldownInfo

```python
cooled_down = router.get_cooldown_models()

for info in cooled_down:
    print(f"Model: {info.model_id}")
    print(f"Cooldown until: {info.cooldown_until}")
    print(f"Reason: {info.reason}")
```

## Routing Strategies

```python
from skye.router import RoutingStrategy

# Available strategies:
RoutingStrategy.ROUND_ROBIN        # Rotate through models
RoutingStrategy.SIMPLE_SHUFFLE     # Random selection
RoutingStrategy.LEAST_BUSY         # Fewest active requests
RoutingStrategy.RATE_LIMIT_AWARE   # Most available capacity
RoutingStrategy.LATENCY_BASED      # Lowest average latency
RoutingStrategy.COST_BASED         # Lowest cost
RoutingStrategy.WEIGHTED           # Weighted random (by target weight)
RoutingStrategy.PRIORITY_BASED     # Highest success rate

# Change strategy dynamically
router.set_routing_strategy(RoutingStrategy.LATENCY_BASED)
```

## Advanced Features

### Rate Limiting

```python
# Set rate limits
router.set_rate_limits("gpt-4", tpm=100000, rpm=1000)

# Enable/disable pre-call checks
router.enable_pre_call_checks(True)
```

### Cooldown Management

```python
# Set cooldown duration
router.set_cooldown_time(60.0)  # 60 seconds

# Manually mark model as failed
router.mark_model_failed("gpt-4")

# Check cooldown status
cooled_down = router.get_cooldown_models()
```

### Tag-Based Routing

```python
# Set tags on models
router.set_model_tags("gpt-4", ["premium", "high-quality"])

# Route to models with specific tags
response = router.route_with_tags(
    request,
    required_tags=["premium", "high-quality"]
)
```

### Alias Management

```python
# Check if name is an alias
if router.is_alias("gpt-3.5-turbo"):
    print("This is an alias")

# List all aliases
aliases = router.list_aliases()

# Get route configuration
route = router.get_route("gpt-3.5-turbo")
if route:
    print(f"Targets: {len(route.targets)}")
    print(f"Strategy: {route.strategy}")
```

## Constructor vs Methods

You can configure the router in two ways:

### 1. Constructor Configuration (Recommended)

Configure everything upfront for a clean, declarative setup:

```python
router = ModelRouter(
    routes=[...],
    strategy=RoutingStrategy.LEAST_BUSY,
    cooldown_seconds=60.0,
    fallbacks=[...],
    retry_policies=[...],
    allowed_fails_policies=[...],
)
```

### 2. Method Configuration

Configure after instantiation for dynamic setup:

```python
router = ModelRouter()
router.set_fallbacks([...])
router.set_retry_policy([...])
router.set_routing_strategy(RoutingStrategy.LATENCY_BASED)
```

### 3. Mixed Approach

Combine both for flexibility:

```python
router = ModelRouter(
    routes=[...],
    strategy=RoutingStrategy.ROUND_ROBIN,
)

# Add more configuration later
router.set_fallbacks([...])
router.set_routing_strategy(RoutingStrategy.LATENCY_BASED)
```

## Best Practices

1. **Use Constructor Configuration**: Configure everything upfront for clarity
2. **Use Pydantic Models**: All configurations use Pydantic for validation
3. **Set Rate Limits**: Prevent exceeding provider quotas
4. **Configure Fallbacks**: Ensure high availability
5. **Monitor Health**: Regularly check model health metrics
6. **Use Appropriate Strategy**: Choose strategy based on your needs
7. **Enable Pre-Call Checks**: Filter out rate-limited models early
8. **Set Cooldowns**: Prevent cascading failures
9. **Use Tags**: Organize models by capability or cost tier

## Complete Examples

- `examples/router_constructor_config.py` - Constructor-based configuration (recommended)
- `examples/advanced_routing.py` - Method-based configuration and all features
