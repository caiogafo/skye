"""Configuration: a file, environment variables and code overrides, in that order of precedence (code > environment > file).

The library reads exactly three prefixed environment variables: ``SKYE_LOG_LEVEL``, ``SKYE_CONFIG`` (the path of the configuration
file) and ``SKYE_ENABLE_TELEMETRY``. Provider credentials are never read from a prefixed variable: they come from each provider's
standard variable (``OPENAI_API_KEY``, ``AWS_*``, ...). Inside a file, ``${VAR}`` is replaced by the environment variable.
"""

import os
import tempfile
from pathlib import Path

from skye.config import ConfigLoader, substitute_env_vars

YAML = """\
log_level: INFO
enable_telemetry: false
"""


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "skye.yaml"
        path.write_text(YAML, encoding="utf-8")

        config = ConfigLoader.load(config_path=path)
        print("from the file:       ", config.log_level)

        os.environ["SKYE_LOG_LEVEL"] = "WARNING"
        config = ConfigLoader.load(config_path=path)
        print("environment wins:    ", config.log_level)

        config = ConfigLoader.load(config_path=path, overrides={"log_level": "ERROR"})
        print("code wins:           ", config.log_level)
        del os.environ["SKYE_LOG_LEVEL"]

    os.environ.setdefault("OPENAI_API_KEY", "sk-example")
    print("substitution:        ", substitute_env_vars({"api_key": "${OPENAI_API_KEY}"}))


if __name__ == "__main__":
    main()
