"""Unit tests for ConfigLoader."""

from pathlib import Path

import pytest

from skye.base.config import ConfigLoader, ModelConfig, SkyeConfig
from skye.base.exceptions import ConfigurationError


def test_config_loader_from_yaml():
    """Test loading configuration from YAML file."""
    config_path = Path("tests/fixtures/sample_config.yaml")
    config = ConfigLoader.load(config_path=config_path)

    assert isinstance(config, SkyeConfig)
    assert config.log_level == "INFO"
    assert config.enable_telemetry is True
    assert config.correlation_id_header == "X-Correlation-ID"
    assert config.default_routing_strategy == "round_robin"
    assert config.enable_fallbacks is True
    assert config.enable_rate_limiting is True

    # Check models
    assert "gpt-4" in config.models
    assert "claude-3" in config.models
    assert config.models["gpt-4"].model_id == "gpt-4"
    assert config.models["gpt-4"].provider == "openai"
    assert config.models["gpt-4"].temperature == 0.7
    assert config.models["gpt-4"].max_tokens == 2000
    assert config.models["gpt-4"].fallback_models == ["gpt-3.5-turbo"]
    assert config.models["gpt-4"].cost_per_1k_prompt_tokens == 0.03
    assert config.models["gpt-4"].cost_per_1k_completion_tokens == 0.06

    # Check rate limits
    assert config.models["gpt-4"].rate_limits is not None
    assert config.models["gpt-4"].rate_limits.requests_per_minute == 60
    assert config.models["gpt-4"].rate_limits.tokens_per_minute == 90000

    # Check plugins
    assert "memory" in config.plugins
    assert "observe" in config.plugins
    assert config.plugins["memory"]["type"] == "redis"
    assert config.plugins["observe"]["endpoint"] == "http://localhost:4318"


def test_config_loader_from_json():
    """Test loading configuration from JSON file."""
    config_path = Path("tests/fixtures/sample_config.json")
    config = ConfigLoader.load(config_path=config_path)

    assert isinstance(config, SkyeConfig)
    assert config.log_level == "DEBUG"
    assert config.enable_telemetry is False
    assert config.correlation_id_header == "X-Request-ID"
    assert config.default_routing_strategy == "least_busy"
    assert config.enable_fallbacks is False
    assert config.enable_rate_limiting is False

    # Check models
    assert "gpt-3.5" in config.models
    assert config.models["gpt-3.5"].model_id == "gpt-3.5-turbo"
    assert config.models["gpt-3.5"].provider == "openai"
    assert config.models["gpt-3.5"].temperature == 0.8
    assert config.models["gpt-3.5"].max_tokens == 1000
    assert config.models["gpt-3.5"].timeout == 30

    # Check plugins
    assert "guard" in config.plugins
    assert config.plugins["guard"]["type"] == "content_filter"
    assert config.plugins["guard"]["enabled"] is True


def test_config_loader_from_env(monkeypatch):
    """Test loading configuration from environment variables."""
    # Set environment variables
    monkeypatch.setenv("SKYE_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("SKYE_ENABLE_TELEMETRY", "false")

    config = ConfigLoader.load()

    assert config.log_level == "WARNING"
    assert config.enable_telemetry is False


def test_only_three_skye_prefixed_env_vars(monkeypatch):
    """Requirement 23: exactly SKYE_LOG_LEVEL, SKYE_CONFIG, SKYE_ENABLE_TELEMETRY are read."""
    from skye.base.config import ALL_ENV_VARS

    assert ALL_ENV_VARS == {"SKYE_LOG_LEVEL", "SKYE_CONFIG", "SKYE_ENABLE_TELEMETRY"}
    monkeypatch.setenv("SKYE_ENABLE_FALLBACKS", "false")
    monkeypatch.setenv("SKYE_OPENAI_API_KEY", "sk-ignored")
    config = ConfigLoader.load()
    assert config.enable_fallbacks is True  # default: the variable is not a config source
    assert "openai_api_key" not in ConfigLoader._load_from_env()


def test_skye_config_env_names_the_config_file(monkeypatch):
    monkeypatch.setenv("SKYE_CONFIG", "tests/fixtures/sample_config.yaml")
    assert ConfigLoader.load().log_level == ConfigLoader.load(
        config_path=Path("tests/fixtures/sample_config.yaml")
    ).log_level


def test_config_loader_from_code_overrides():
    """Test loading configuration with code overrides."""
    overrides = {
        "log_level": "ERROR",
        "enable_telemetry": False,
        "default_routing_strategy": "lowest_cost",
        "models": {
            "test-model": ModelConfig(
                model_id="test-model",
                provider="test-provider",
                temperature=0.9,
            )
        },
    }

    config = ConfigLoader.load(overrides=overrides)

    assert config.log_level == "ERROR"
    assert config.enable_telemetry is False
    assert config.default_routing_strategy == "lowest_cost"
    assert "test-model" in config.models
    assert config.models["test-model"].model_id == "test-model"
    assert config.models["test-model"].provider == "test-provider"
    assert config.models["test-model"].temperature == 0.9


def test_config_loader_precedence(monkeypatch):
    """Test configuration precedence: code > env > file."""
    # 1. Load from file (lowest precedence)
    config_path = Path("tests/fixtures/sample_config.yaml")

    # 2. Set environment variables (medium precedence)
    monkeypatch.setenv("SKYE_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("SKYE_ENABLE_TELEMETRY", "false")

    # 3. Set code overrides (highest precedence)
    overrides = {
        "log_level": "CRITICAL",
    }

    config = ConfigLoader.load(config_path=config_path, overrides=overrides)

    # Code override should win for log_level
    assert config.log_level == "CRITICAL"

    # Environment variable should win for enable_telemetry (no code override)
    assert config.enable_telemetry is False

    # File value should be used for correlation_id_header (no env or code override)
    assert config.correlation_id_header == "X-Correlation-ID"

    # File value should be used for models (no env or code override)
    assert "gpt-4" in config.models


def test_config_loader_no_sources():
    """Test loading configuration with no sources (all defaults)."""
    config = ConfigLoader.load()

    assert isinstance(config, SkyeConfig)
    assert config.log_level == "INFO"
    assert config.enable_telemetry is True
    assert config.correlation_id_header == "X-Correlation-ID"
    assert config.models == {}
    assert config.plugins == {}


def test_config_loader_nonexistent_file():
    """Test loading from nonexistent file raises ConfigurationError."""
    config_path = Path("tests/fixtures/nonexistent.yaml")

    with pytest.raises(ConfigurationError) as exc_info:
        ConfigLoader.load(config_path=config_path)

    assert "Configuration file not found" in str(exc_info.value)
    assert "nonexistent.yaml" in str(exc_info.value)


def test_config_loader_invalid_file_format():
    """Test loading from unsupported file format raises ConfigurationError."""
    # Create a temporary file with unsupported extension
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write("log_level: INFO")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load(config_path=temp_path)

        assert "Unsupported configuration file format" in str(exc_info.value)
        assert ".txt" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_config_loader_invalid_yaml():
    """Test loading invalid YAML raises ConfigurationError."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
        f.write("log_level: INFO\n  invalid: indentation\n")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load(config_path=temp_path)

        assert "Failed to parse configuration file" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_config_loader_invalid_json():
    """Test loading invalid JSON raises ConfigurationError."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        f.write('{"log_level": "INFO",}')  # Trailing comma is invalid JSON
        temp_path = Path(f.name)

    try:
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load(config_path=temp_path)

        assert "Failed to parse configuration file" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_config_loader_empty_file():
    """Test loading empty configuration file."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
        f.write("")
        temp_path = Path(f.name)

    try:
        config = ConfigLoader.load(config_path=temp_path)
        # Should load with all defaults
        assert config.log_level == "INFO"
        assert config.enable_telemetry is True
    finally:
        temp_path.unlink()


def test_config_loader_non_dict_root():
    """Test loading file with non-dict root raises ConfigurationError."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
        f.write("- item1\n- item2\n")  # List at root level
        temp_path = Path(f.name)

    try:
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load(config_path=temp_path)

        assert "must contain a dictionary/object at root level" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_config_loader_env_type_conversion(monkeypatch):
    """Test environment variable type conversion."""
    # Test boolean conversion
    monkeypatch.setenv("SKYE_ENABLE_TELEMETRY", "true")

    config = ConfigLoader.load()

    assert config.enable_telemetry is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


def test_config_validation_invalid_log_level():
    """Test that invalid configuration values raise ConfigurationError."""
    # Note: Pydantic doesn't validate log_level as an enum by default,
    # but we can test other validation scenarios
    overrides = {
        "models": {
            "invalid-model": {
                "model_id": "test",
                # Missing required 'provider' field
            }
        }
    }

    with pytest.raises(ConfigurationError) as exc_info:
        ConfigLoader.load(overrides=overrides)

    assert "Configuration validation failed" in str(exc_info.value)
    assert "validation_errors" in exc_info.value.details


def test_config_validation_invalid_model_config():
    """Test that invalid ModelConfig raises ConfigurationError."""
    overrides = {
        "models": {
            "test-model": {
                # Missing both model_id and provider (required fields)
                "temperature": 0.7,
            }
        }
    }

    with pytest.raises(ConfigurationError) as exc_info:
        ConfigLoader.load(overrides=overrides)

    assert "Configuration validation failed" in str(exc_info.value)
    error_details = exc_info.value.details
    assert "validation_errors" in error_details
    # Check that validation errors are included
    assert len(error_details["validation_errors"]) > 0


def test_config_validation_invalid_nested_config():
    """Test that invalid nested configuration raises ConfigurationError."""
    overrides = {
        "models": {
            "test-model": {
                "model_id": "test",
                "provider": "test-provider",
                "rate_limits": {
                    # Invalid: requests_per_minute should be int, not string
                    "requests_per_minute": "not-a-number",
                },
            }
        }
    }

    with pytest.raises(ConfigurationError) as exc_info:
        ConfigLoader.load(overrides=overrides)

    assert "Configuration validation failed" in str(exc_info.value)


def test_config_validation_with_proper_context():
    """Test that ConfigurationError includes proper context."""
    overrides = {
        "models": {
            "invalid": {
                "model_id": "test",
                # Missing provider
            }
        }
    }

    with pytest.raises(ConfigurationError) as exc_info:
        ConfigLoader.load(overrides=overrides)

    error = exc_info.value
    assert error.message == "Configuration validation failed"
    assert "validation_errors" in error.details
    assert isinstance(error.details["validation_errors"], list)

    # Verify that the error includes field information
    validation_errors = error.details["validation_errors"]
    assert len(validation_errors) > 0
    # Each validation error should have type, loc, msg, and input fields
    for err in validation_errors:
        assert "type" in err
        assert "loc" in err
        assert "msg" in err


def test_config_validation_file_with_invalid_data():
    """Test that loading a file with invalid data raises ConfigurationError."""
    import tempfile

    # Create a YAML file with invalid model configuration
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
        f.write(
            """
log_level: INFO
models:
  invalid-model:
    model_id: test
    # Missing required 'provider' field
    temperature: 0.7
"""
        )
        temp_path = Path(f.name)

    try:
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load(config_path=temp_path)

        assert "Configuration validation failed" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_config_validation_env_with_invalid_data(monkeypatch):
    """Test that environment variables with invalid data raise ConfigurationError."""
    # Set up a scenario where we have a valid file but invalid env override
    config_path = Path("tests/fixtures/sample_config.yaml")

    # This won't actually cause validation error because Pydantic will accept
    # string values for most fields, but we can test the validation mechanism
    # by using the overrides parameter with invalid data
    overrides = {
        "models": {
            "test": {
                "model_id": "test",
                # Missing provider
            }
        }
    }

    with pytest.raises(ConfigurationError) as exc_info:
        ConfigLoader.load(config_path=config_path, overrides=overrides)

    assert "Configuration validation failed" in str(exc_info.value)
