"""Unit tests for environment variable substitution in configuration."""

import os
from pathlib import Path

import pytest

from nimbus.base.config import ConfigLoader, substitute_env_vars
from nimbus.base.exceptions import ConfigurationError


class TestSubstituteEnvVars:
    """Test suite for substitute_env_vars function."""

    def setup_method(self):
        """Clear the environment variable cache before each test."""
        from nimbus.base.config import _env_var_cache
        _env_var_cache.clear()

    def test_substitute_simple_string(self, monkeypatch):
        """Test successful substitution in a simple string."""
        monkeypatch.setenv("TEST_VAR", "test_value")

        result = substitute_env_vars("${TEST_VAR}")
        assert result == "test_value"

    def test_substitute_string_with_text(self, monkeypatch):
        """Test substitution in string with surrounding text."""
        monkeypatch.setenv("API_KEY", "secret-123")

        result = substitute_env_vars("Bearer ${API_KEY}")
        assert result == "Bearer secret-123"

    def test_substitute_multiple_vars_in_string(self, monkeypatch):
        """Test substitution of multiple variables in one string."""
        monkeypatch.setenv("HOST", "localhost")
        monkeypatch.setenv("PORT", "8080")

        result = substitute_env_vars("http://${HOST}:${PORT}/api")
        assert result == "http://localhost:8080/api"

    def test_substitute_in_dict(self, monkeypatch):
        """Test substitution in dictionary values."""
        monkeypatch.setenv("API_KEY", "secret-key")
        monkeypatch.setenv("API_BASE", "https://api.example.com")

        config = {
            "api_key": "${API_KEY}",
            "api_base": "${API_BASE}",
            "timeout": 30,
        }

        result = substitute_env_vars(config)
        assert result["api_key"] == "secret-key"
        assert result["api_base"] == "https://api.example.com"
        assert result["timeout"] == 30

    def test_substitute_in_nested_dict(self, monkeypatch):
        """Test substitution in nested dictionary structures."""
        monkeypatch.setenv("OPENAI_KEY", "openai-secret")
        monkeypatch.setenv("AZURE_KEY", "azure-secret")

        config = {
            "models": {
                "gpt-4": {
                    "provider": "openai",
                    "api_key": "${OPENAI_KEY}",
                },
                "azure-gpt": {
                    "provider": "azure",
                    "api_key": "${AZURE_KEY}",
                },
            }
        }

        result = substitute_env_vars(config)
        assert result["models"]["gpt-4"]["api_key"] == "openai-secret"
        assert result["models"]["azure-gpt"]["api_key"] == "azure-secret"

    def test_substitute_in_list(self, monkeypatch):
        """Test substitution in list items."""
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.setenv("VAR2", "value2")

        config = ["${VAR1}", "${VAR2}", "static_value"]

        result = substitute_env_vars(config)
        assert result == ["value1", "value2", "static_value"]

    def test_substitute_in_nested_list(self, monkeypatch):
        """Test substitution in nested list structures."""
        monkeypatch.setenv("KEY1", "secret1")
        monkeypatch.setenv("KEY2", "secret2")

        config = {
            "keys": ["${KEY1}", "${KEY2}"],
            "nested": [{"key": "${KEY1}"}, {"key": "${KEY2}"}],
        }

        result = substitute_env_vars(config)
        assert result["keys"] == ["secret1", "secret2"]
        assert result["nested"][0]["key"] == "secret1"
        assert result["nested"][1]["key"] == "secret2"

    def test_missing_env_var_raises_error(self):
        """Test that missing environment variable raises ConfigurationError."""
        config = {"api_key": "${NONEXISTENT_VAR}"}

        with pytest.raises(ConfigurationError) as exc_info:
            substitute_env_vars(config)

        assert "Environment variable '${NONEXISTENT_VAR}' not found" in str(exc_info.value)
        assert exc_info.value.details["variable_name"] == "NONEXISTENT_VAR"

    def test_missing_env_var_in_nested_structure(self):
        """Test error handling for missing variable in nested structure."""
        config = {
            "models": {
                "gpt-4": {
                    "api_key": "${MISSING_KEY}",
                }
            }
        }

        with pytest.raises(ConfigurationError) as exc_info:
            substitute_env_vars(config)

        assert "MISSING_KEY" in str(exc_info.value)

    def test_empty_string_value(self, monkeypatch):
        """Test substitution with empty string environment variable."""
        monkeypatch.setenv("EMPTY_VAR", "")

        result = substitute_env_vars("${EMPTY_VAR}")
        assert result == ""

    def test_special_characters_in_value(self, monkeypatch):
        """Test substitution with special characters in value."""
        monkeypatch.setenv("SPECIAL_VAR", "value!@#$%^&*()_+-={}[]|:;<>?,./")

        result = substitute_env_vars("${SPECIAL_VAR}")
        assert result == "value!@#$%^&*()_+-={}[]|:;<>?,./"

    def test_numeric_value(self, monkeypatch):
        """Test that numeric values are preserved as-is."""
        config = {"timeout": 30, "max_retries": 3}

        result = substitute_env_vars(config)
        assert result["timeout"] == 30
        assert result["max_retries"] == 3

    def test_boolean_value(self):
        """Test that boolean values are preserved as-is."""
        config = {"enabled": True, "disabled": False}

        result = substitute_env_vars(config)
        assert result["enabled"] is True
        assert result["disabled"] is False

    def test_none_value(self):
        """Test that None values are preserved as-is."""
        config = {"optional_field": None}

        result = substitute_env_vars(config)
        assert result["optional_field"] is None

    def test_no_substitution_needed(self):
        """Test that strings without ${} patterns are unchanged."""
        config = {
            "static_key": "static_value",
            "number": 42,
            "nested": {"key": "value"},
        }

        result = substitute_env_vars(config)
        assert result == config

    def test_partial_match_not_substituted(self, monkeypatch):
        """Test that partial ${} patterns are not substituted."""
        monkeypatch.setenv("VAR", "value")

        # Missing closing brace
        result = substitute_env_vars("${VAR")
        assert result == "${VAR"

        # Missing opening brace
        result = substitute_env_vars("VAR}")
        assert result == "VAR}"

    def test_invalid_var_name_not_substituted(self):
        """Test that invalid variable names are not substituted."""
        # Variable names must start with letter or underscore
        result = substitute_env_vars("${123VAR}")
        assert result == "${123VAR}"

        # Variable names cannot contain hyphens
        result = substitute_env_vars("${VAR-NAME}")
        assert result == "${VAR-NAME}"

    def test_caching_behavior(self, monkeypatch):
        """Test that environment variable values are cached."""
        # Import the cache to verify it's being used
        from nimbus.base.config import _env_var_cache

        # Clear cache before test
        _env_var_cache.clear()

        monkeypatch.setenv("CACHED_VAR", "cached_value")

        # First substitution should cache the value
        result1 = substitute_env_vars("${CACHED_VAR}")
        assert result1 == "cached_value"
        assert "CACHED_VAR" in _env_var_cache
        assert _env_var_cache["CACHED_VAR"] == "cached_value"

        # Change the environment variable
        monkeypatch.setenv("CACHED_VAR", "new_value")

        # Second substitution should use cached value
        result2 = substitute_env_vars("${CACHED_VAR}")
        assert result2 == "cached_value"  # Still uses cached value

    def test_multiple_substitutions_use_cache(self, monkeypatch):
        """Test that multiple substitutions of same variable use cache."""
        from nimbus.base.config import _env_var_cache

        _env_var_cache.clear()

        monkeypatch.setenv("SHARED_VAR", "shared_value")

        config = {
            "key1": "${SHARED_VAR}",
            "key2": "${SHARED_VAR}",
            "nested": {"key3": "${SHARED_VAR}"},
        }

        result = substitute_env_vars(config)
        assert result["key1"] == "shared_value"
        assert result["key2"] == "shared_value"
        assert result["nested"]["key3"] == "shared_value"

        # Variable should be cached
        assert "SHARED_VAR" in _env_var_cache


class TestConfigLoaderWithEnvVarSubstitution:
    """Test ConfigLoader integration with environment variable substitution."""

    def setup_method(self):
        """Clear the environment variable cache before each test."""
        from nimbus.base.config import _env_var_cache
        _env_var_cache.clear()

    def test_yaml_config_with_env_vars(self, monkeypatch, tmp_path):
        """Test loading YAML configuration with environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("AZURE_API_BASE", "https://azure.openai.com")

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
log_level: INFO
models:
  gpt-4:
    model_id: gpt-4
    provider: openai
    api_key: ${OPENAI_API_KEY}
  azure-gpt:
    model_id: azure-gpt
    provider: azure
    api_key: ${OPENAI_API_KEY}
    api_base: ${AZURE_API_BASE}
"""
        )

        config = ConfigLoader.load(config_path=config_file)

        assert config.models["gpt-4"].api_key == "sk-test-key-123"
        assert config.models["azure-gpt"].api_key == "sk-test-key-123"
        assert config.models["azure-gpt"].api_base == "https://azure.openai.com"

    def test_json_config_with_env_vars(self, monkeypatch, tmp_path):
        """Test loading JSON configuration with environment variables."""
        monkeypatch.setenv("API_KEY", "secret-key")

        config_file = tmp_path / "config.json"
        config_file.write_text(
            """
{
  "log_level": "INFO",
  "models": {
    "test-model": {
      "model_id": "test",
      "provider": "test-provider",
      "api_key": "${API_KEY}"
    }
  }
}
"""
        )

        config = ConfigLoader.load(config_path=config_file)

        assert config.models["test-model"].api_key == "secret-key"

    def test_code_overrides_with_env_vars(self, monkeypatch):
        """Test code overrides with environment variable substitution."""
        monkeypatch.setenv("OVERRIDE_KEY", "override-value")

        overrides = {
            "log_level": "DEBUG",
            "models": {
                "test": {
                    "model_id": "test",
                    "provider": "test-provider",
                    "api_key": "${OVERRIDE_KEY}",
                }
            },
        }

        config = ConfigLoader.load(overrides=overrides)

        assert config.models["test"].api_key == "override-value"

    def test_missing_env_var_in_yaml_raises_error(self, tmp_path):
        """Test that missing environment variable in YAML raises error."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
log_level: INFO
models:
  test:
    model_id: test
    provider: test-provider
    api_key: ${MISSING_VAR}
"""
        )

        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load(config_path=config_file)

        assert "MISSING_VAR" in str(exc_info.value)

    def test_mixed_env_vars_and_static_values(self, monkeypatch, tmp_path):
        """Test configuration with mix of env vars and static values."""
        monkeypatch.setenv("DYNAMIC_KEY", "dynamic-value")

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
log_level: INFO
models:
  model1:
    model_id: model1
    provider: provider1
    api_key: ${DYNAMIC_KEY}
    timeout: 30
  model2:
    model_id: model2
    provider: provider2
    api_key: static-key
    timeout: 60
"""
        )

        config = ConfigLoader.load(config_path=config_file)

        assert config.models["model1"].api_key == "dynamic-value"
        assert config.models["model1"].timeout == 30
        assert config.models["model2"].api_key == "static-key"
        assert config.models["model2"].timeout == 60

    def test_env_var_in_nested_plugin_config(self, monkeypatch, tmp_path):
        """Test environment variable substitution in nested plugin configuration."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
        monkeypatch.setenv("OBSERVE_ENDPOINT", "http://localhost:4318")

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
log_level: INFO
plugins:
  memory:
    type: redis
    url: ${REDIS_URL}
  observe:
    type: otlp
    endpoint: ${OBSERVE_ENDPOINT}
"""
        )

        config = ConfigLoader.load(config_path=config_file)

        assert config.plugins["memory"]["url"] == "redis://localhost:6379"
        assert config.plugins["observe"]["endpoint"] == "http://localhost:4318"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
