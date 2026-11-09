"""Configuration: a file, environment variables and code overrides, in that order of precedence (code > environment > file).

The library reads exactly three prefixed environment variables: ``SKYE_LOG_LEVEL``, ``SKYE_CONFIG`` (the path of the configuration
file, JSON; the library reads no YAML) and ``SKYE_ENABLE_TELEMETRY``. Provider credentials are never read from a prefixed variable: they come from each provider's
standard variable (``OPENAI_API_KEY``, ``AWS_*``, ...). Inside a file, ``${VAR}`` is replaced by the environment variable.
"""

import os
import tempfile
from pathlib import Path

import skye
from skye.config import substitute_env_vars

CONFIG = '{"log_level": "INFO", "enable_telemetry": false}'


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "skye.json"
        path.write_text(CONFIG, encoding="utf-8")

        config = skye.load_config(path)
        print("from the file:       ", config.log_level)

        os.environ["SKYE_LOG_LEVEL"] = "WARNING"
        config = skye.load_config(path)
        print("environment wins:    ", config.log_level)

        config = skye.load_config(path, overrides={"log_level": "ERROR"})
        print("code wins:           ", config.log_level)
        del os.environ["SKYE_LOG_LEVEL"]

    os.environ.setdefault("OPENAI_API_KEY", "sk-example")
    print("substitution:        ", substitute_env_vars({"api_key": "${OPENAI_API_KEY}"}))


if __name__ == "__main__":
    main()
