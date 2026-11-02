"""YAML Configuration for Skye Routers.

This example demonstrates how to configure ModelRouter using YAML files with:
- Environment variable substitution for secure credential management
- Multiple routing strategies (round-robin, rate-limit-aware, least-busy, etc.)
- Fallback chains for automatic failover
- Rate limiting and retry policies
- Multi-provider and multi-region deployments

YAML configuration provides a declarative way to manage complex routing setups
without hardcoding credentials or deployment details in your code.
"""

import os
from pathlib import Path

from skye.base.messages import UserMessage
from skye.router import ModelRouter


def basic_yaml_config():
    """Load router from basic YAML configuration."""
    print("=" * 70)
    print("1. Basic YAML Configuration")
    print("=" * 70)
    
    # Load router from YAML file
    # The YAML file contains routes, fallbacks, and retry policies
    # Use simple config if OPENAI_API_KEY is set, otherwise show error
    config_path = Path(__file__).parent / "router_config_simple.yaml"
    
    if not os.getenv("OPENAI_API_KEY"):
        print(f"\n⚠️  OPENAI_API_KEY not set. Skipping router loading.")
        print(f"   Set OPENAI_API_KEY to load router from: {config_path}")
        print(f"\n   Example: export OPENAI_API_KEY='sk-...'")
        return
    
    print(f"\nLoading router from: {config_path}")
    
    try:
        router = ModelRouter.from_yaml(config_path)
    except Exception as e:
        print(f"\n❌ Error loading router: {e}")
        return
    
    # Display loaded configuration
    print(f"\n✓ Router loaded successfully!")
    print(f"  Registered aliases: {router.list_aliases()}")
    print(f"  Default strategy: {router.strategy.value}")
    print(f"  Cooldown duration: {router.cooldown_seconds}s")
    
    # Show route details
    for alias in router.list_aliases():
        route = router.get_route(alias)
        if route:
            print(f"\n  Route '{alias}':")
            print(f"    Strategy: {route.strategy.value}")
            print(f"    Targets: {len(route.targets)}")
            for i, target in enumerate(route.targets, 1):
                print(f"      {i}. {target.provider}/{target.model}")
                if target.tpm:
                    print(f"         TPM: {target.tpm:,}, RPM: {target.rpm:,}")


def environment_variable_substitution():
    """Demonstrate environment variable substitution in YAML."""
    print("\n" + "=" * 70)
    print("2. Environment Variable Substitution")
    print("=" * 70)
    
    print("""
Environment variables provide secure credential management:
- API keys are never hardcoded in configuration files
- Different credentials can be used per environment (dev/staging/prod)
- Credentials can be managed by secret management systems

YAML Syntax: ${VARIABLE_NAME}

Example YAML:
  api_key: "${OPENAI_API_KEY}"
  api_base: "${AZURE_API_BASE}"
  region: "${AWS_REGION}"
""")
    
    # Check which environment variables are set
    env_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "AWS_PROFILE",
        "AWS_ACCESS_KEY_ID",
    ]
    
    print("Environment variables status:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"  ✓ {var}: {masked}")
        else:
            print(f"  - {var}: not set")
    
    print("""
To set environment variables:
  export OPENAI_API_KEY="sk-..."
  export ANTHROPIC_API_KEY="sk-ant-..."
  export AZURE_OPENAI_API_KEY="..."
""")


def multiple_routing_strategies():
    """Demonstrate different routing strategies via YAML."""
    print("\n" + "=" * 70)
    print("3. Multiple Routing Strategies")
    print("=" * 70)
    
    print("""
Skye supports multiple routing strategies, each optimized for different goals:

1. ROUND_ROBIN
   - Distributes requests evenly across all targets
   - Simple and predictable load distribution
   - Good for: Homogeneous deployments with similar capacity

2. RATE_LIMIT_AWARE
   - Routes to target with most available capacity (TPM/RPM)
   - Prevents rate limit errors by checking limits before routing
   - Good for: Maximizing throughput, avoiding rate limits

3. LEAST_BUSY
   - Routes to target with fewest active requests
   - Balances load based on current utilization
   - Good for: Varying request durations, real-time load balancing

4. LATENCY_BASED
   - Routes to target with lowest average latency
   - Optimizes for response time
   - Good for: Latency-sensitive applications

5. COST_BASED
   - Routes to target with lowest cost per token
   - Optimizes for cost efficiency
   - Good for: Budget-conscious deployments

6. WEIGHTED
   - Routes based on assigned weights (higher weight = more traffic)
   - Allows fine-grained traffic distribution
   - Good for: Gradual rollouts, A/B testing

7. PRIORITY_BASED
   - Routes to highest priority target first
   - Falls back to lower priority on failure
   - Good for: Primary/secondary deployments

8. SIMPLE_SHUFFLE
   - Random selection from available targets
   - Simple and unpredictable distribution
   - Good for: Testing, development
""")
    
    # Create example YAML configs for each strategy
    strategies_yaml = """
# Example: Different strategies for different routes

routes:
  # Fast models with round-robin
  - alias: "fast"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
    strategy: "round_robin"
  
  # Production models with rate-limit awareness
  - alias: "production"
    targets:
      - model: "gpt-4"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 100000
        rpm: 1000
    strategy: "rate_limit_aware"
  
  # Multi-region with latency optimization
  - alias: "global"
    targets:
      - model: "gpt-4"
        provider: "azure"
        api_key: "${AZURE_API_KEY_EAST}"
        region: "us-east-1"
      - model: "gpt-4"
        provider: "azure"
        api_key: "${AZURE_API_KEY_WEST}"
        region: "us-west-2"
    strategy: "latency_based"
  
  # Cost-optimized deployment
  - alias: "budget"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        cost_per_1k_prompt_tokens: 0.0005
        cost_per_1k_completion_tokens: 0.0015
    strategy: "cost_based"
"""
    
    print("\nExample YAML configuration:")
    print(strategies_yaml)


def advanced_yaml_features():
    """Demonstrate advanced YAML configuration features."""
    print("\n" + "=" * 70)
    print("4. Advanced YAML Features")
    print("=" * 70)
    
    print("""
Advanced features available in YAML configuration:

A. FALLBACK CHAINS
   Automatically try alternative models when primary fails:
   
   fallbacks:
     - primary: "gpt-4"
       fallbacks: ["gpt-3.5-turbo", "claude-3-sonnet"]
   
   Benefits:
   - Automatic failover on errors
   - Improved reliability
   - No code changes needed

B. RETRY POLICIES
   Configure retry behavior per error type:
   
   retry_policies:
     - error_type: "RateLimitError"
       max_retries: 3
     - error_type: "TimeoutError"
       max_retries: 2
   
   Benefits:
   - Automatic retry on transient errors
   - Configurable per error type
   - Exponential backoff support

C. COOLDOWN POLICIES
   Temporarily disable failing models:
   
   allowed_fails_policies:
     - error_type: "RateLimitError"
       allowed_fails_per_minute: 100
   
   cooldown_seconds: 60.0
   
   Benefits:
   - Prevents cascading failures
   - Allows time for recovery
   - Automatic re-enablement

D. RATE LIMITING
   Enforce TPM/RPM limits per target:
   
   targets:
     - model: "gpt-4"
       provider: "openai"
       tpm: 100000  # Tokens per minute
       rpm: 1000    # Requests per minute
   
   enable_pre_call_checks: true
   
   Benefits:
   - Prevents rate limit errors
   - Maximizes throughput
   - Respects provider quotas

E. METADATA AND TAGS
   Add custom metadata for filtering and routing:
   
   targets:
     - model: "gpt-4"
       provider: "openai"
       tags: ["premium", "high-quality"]
       metadata:
         deployment: "production"
         region: "us-east-1"
   
   Benefits:
   - Tag-based routing
   - Custom filtering
   - Deployment tracking
""")


def multi_provider_example():
    """Demonstrate multi-provider configuration."""
    print("\n" + "=" * 70)
    print("5. Multi-Provider Configuration")
    print("=" * 70)
    
    multi_provider_yaml = """
# Multi-provider router configuration
# Supports OpenAI, Anthropic, AWS Bedrock, Azure, and more

routes:
  # OpenAI GPT-4
  - alias: "gpt-4"
    targets:
      - model: "gpt-4"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 100000
        rpm: 1000
    strategy: "rate_limit_aware"
  
  # Anthropic Claude
  - alias: "claude"
    targets:
      - model: "claude-3-sonnet-20240229"
        provider: "anthropic"
        api_key: "${ANTHROPIC_API_KEY}"
        tpm: 80000
        rpm: 800
    strategy: "rate_limit_aware"
  
  # AWS Bedrock (multi-region)
  - alias: "bedrock-claude"
    targets:
      - model: "anthropic.claude-3-sonnet-20240229-v1:0"
        provider: "bedrock"
        region: "us-east-1"
      - model: "anthropic.claude-3-sonnet-20240229-v1:0"
        provider: "bedrock"
        region: "us-west-2"
    strategy: "latency_based"
  
  # Azure OpenAI (multi-region)
  - alias: "azure-gpt4"
    targets:
      - model: "gpt-4"
        provider: "azure"
        api_key: "${AZURE_OPENAI_API_KEY_EAST}"
        api_base: "${AZURE_API_BASE_EAST}"
        api_version: "2024-02-15-preview"
        region: "eastus"
      - model: "gpt-4"
        provider: "azure"
        api_key: "${AZURE_OPENAI_API_KEY_WEST}"
        api_base: "${AZURE_API_BASE_WEST}"
        api_version: "2024-02-15-preview"
        region: "westus"
    strategy: "least_busy"

# Cross-provider fallbacks
fallbacks:
  - primary: "gpt-4"
    fallbacks: ["azure-gpt4", "claude"]
  - primary: "claude"
    fallbacks: ["bedrock-claude", "gpt-4"]

# Global settings
strategy: "rate_limit_aware"
cooldown_seconds: 60.0
enable_pre_call_checks: true
"""
    
    print("\nMulti-provider YAML configuration:")
    print(multi_provider_yaml)
    
    print("""
Benefits of multi-provider setup:
- Avoid vendor lock-in
- Leverage best model for each task
- Automatic cross-provider failover
- Geographic redundancy
- Cost optimization across providers
""")


def programmatic_overrides():
    """Demonstrate programmatic overrides of YAML config."""
    print("\n" + "=" * 70)
    print("6. Programmatic Overrides")
    print("=" * 70)
    
    print("""
You can override YAML configuration programmatically:
""")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY not set. Skipping this example.")
        print("""
Example code:
    router = ModelRouter.from_yaml(
        "router_config.yaml",
        cooldown_seconds=120.0,  # Override cooldown
        enable_pre_call_checks=False,  # Disable pre-call checks
    )
""")
        return
    
    config_path = Path(__file__).parent / "router_config_simple.yaml"
    
    try:
        # Load with overrides
        router = ModelRouter.from_yaml(
            config_path,
            cooldown_seconds=120.0,  # Override cooldown
            enable_pre_call_checks=False,  # Disable pre-call checks
        )
        
        print(f"\nLoaded router with overrides:")
        print(f"  Cooldown: {router.cooldown_seconds}s (overridden from YAML)")
        print(f"  Pre-call checks: {router.enable_pre_call_checks} (overridden from YAML)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("""
This allows:
- Environment-specific overrides (dev/staging/prod)
- Runtime configuration changes
- A/B testing different settings
- Gradual rollout of new configurations
""")


def making_requests():
    """Demonstrate making requests with YAML-configured router."""
    print("\n" + "=" * 70)
    print("7. Making Requests with YAML Router")
    print("=" * 70)
    
    # Check if we have API keys
    has_openai = os.getenv("OPENAI_API_KEY")
    
    if not has_openai:
        print("""
⚠️  No API keys configured. Set environment variables to run this example:
  
  export OPENAI_API_KEY="sk-..."
  
Then run this example again.
""")
        return
    
    # Load router from YAML
    config_path = Path(__file__).parent / "router_config_simple.yaml"
    
    try:
        router = ModelRouter.from_yaml(config_path)
    except Exception as e:
        print(f"\n❌ Error loading router: {e}")
        return
    
    print("\nMaking completion request using YAML-configured router...")
    
    try:
        # Make a request using the alias from YAML
        response = router.complete(
            messages=[UserMessage(content="What is 2+2? Answer briefly.")],
            model="gpt-3.5-turbo",  # Alias from YAML
            max_tokens=50
        )
        
        print(f"\n✓ Request successful!")
        print(f"  Response: {response.content}")
        print(f"  Tokens used: {response.usage.total_tokens}")
        print(f"  Model: {response.model}")
        
        # Show routing metrics
        print(f"\n  Router metrics:")
        for alias in router.list_aliases():
            route = router.get_route(alias)
            if route:
                print(f"    {alias}: {len(route.targets)} target(s)")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"   Make sure your API key is valid and has sufficient quota")


def best_practices():
    """Display best practices for YAML configuration."""
    print("\n" + "=" * 70)
    print("8. Best Practices")
    print("=" * 70)
    
    print("""
YAML Configuration Best Practices:

1. SECURITY
   ✓ Always use environment variables for API keys
   ✓ Never commit API keys to version control
   ✓ Use .env files for local development
   ✓ Use secret management systems in production
   
   # .gitignore
   .env
   *_secrets.yaml
   
2. ORGANIZATION
   ✓ Use descriptive alias names
   ✓ Group related routes together
   ✓ Add comments explaining complex configurations
   ✓ Keep YAML files under version control (without secrets)
   
3. RATE LIMITING
   ✓ Always set TPM/RPM limits for production
   ✓ Enable pre-call checks to prevent rate limit errors
   ✓ Configure appropriate cooldown periods
   ✓ Monitor rate limit usage
   
4. FALLBACKS
   ✓ Configure fallback chains for critical routes
   ✓ Test fallback behavior regularly
   ✓ Use cross-provider fallbacks for redundancy
   ✓ Monitor fallback activation rates
   
5. STRATEGIES
   ✓ Use rate_limit_aware for high-throughput scenarios
   ✓ Use latency_based for latency-sensitive applications
   ✓ Use cost_based for budget-conscious deployments
   ✓ Test different strategies to find optimal configuration
   
6. MONITORING
   ✓ Track success rates per target
   ✓ Monitor latency distributions
   ✓ Alert on high error rates
   ✓ Review cooldown activations
   
7. TESTING
   ✓ Test YAML configuration in staging first
   ✓ Validate environment variable substitution
   ✓ Test fallback chains
   ✓ Load test with production-like traffic
   
8. DOCUMENTATION
   ✓ Document routing strategies and rationale
   ✓ Explain fallback chains
   ✓ Document required environment variables
   ✓ Keep configuration examples up to date
""")


def main():
    """Run all YAML configuration examples."""
    print("\n" + "🔧 " * 25)
    print("SKYE - YAML Configuration Examples")
    print("🔧 " * 25)
    
    try:
        basic_yaml_config()
        environment_variable_substitution()
        multiple_routing_strategies()
        advanced_yaml_features()
        multi_provider_example()
        programmatic_overrides()
        making_requests()
        best_practices()
        
        print("\n" + "=" * 70)
        print("✅ All examples completed!")
        print("=" * 70)
        
        print("""
Next Steps:
1. Create your own router_config.yaml
2. Set required environment variables
3. Load router with ModelRouter.from_yaml()
4. Make requests using configured aliases

For more information:
- See examples/routing/router_config.yaml for full configuration
- See examples/routing/README.md for routing documentation
- See .kiro/steering/00-rules.md for architecture details
""")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
