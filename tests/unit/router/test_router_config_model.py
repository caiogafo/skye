"""Unit tests for YAML router configuration loading.

Tests the load_router_config function and RouterConfig model to ensure
proper loading, validation, and environment variable substitution.
"""

import os
import tempfile
from pathlib import Path

import pytest

from skye.base.config import RouterConfig
from skye.base.exceptions import ConfigurationError


class TestRouterConfig:
    """Tests for RouterConfig Pydantic model."""

    def test_router_config_defaults(self):
        """Test RouterConfig with default values."""
        config = RouterConfig()

        assert config.routes == []
        assert config.fallbacks == []
        assert config.retry_policies == []
        assert config.allowed_fails_policies == []
        assert config.strategy == "round_robin"
        assert config.cooldown_seconds == 60.0
        assert config.enable_pre_call_checks is True

    def test_router_config_with_routes(self):
        """Test RouterConfig with route configurations."""
        config = RouterConfig(
            routes=[
                {
                    "alias": "gpt-3.5-turbo",
                    "targets": [
                        {
                            "model": "gpt-3.5-turbo",
                            "provider": "openai",
                            "api_key": "sk-test",
                            "tpm": 200000,
                            "rpm": 2000,
                        }
                    ],
                    "strategy": "rate_limit_aware",
                }
            ]
        )

        assert len(config.routes) == 1
        assert config.routes[0]["alias"] == "gpt-3.5-turbo"
        assert len(config.routes[0]["targets"]) == 1

    def test_router_config_with_fallbacks(self):
        """Test RouterConfig with fallback configurations."""
        config = RouterConfig(
            fallbacks=[{"primary": "gpt-4", "fallbacks": ["gpt-3.5-turbo", "claude-3-sonnet"]}]
        )

        assert len(config.fallbacks) == 1
        assert config.fallbacks[0]["primary"] == "gpt-4"
        assert len(config.fallbacks[0]["fallbacks"]) == 2

    def test_router_config_with_retry_policies(self):
        """Test RouterConfig with retry policy configurations."""
        config = RouterConfig(
            retry_policies=[
                {"error_type": "RateLimitError", "max_retries": 3},
                {"error_type": "TimeoutError", "max_retries": 2},
            ]
        )

        assert len(config.retry_policies) == 2
        assert config.retry_policies[0]["error_type"] == "RateLimitError"
        assert config.retry_policies[0]["max_retries"] == 3

    def test_router_config_with_allowed_fails_policies(self):
        """Test RouterConfig with allowed fails policy configurations."""
        config = RouterConfig(
            allowed_fails_policies=[
                {"error_type": "RateLimitError", "allowed_fails_per_minute": 100}
            ]
        )

        assert len(config.allowed_fails_policies) == 1
        assert config.allowed_fails_policies[0]["error_type"] == "RateLimitError"
        assert config.allowed_fails_policies[0]["allowed_fails_per_minute"] == 100

    def test_router_config_validation_negative_cooldown(self):
        """Test that negative cooldown_seconds is rejected."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            RouterConfig(cooldown_seconds=-10.0)
