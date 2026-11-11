"""Unit tests for configuration models."""

import pytest

from skye.base.config import (
    CooldownConfig,
    ModelConfig,
    RateLimitConfig,
    RetryConfig,
    SkyeConfig,
)
from skye.base.exceptions import ValidationError


def test_rate_limit_config():
    """Test RateLimitConfig model."""
    # Test with all fields
    rate_limits = RateLimitConfig(
        requests_per_minute=60,
        tokens_per_minute=90000,
        requests_per_day=10000,
        tokens_per_day=2000000,
    )
    assert rate_limits.requests_per_minute == 60
    assert rate_limits.tokens_per_minute == 90000
    assert rate_limits.requests_per_day == 10000
    assert rate_limits.tokens_per_day == 2000000

    # Test with partial fields
    rate_limits_partial = RateLimitConfig(
        requests_per_minute=100,
        tokens_per_minute=150000,
    )
    assert rate_limits_partial.requests_per_minute == 100
    assert rate_limits_partial.tokens_per_minute == 150000
    assert rate_limits_partial.requests_per_day is None
    assert rate_limits_partial.tokens_per_day is None

    # Test with no fields (all defaults to None)
    rate_limits_empty = RateLimitConfig()
    assert rate_limits_empty.requests_per_minute is None
    assert rate_limits_empty.tokens_per_minute is None
    assert rate_limits_empty.requests_per_day is None
    assert rate_limits_empty.tokens_per_day is None


def test_retry_config():
    """Test RetryConfig model."""
    # Test with default values
    retry_config = RetryConfig()
    assert retry_config.max_retries == 3
    assert retry_config.retry_after_seconds == 5
    assert retry_config.exponential_backoff is True
    assert retry_config.retry_on_errors == ["rate_limit", "timeout", "server_error"]

    # Test with custom values
    retry_config_custom = RetryConfig(
        max_retries=5,
        retry_after_seconds=10,
        exponential_backoff=False,
        retry_on_errors=["rate_limit", "timeout"],
    )
    assert retry_config_custom.max_retries == 5
    assert retry_config_custom.retry_after_seconds == 10
    assert retry_config_custom.exponential_backoff is False
    assert retry_config_custom.retry_on_errors == ["rate_limit", "timeout"]

    # Test with empty retry_on_errors
    retry_config_no_errors = RetryConfig(retry_on_errors=[])
    assert retry_config_no_errors.retry_on_errors == []


def test_cooldown_config():
    """Test CooldownConfig model."""
    # Test with default values
    cooldown_config = CooldownConfig()
    assert cooldown_config.enabled is True
    assert cooldown_config.allowed_fails_per_minute == 3
    assert cooldown_config.cooldown_duration_seconds == 60

    # Test with custom values
    cooldown_config_custom = CooldownConfig(
        enabled=False,
        allowed_fails_per_minute=5,
        cooldown_duration_seconds=120,
    )
    assert cooldown_config_custom.enabled is False
    assert cooldown_config_custom.allowed_fails_per_minute == 5
    assert cooldown_config_custom.cooldown_duration_seconds == 120

    # Test cooldown disabled
    cooldown_config_disabled = CooldownConfig(enabled=False)
    assert cooldown_config_disabled.enabled is False
    assert cooldown_config_disabled.allowed_fails_per_minute == 3  # Still has default
    assert cooldown_config_disabled.cooldown_duration_seconds == 60


def test_model_config():
    """Test ModelConfig model."""
    # Test basic model config
    model_config = ModelConfig(
        model_id="gpt-4",
        provider="openai",
    )
    assert model_config.model_id == "gpt-4"
    assert model_config.provider == "openai"
    assert model_config.api_key is None
    assert model_config.api_base is None
    assert model_config.temperature == 0.7
    assert model_config.max_tokens is None
    assert model_config.timeout == 60

    # Test with all basic fields
    model_config_full = ModelConfig(
        model_id="claude-3-sonnet",
        provider="anthropic",
        api_key="sk-test-key",
        api_base="https://api.anthropic.com",
        temperature=0.5,
        max_tokens=2000,
        timeout=30,
    )
    assert model_config_full.model_id == "claude-3-sonnet"
    assert model_config_full.provider == "anthropic"
    assert model_config_full.api_key == "sk-test-key"
    assert model_config_full.api_base == "https://api.anthropic.com"
    assert model_config_full.temperature == 0.5
    assert model_config_full.max_tokens == 2000
    assert model_config_full.timeout == 30

    # Test with nested configs
    model_config_nested = ModelConfig(
        model_id="gpt-4",
        provider="openai",
        rate_limits=RateLimitConfig(
            requests_per_minute=60,
            tokens_per_minute=90000,
        ),
        retry_config=RetryConfig(max_retries=5),
        cooldown_config=CooldownConfig(enabled=False),
    )
    assert model_config_nested.rate_limits is not None
    assert model_config_nested.rate_limits.requests_per_minute == 60
    assert model_config_nested.retry_config.max_retries == 5
    assert model_config_nested.cooldown_config.enabled is False

    # Test default nested configs
    assert isinstance(model_config.retry_config, RetryConfig)
    assert isinstance(model_config.cooldown_config, CooldownConfig)
    assert model_config.retry_config.max_retries == 3
    assert model_config.cooldown_config.enabled is True

    # Test fallback models
    model_config_fallback = ModelConfig(
        model_id="gpt-4",
        provider="openai",
        fallback_models=["gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
    )
    assert model_config_fallback.fallback_models == [
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]

    # Test routing fields
    model_config_routing = ModelConfig(
        model_id="gpt-4",
        provider="openai",
        weight=2.0,
        priority=10,
        tags=["production", "high-quality"],
    )
    assert model_config_routing.weight == 2.0
    assert model_config_routing.priority == 10
    assert model_config_routing.tags == ["production", "high-quality"]

    # Test cost tracking
    model_config_cost = ModelConfig(
        model_id="gpt-4",
        provider="openai",
        cost_per_1k_prompt_tokens=0.03,
        cost_per_1k_completion_tokens=0.06,
    )
    assert model_config_cost.cost_per_1k_prompt_tokens == 0.03
    assert model_config_cost.cost_per_1k_completion_tokens == 0.06


def test_skye_config():
    """Test SkyeConfig model: only the keys that code reads (D106)."""
    # Test with default values
    skye_config = SkyeConfig()
    assert skye_config.log_level == "INFO"
    assert skye_config.correlation_id_header == "X-Correlation-ID"
    assert skye_config.component_log_levels == {}

    # Test with custom values
    skye_config_custom = SkyeConfig(
        log_level="DEBUG",
        correlation_id_header="X-Request-ID",
        component_log_levels={"router": "warning"},
    )
    assert skye_config_custom.log_level == "DEBUG"
    assert skye_config_custom.correlation_id_header == "X-Request-ID"
    assert skye_config_custom.level_for("router") == "WARNING"
    assert skye_config_custom.level_for("models") == "DEBUG"


def test_model_config_validation():
    """Test ModelConfig validation."""
    # Test that model_id and provider are required
    with pytest.raises(ValidationError):
        ModelConfig()  # Missing required fields

    with pytest.raises(ValidationError):
        ModelConfig(model_id="gpt-4")  # Missing provider

    with pytest.raises(ValidationError):
        ModelConfig(provider="openai")  # Missing model_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
