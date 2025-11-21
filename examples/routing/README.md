# Routing Examples

This directory contains examples demonstrating how to use Nimbus routers for load balancing and failover.

## What is Routing?

Routing allows you to:
- Load balance across multiple model deployments
- Implement fallback chains for reliability
- Track model health and performance
- Enforce rate limits (TPM/RPM)
- Use different strategies (round-robin, least-busy, cost-based, etc.)

## Examples

### `basic_routing.py`
Basic router configuration with multiple targets.

**Topics covered:**
- Creating routers with multiple targets
- Round-robin load balancing
- Accessing routing metrics

### `yaml_config.py`
Loading router configuration from YAML files.

**Topics covered:**
- YAML configuration format
- Environment variable substitution
- Multi-provider setup

### `fallback_chains.py`
Implementing fallback chains for reliability.

**Topics covered:**
- Primary and fallback models
- Automatic failover
- Cooldown mechanisms

### `rate_limiting.py`
Enforcing rate limits (TPM/RPM).

**Topics covered:**
- Tokens per minute (TPM) limits
- Requests per minute (RPM) limits
- Rate limit tracking
- Pre-call rate limit checks

## Running the Examples

```bash
# Run basic routing example
python examples/routing/basic_routing.py

# Run YAML configuration example
python examples/routing/yaml_config.py

# Run fallback chains example
python examples/routing/fallback_chains.py

# Run rate limiting example
python examples/routing/rate_limiting.py
```

## Key Concepts

- **ModelRouter**: Main router class for load balancing
- **ModelTarget**: Individual model deployment configuration
- **RouteConfig**: Configuration for a route (alias + targets)
- **RoutingStrategy**: Strategy for selecting targets (round-robin, least-busy, etc.)
- **FallbackConfig**: Fallback chain configuration
- **RetryPolicyConfig**: Retry policy for specific error types
- **AllowedFailsPolicyConfig**: Allowed failures before cooldown

## Routing Strategies

- **ROUND_ROBIN**: Rotate through targets in order
- **SIMPLE_SHUFFLE**: Random selection
- **LEAST_BUSY**: Fewest active requests
- **RATE_LIMIT_AWARE**: Most available capacity
- **LATENCY_BASED**: Lowest average latency
- **COST_BASED**: Lowest cost
- **WEIGHTED**: Weighted random selection
- **PRIORITY_BASED**: Highest success rate

## YAML Configuration

Example YAML configuration:

```yaml
routes:
  - alias: "gpt-3.5-turbo"
    strategy: "rate_limit_aware"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 200000
        rpm: 2000
      - model: "gpt-35-turbo"
        provider: "azure"
        api_key: "${AZURE_API_KEY}"
        api_base: "${AZURE_API_BASE}"
        tpm: 100000
        rpm: 1000

fallbacks:
  - primary: "gpt-4"
    fallbacks: ["gpt-3.5-turbo"]

retry_policies:
  - error_type: "RateLimitError"
    max_retries: 3
```

## Environment Variable Substitution

Use `${VAR_NAME}` syntax in YAML or Python config:

```yaml
api_key: "${OPENAI_API_KEY}"
api_base: "${AZURE_API_BASE}"
```

```python
target = ModelTarget(
    model="gpt-4",
    provider="openai",
    api_key="${OPENAI_API_KEY}"  # Will be substituted
)
```

## Next Steps

After understanding routing, explore:
- `examples/providers/` - Provider-specific features
- `examples/capabilities/` - Using capabilities with routing
- `examples/advanced/` - Advanced routing patterns
