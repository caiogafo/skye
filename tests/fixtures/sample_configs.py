"""Sample router configuration fixtures for testing.

This module provides reusable ``.skye`` router texts and configuration dictionaries for testing router loading and validation.
The library reads no YAML (decision D62): a router file is a ``.skye`` ``router`` block or a JSON object.
"""

# Basic router configuration with single route
BASIC_ROUTER_CONFIG_SKYE = """
router "main" {
  route "gpt-3.5-turbo" {
    strategy = "round_robin"
    target { model = "gpt-3.5-turbo", provider = "openai", api_key = "test-key-123", tpm = 100000, rpm = 1000 }
  }
}
"""

# Router configuration with environment variables
ENV_VAR_ROUTER_CONFIG_SKYE = """
router "main" {
  route "gpt-4" {
    strategy = "rate_limit_aware"
    target { model = "gpt-4", provider = "openai", api_key = env.OPENAI_API_KEY, tpm = 200000, rpm = 2000 }
  }
}
"""

# Multi-provider router configuration with a fallback chain and policies
MULTI_PROVIDER_ROUTER_CONFIG_SKYE = """
router "main" {
  route "gpt-4" {
    target { model = "gpt-4", provider = "openai", api_key = "test-key-gpt4" }
  }
  route "gpt-3.5-turbo" {
    strategy = "rate_limit_aware"
    fallback = ["gpt-4"]
    target { model = "azure/chatgpt-v-2", provider = "azure", api_key = env.AZURE_API_KEY, api_base = env.AZURE_API_BASE, tpm = 100000, rpm = 1000 }
    target { model = "gpt-3.5-turbo", provider = "openai", api_key = env.OPENAI_API_KEY, tpm = 200000, rpm = 2000 }
  }
  retry_policy "RateLimitError" { max_retries = 3 }
  allowed_fails_policy "RateLimitError" { allowed_fails_per_minute = 100 }
}
"""

# Router configuration with fallback chains
FALLBACK_ROUTER_CONFIG_SKYE = """
router "main" {
  route "gpt-4" {
    strategy = "round_robin"
    fallback = ["gpt-3.5-turbo"]
    target { model = "gpt-4", provider = "openai", api_key = "test-key-gpt4", tpm = 150000, rpm = 1500 }
  }
  route "gpt-3.5-turbo" {
    strategy = "round_robin"
    target { model = "gpt-3.5-turbo", provider = "openai", api_key = "test-key-gpt35", tpm = 200000, rpm = 2000 }
  }
}
"""

# Invalid router configuration (missing required fields: the target has no provider)
INVALID_ROUTER_CONFIG_SKYE = """
router "main" {
  route "gpt-4" {
    target { model = "gpt-4", api_key = "test-key" }
  }
}
"""

# Router configuration with several strategies
ALL_STRATEGIES_ROUTER_CONFIG_SKYE = """
router "main" {
  route "round-robin-route" {
    strategy = "round_robin"
    target { model = "gpt-3.5-turbo", provider = "openai", api_key = "test-key-1" }
  }
  route "least-busy-route" {
    strategy = "least_busy"
    target { model = "gpt-4", provider = "openai", api_key = "test-key-2" }
  }
  route "rate-limit-route" {
    strategy = "rate_limit_aware"
    target { model = "claude-3", provider = "anthropic", api_key = "test-key-3", tpm = 100000, rpm = 1000 }
  }
}
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
