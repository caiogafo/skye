"""Unit tests for YAML router configuration loading.

Tests the load_router_config function and RouterConfig model to ensure
proper loading, validation, and environment variable substitution.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from nimbus.config import RouterConfig, load_router_config
from nimbus.exceptions import ConfigurationError


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


class TestLoadRouterConfig:
    """Tests for load_router_config function."""

    def test_load_valid_yaml_config(self):
        """Test loading a valid YAML configuration."""
        yaml_content = """
routes:
  - alias: "gpt-3.5-turbo"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "sk-test-key"
        tpm: 200000
        rpm: 2000
    strategy: "rate_limit_aware"

fallbacks:
  - primary: "gpt-4"
    fallbacks: ["gpt-3.5-turbo"]

retry_policies:
  - error_type: "RateLimitError"
    max_retries: 3

strategy: "round_robin"
cooldown_seconds: 60.0
enable_pre_call_checks: true
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = load_router_config(temp_path)

            assert isinstance(config, dict)
            assert len(config["routes"]) == 1
            assert config["routes"][0]["alias"] == "gpt-3.5-turbo"
            assert len(config["fallbacks"]) == 1
            assert len(config["retry_policies"]) == 1
            assert config["strategy"] == "round_robin"
            assert config["cooldown_seconds"] == 60.0
            assert config["enable_pre_call_checks"] is True
        finally:
            os.unlink(temp_path)

    def test_load_config_with_env_var_substitution(self):
        """Test environment variable substitution in YAML config."""
        # Set test environment variables
        os.environ["TEST_OPENAI_KEY"] = "sk-real-key-123"
        os.environ["TEST_AZURE_BASE"] = "https://test.openai.azure.com"

        yaml_content = """
routes:
  - alias: "gpt-3.5-turbo"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "${TEST_OPENAI_KEY}"
        tpm: 200000
      - model: "azure/chatgpt-v-2"
        provider: "azure"
        api_key: "${TEST_OPENAI_KEY}"
        api_base: "${TEST_AZURE_BASE}"
        tpm: 100000
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = load_router_config(temp_path)

            # Check that environment variables were substituted
            assert config["routes"][0]["targets"][0]["api_key"] == "sk-real-key-123"
            assert config["routes"][0]["targets"][1]["api_key"] == "sk-real-key-123"
            assert config["routes"][0]["targets"][1]["api_base"] == "https://test.openai.azure.com"
        finally:
            os.unlink(temp_path)
            # Clean up environment variables
            del os.environ["TEST_OPENAI_KEY"]
            del os.environ["TEST_AZURE_BASE"]

    def test_load_config_missing_env_var(self):
        """Test that missing environment variable raises ConfigurationError."""
        yaml_content = """
routes:
  - alias: "gpt-3.5-turbo"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "${NONEXISTENT_ENV_VAR}"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_router_config(temp_path)

            assert "NONEXISTENT_ENV_VAR" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_load_config_file_not_found(self):
        """Test that missing file raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_router_config("/nonexistent/path/config.yaml")

        assert "not found" in str(exc_info.value).lower()

    def test_load_config_invalid_yaml_syntax(self):
        """Test that invalid YAML syntax raises ConfigurationError."""
        yaml_content = """
routes:
  - alias: "gpt-3.5-turbo"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "sk-test"
      invalid yaml syntax here: [
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_router_config(temp_path)

            assert "parse" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_load_config_empty_file(self):
        """Test that empty YAML file raises ConfigurationError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_router_config(temp_path)

            assert "empty" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_load_config_non_dict_root(self):
        """Test that non-dictionary root raises ConfigurationError."""
        yaml_content = """
- item1
- item2
- item3
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_router_config(temp_path)

            assert "dictionary" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_load_config_validation_failure(self):
        """Test that invalid configuration values raise ConfigurationError."""
        yaml_content = """
routes:
  - alias: "gpt-3.5-turbo"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "sk-test"

cooldown_seconds: -10.0
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_router_config(temp_path)

            assert "validation" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_load_config_with_path_object(self):
        """Test loading config with Path object instead of string."""
        yaml_content = """
routes:
  - alias: "gpt-3.5-turbo"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "sk-test"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = load_router_config(temp_path)

            assert isinstance(config, dict)
            assert len(config["routes"]) == 1
        finally:
            temp_path.unlink()

    def test_load_config_minimal_valid(self):
        """Test loading minimal valid configuration."""
        yaml_content = """
routes: []
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = load_router_config(temp_path)

            assert isinstance(config, dict)
            assert config["routes"] == []
            # Check defaults are applied
            assert config["strategy"] == "round_robin"
            assert config["cooldown_seconds"] == 60.0
            assert config["enable_pre_call_checks"] is True
        finally:
            os.unlink(temp_path)

    def test_load_config_complex_nested_structure(self):
        """Test loading complex configuration with nested structures."""
        yaml_content = """
routes:
  - alias: "gpt-4"
    targets:
      - model: "gpt-4"
        provider: "openai"
        api_key: "sk-test-1"
        tpm: 100000
        rpm: 1000
        tags: ["premium", "paid"]
        metadata:
          team: "engineering"
          cost_center: "ai-research"
      - model: "azure/gpt-4"
        provider: "azure"
        api_key: "sk-test-2"
        api_base: "https://test.openai.azure.com"
        api_version: "2024-02-15-preview"
        tpm: 80000
        rpm: 800
        tags: ["premium", "azure"]
    strategy: "rate_limit_aware"
    fallback_on_error: true

  - alias: "gpt-3.5-turbo"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "sk-test-3"
        tpm: 200000
        rpm: 2000
    strategy: "round_robin"

fallbacks:
  - primary: "gpt-4"
    fallbacks: ["gpt-3.5-turbo"]

retry_policies:
  - error_type: "RateLimitError"
    max_retries: 3
  - error_type: "TimeoutError"
    max_retries: 2

allowed_fails_policies:
  - error_type: "RateLimitError"
    allowed_fails_per_minute: 100

strategy: "least_busy"
cooldown_seconds: 120.0
enable_pre_call_checks: false
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = load_router_config(temp_path)

            # Verify routes
            assert len(config["routes"]) == 2
            assert config["routes"][0]["alias"] == "gpt-4"
            assert len(config["routes"][0]["targets"]) == 2
            assert config["routes"][0]["targets"][0]["tags"] == ["premium", "paid"]
            assert config["routes"][0]["targets"][0]["metadata"]["team"] == "engineering"

            # Verify fallbacks
            assert len(config["fallbacks"]) == 1
            assert config["fallbacks"][0]["primary"] == "gpt-4"

            # Verify policies
            assert len(config["retry_policies"]) == 2
            assert len(config["allowed_fails_policies"]) == 1

            # Verify top-level settings
            assert config["strategy"] == "least_busy"
            assert config["cooldown_seconds"] == 120.0
            assert config["enable_pre_call_checks"] is False
        finally:
            os.unlink(temp_path)
