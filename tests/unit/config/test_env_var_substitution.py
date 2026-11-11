"""Unit tests for environment variable substitution in configuration."""


import json

import pytest

from skye.base.config import ConfigLoader, substitute_env_vars
from skye.base.exceptions import ConfigurationError
from skye.utils.config_files import load_config


class TestSubstituteEnvVars:
    """Test suite for substitute_env_vars function."""

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

    def test_a_changed_variable_is_read_again(self, monkeypatch):
        """The environment is read at every substitution: no value is kept between calls (decision D66)."""
        monkeypatch.setenv("CHANGING_VAR", "first")
        assert substitute_env_vars("${CHANGING_VAR}") == "first"
        monkeypatch.setenv("CHANGING_VAR", "second")
        assert substitute_env_vars("${CHANGING_VAR}") == "second"
        monkeypatch.delenv("CHANGING_VAR")
        with pytest.raises(ConfigurationError, match="CHANGING_VAR"):
            substitute_env_vars("${CHANGING_VAR}")

    def test_the_same_variable_in_several_places(self, monkeypatch):
        """One variable may appear in several keys and nested levels."""
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


class TestConfigLoaderWithEnvVarSubstitution:
    """Test ConfigLoader integration with environment variable substitution."""

    def test_json_config_with_several_env_vars(self, monkeypatch, tmp_path):
        """Test loading a JSON configuration file with several environment variables."""
        monkeypatch.setenv("APP_LOG_LEVEL", "WARNING")
        monkeypatch.setenv("APP_HEADER", "X-Trace-ID")

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "log_level": "${APP_LOG_LEVEL}",
            "correlation_id_header": "${APP_HEADER}",
        }))

        config = load_config(config_file)

        assert config.log_level == "WARNING"
        assert config.correlation_id_header == "X-Trace-ID"

    def test_json_config_with_env_vars(self, monkeypatch, tmp_path):
        """Test loading JSON configuration with environment variables in a nested value."""
        monkeypatch.setenv("ROUTER_LEVEL", "DEBUG")

        config_file = tmp_path / "config.json"
        config_file.write_text(
            """
{
  "log_level": "INFO",
  "component_log_levels": {"router": "${ROUTER_LEVEL}"}
}
"""
        )

        config = load_config(config_file)

        assert config.component_log_levels["router"] == "DEBUG"

    def test_code_overrides_with_env_vars(self, monkeypatch):
        """Test code overrides with environment variable substitution."""
        monkeypatch.setenv("OVERRIDE_HEADER", "X-Override")

        config = ConfigLoader.load(overrides={"correlation_id_header": "${OVERRIDE_HEADER}"})

        assert config.correlation_id_header == "X-Override"

    def test_missing_env_var_in_file_raises_error(self, tmp_path):
        """Test that missing environment variable in a file raises error."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"log_level": "INFO", "correlation_id_header": "${MISSING_VAR}"}))

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(config_file)

        assert "MISSING_VAR" in str(exc_info.value)

    def test_mixed_env_vars_and_static_values(self, monkeypatch, tmp_path):
        """Test configuration with mix of env vars and static values."""
        monkeypatch.setenv("DYNAMIC_LEVEL", "ERROR")

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "log_level": "INFO",
            "component_log_levels": {"router": "${DYNAMIC_LEVEL}", "models": "DEBUG"},
        }))

        config = load_config(config_file)

        assert config.level_for("router") == "ERROR"
        assert config.level_for("models") == "DEBUG"
        assert config.log_level == "INFO"

    def test_substitution_happens_at_each_load(self, monkeypatch, tmp_path):
        """Nothing is cached (D66): a variable changed between two loads is seen by the second."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"correlation_id_header": "${HEADER}"}))

        monkeypatch.setenv("HEADER", "X-One")
        assert load_config(config_file).correlation_id_header == "X-One"
        monkeypatch.setenv("HEADER", "X-Two")
        assert load_config(config_file).correlation_id_header == "X-Two"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
