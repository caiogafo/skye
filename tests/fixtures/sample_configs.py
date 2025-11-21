"""Sample YAML configuration fixtures for testing.

This module provides reusable YAML configuration strings and dictionaries
for testing router configuration loading and validation.
"""

# Basic router configuration with single route
BASIC_ROUTER_CONFIG_YAML = """
routes:
  - alias: "gpt-3.5-turbo"
    strategy: "round_robin"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "test-key-123"
        tpm: 100000
        rpm: 1000
"""

# Router configuration with environment variables
ENV_VAR_ROUTER_CONFIG_YAML = """
routes:
  - alias: "gpt-4"
    strategy: "rate_limit_aware"
    targets:
      - model: "gpt-4"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 200000
        rpm: 2000
"""

# Multi-provider router configuration
MULTI_PROVIDER_ROUTER_CONFIG_YAML = """
routes:
  - alias: "gpt-3.5-turbo"
    strategy: "rate_limit_aware"
    targets:
      - model: "azure/chatgpt-v-2"
        provider: "azure"
        api_key: "${AZURE_API_KEY}"
        api_base: "${AZURE_API_BASE}"
        tpm: 100000
        rpm: 1000
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 200000
        rpm: 2000

fallbacks:
  - primary: "gpt-4"
    fallbacks: ["gpt-3.5-turbo"]

retry_policies:
  - error_type: "RateLimitError"
    max_retries: 3

allowed_fails_policies:
  - error_type: "RateLimitError"
    allowed_fails_per_minute: 100
"""

# Router configuration with fallback chains
FALLBACK_ROUTER_CONFIG_YAML = """
routes:
  - alias: "gpt-4"
    strategy: "round_robin"
    targets:
      - model: "gpt-4"
        provider: "openai"
        api_key: "test-key-gpt4"
        tpm: 150000
        rpm: 1500
  
  - alias: "gpt-3.5-turbo"
    strategy: "round_robin"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "test-key-gpt35"
        tpm: 200000
        rpm: 2000

fallbacks:
  - primary: "gpt-4"
    fallbacks: ["gpt-3.5-turbo"]
"""

# Invalid router configuration (missing required fields)
INVALID_ROUTER_CONFIG_YAML = """
routes:
  - alias: "gpt-4"
    targets:
      - model: "gpt-4"
        # Missing provider field
        api_key: "test-key"
"""

# Router configuration with all strategies
ALL_STRATEGIES_ROUTER_CONFIG_YAML = """
routes:
  - alias: "round-robin-route"
    strategy: "round_robin"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "test-key-1"
  
  - alias: "least-busy-route"
    strategy: "least_busy"
    targets:
      - model: "gpt-4"
        provider: "openai"
        api_key: "test-key-2"
  
  - alias: "rate-limit-route"
    strategy: "rate_limit_aware"
    targets:
      - model: "claude-3"
        provider: "anthropic"
        api_key: "test-key-3"
        tpm: 100000
        rpm: 1000
"""

# Configuration dictionary equivalents for programmatic testing
BASIC_ROUTER_CONFIG_DICT = {
    "routes": [
        {
            "alias": "gpt-3.5-turbo",
            "strategy": "round_robin",
            "targets": [
                {
                    "model": "gpt-3.5-turbo",
                    "provider": "openai",
                    "api_key": "test-key-123",
                    "tpm": 100000,
                    "rpm": 1000,
                }
            ],
        }
    ]
}

MULTI_PROVIDER_ROUTER_CONFIG_DICT = {
    "routes": [
        {
            "alias": "gpt-3.5-turbo",
            "strategy": "rate_limit_aware",
            "targets": [
                {
                    "model": "azure/chatgpt-v-2",
                    "provider": "azure",
                    "api_key": "${AZURE_API_KEY}",
                    "api_base": "${AZURE_API_BASE}",
                    "tpm": 100000,
                    "rpm": 1000,
                },
                {
                    "model": "gpt-3.5-turbo",
                    "provider": "openai",
                    "api_key": "${OPENAI_API_KEY}",
                    "tpm": 200000,
                    "rpm": 2000,
                },
            ],
        }
    ],
    "fallbacks": [{"primary": "gpt-4", "fallbacks": ["gpt-3.5-turbo"]}],
    "retry_policies": [{"error_type": "RateLimitError", "max_retries": 3}],
    "allowed_fails_policies": [
        {"error_type": "RateLimitError", "allowed_fails_per_minute": 100}
    ],
}

# Sample model target configurations
SAMPLE_OPENAI_TARGET = {
    "model": "gpt-4",
    "provider": "openai",
    "api_key": "${OPENAI_API_KEY}",
    "tpm": 200000,
    "rpm": 2000,
}

SAMPLE_AZURE_TARGET = {
    "model": "azure/chatgpt-v-2",
    "provider": "azure",
    "api_key": "${AZURE_API_KEY}",
    "api_base": "${AZURE_API_BASE}",
    "tpm": 100000,
    "rpm": 1000,
}

SAMPLE_ANTHROPIC_TARGET = {
    "model": "claude-3-opus",
    "provider": "anthropic",
    "api_key": "${ANTHROPIC_API_KEY}",
    "tpm": 150000,
    "rpm": 1500,
}

SAMPLE_BEDROCK_TARGET = {
    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "provider": "bedrock",
    "region": "us-east-1",
    "tpm": 100000,
    "rpm": 1000,
}
