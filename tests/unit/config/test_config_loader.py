"""Unit tests for ConfigLoader."""

from pathlib import Path

import pytest

from skye.base.config import ConfigLoader, SkyeConfig
from skye.base.exceptions import ConfigurationError
from skye.utils.config_files import load_config


def test_config_loader_from_full_json():
    """Load a configuration with every key from a JSON file."""
    config = load_config(Path("tests/fixtures/sample_config_full.json"))

    assert isinstance(config, SkyeConfig)
    assert config.log_level == "INFO"
    assert config.correlation_id_header == "X-Correlation-ID"
    assert config.component_log_levels == {"router": "DEBUG", "models": "WARNING"}
    assert config.level_for("router") == "DEBUG"
    assert config.level_for("tools") == "INFO"


def test_config_loader_from_json():
    """Test loading configuration from JSON file."""
    config = load_config(Path("tests/fixtures/sample_config.json"))

    assert isinstance(config, SkyeConfig)
    assert config.log_level == "DEBUG"
    assert config.correlation_id_header == "X-Request-ID"
    assert config.component_log_levels == {"router": "WARNING"}


def test_config_loader_from_env(monkeypatch):
    """Test loading configuration from environment variables."""
    monkeypatch.setenv("SKYE_LOG_LEVEL", "WARNING")

    config = ConfigLoader.load()

    assert config.log_level == "WARNING"


def test_only_two_skye_prefixed_env_vars(monkeypatch):
    """Exactly SKYE_LOG_LEVEL and SKYE_CONFIG are read (the telemetry variable left with its key, D106)."""
    from skye.base.config import ALL_ENV_VARS

    assert ALL_ENV_VARS == {"SKYE_LOG_LEVEL", "SKYE_CONFIG"}
    monkeypatch.setenv("SKYE_ENABLE_TELEMETRY", "false")
    monkeypatch.setenv("SKYE_ENABLE_FALLBACKS", "false")
    monkeypatch.setenv("SKYE_OPENAI_API_KEY", "sk-ignored")
    assert ConfigLoader._load_from_env() == {}
    assert ConfigLoader.load() == SkyeConfig()  # the variables are not config sources

def test_skye_config_env_names_the_config_file(monkeypatch):
    """``SKYE_CONFIG`` names the file that ``load_config`` opens (D91)."""
    monkeypatch.setenv("SKYE_CONFIG", "tests/fixtures/sample_config_full.json")
    assert load_config().log_level == load_config(
        Path("tests/fixtures/sample_config_full.json")
    ).log_level


def test_config_loader_opens_no_file_when_skye_config_is_set(monkeypatch):
    """``base`` opens no file (D91): with ``SKYE_CONFIG`` set, the loader names ``load_config``."""
    monkeypatch.setenv("SKYE_CONFIG", "tests/fixtures/sample_config_full.json")
    with pytest.raises(ConfigurationError, match="skye.load_config"):
        ConfigLoader.load()


def test_config_loader_takes_text_not_a_path():
    """A path given to the text loader is a mistake with a clear message (D91)."""
    with pytest.raises(ConfigurationError, match="not a path"):
        ConfigLoader.load(Path("skye.json"))  # type: ignore[arg-type]


def test_config_loader_from_text_and_from_dict():
    """The text and the dictionary give the same configuration; code overrides win."""
    from_text = ConfigLoader.from_text('{"log_level": "DEBUG"}', source="skye.json")
    from_dict = ConfigLoader.from_dict({"log_level": "DEBUG"})
    assert from_text.log_level == from_dict.log_level == "DEBUG"
    assert ConfigLoader.load('{"log_level": "DEBUG"}', {"log_level": "ERROR"}).log_level == "ERROR"
    assert ConfigLoader.from_text("").log_level == "INFO"



def test_config_loader_from_code_overrides():
    """Test loading configuration with code overrides."""
    overrides = {
        "log_level": "ERROR",
        "correlation_id_header": "X-Trace",
        "component_log_levels": {"models": "DEBUG"},
    }

    config = ConfigLoader.load(overrides=overrides)

    assert config.log_level == "ERROR"
    assert config.correlation_id_header == "X-Trace"
    assert config.level_for("models") == "DEBUG"


def test_config_loader_precedence(monkeypatch):
    """Test configuration precedence: code > env > file."""
    config_path = Path("tests/fixtures/sample_config.json")  # log_level DEBUG in the file
    monkeypatch.setenv("SKYE_LOG_LEVEL", "WARNING")

    # The environment wins over the file.
    assert load_config(config_path).log_level == "WARNING"

    config = load_config(config_path, overrides={"log_level": "CRITICAL"})
    # Code override should win for log_level
    assert config.log_level == "CRITICAL"
    # File value should be used where neither the environment nor the code sets one
    assert config.correlation_id_header == "X-Request-ID"
    assert config.component_log_levels == {"router": "WARNING"}


def test_config_loader_no_sources():
    """Test loading configuration with no sources (all defaults)."""
    config = ConfigLoader.load()

    assert isinstance(config, SkyeConfig)
    assert config.log_level == "INFO"
    assert config.correlation_id_header == "X-Correlation-ID"
    assert config.component_log_levels == {}

def test_config_loader_nonexistent_file():
    """Test loading from nonexistent file raises ConfigurationError."""
    config_path = Path("tests/fixtures/nonexistent.json")

    with pytest.raises(ConfigurationError) as exc_info:
        load_config(config_path)

    assert "Configuration file not found" in str(exc_info.value)
    assert "nonexistent.json" in str(exc_info.value)


def test_config_loader_invalid_file_format():
    """Test loading from unsupported file format raises ConfigurationError."""
    # Create a temporary file with unsupported extension
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write("log_level: INFO")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(temp_path)

        assert "Unsupported configuration file format" in str(exc_info.value)
        assert ".txt" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_config_loader_rejects_yaml(tmp_path):
    """The library reads no YAML (D62): the error names the supported formats instead of a parse failure."""
    path = tmp_path / "skye.yaml"
    path.write_text("log_level: INFO\n", encoding="utf-8")
    with pytest.raises(ConfigurationError) as exc_info:
        load_config(path)
    message = str(exc_info.value)
    assert "YAML is not read" in message and ".skye" in message and "JSON" in message


def test_config_loader_invalid_json():
    """Test loading invalid JSON raises ConfigurationError."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        f.write('{"log_level": "INFO",}')  # Trailing comma is invalid JSON
        temp_path = Path(f.name)

    try:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(temp_path)

        assert "Failed to parse configuration file" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_config_loader_empty_file():
    """Test loading an empty configuration object."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        f.write("{}")
        temp_path = Path(f.name)

    try:
        config = load_config(temp_path)
        # Should load with all defaults
        assert config.log_level == "INFO"
        assert config.component_log_levels == {}
    finally:
        temp_path.unlink()


def test_config_loader_non_dict_root():
    """Test loading file with non-dict root raises ConfigurationError."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        f.write('["item1", "item2"]')  # List at root level
        temp_path = Path(f.name)

    try:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(temp_path)

        assert "must contain a dictionary/object at root level" in str(exc_info.value)
    finally:
        temp_path.unlink()



def test_config_loader_env_type_conversion(monkeypatch):
    """A value of the environment that reads as a number or a boolean is converted, then validated."""
    monkeypatch.setenv("SKYE_LOG_LEVEL", "debug")
    assert ConfigLoader.load().level_for("router") == "DEBUG"


def test_config_validation_invalid_component_log_level():
    """An unknown level name is a ConfigurationError with the validation errors."""
    with pytest.raises(ConfigurationError) as exc_info:
        ConfigLoader.load(overrides={"component_log_levels": {"router": "LOUD"}})

    assert "Configuration validation failed" in str(exc_info.value)
    assert "validation_errors" in exc_info.value.details


def test_config_validation_wrong_type():
    """A value that cannot be read as the type of its key is a ConfigurationError."""
    with pytest.raises(ConfigurationError) as exc_info:
        ConfigLoader.load(overrides={"component_log_levels": ["router"]})

    assert "Configuration validation failed" in str(exc_info.value)


def test_config_validation_with_proper_context():
    """Test that ConfigurationError includes proper context."""
    with pytest.raises(ConfigurationError) as exc_info:
        ConfigLoader.load(overrides={"component_log_levels": {"router": "LOUD"}})

    error = exc_info.value
    assert error.message == "Configuration validation failed"
    assert isinstance(error.details["validation_errors"], list)
    validation_errors = error.details["validation_errors"]
    assert len(validation_errors) > 0
    # Each validation error should have type, loc, msg, and input fields
    for err in validation_errors:
        assert "type" in err
        assert "loc" in err
        assert "msg" in err


def test_config_validation_file_with_invalid_data(tmp_path):
    """Test that loading a file with invalid data raises ConfigurationError."""
    path = tmp_path / "skye.json"
    path.write_text('{"log_level": "INFO", "component_log_levels": {"router": "LOUD"}}', encoding="utf-8")

    with pytest.raises(ConfigurationError) as exc_info:
        load_config(path)

    assert "Configuration validation failed" in str(exc_info.value)


def test_config_validation_file_with_an_unknown_key(tmp_path):
    """A key that is not a configuration key is an error that names it (D106), not ignored."""
    path = tmp_path / "skye.json"
    path.write_text('{"log_level": "INFO", "models": {}}', encoding="utf-8")

    with pytest.raises(ConfigurationError, match="models"):
        load_config(path)
