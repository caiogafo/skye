"""Read the configuration file of the library: the one place that opens it.

``skye.base.config.ConfigLoader`` takes text and opens no file, because ``base`` does no file I/O
(Requirement 3.2, decision D91). This module opens the file, the same way ``skye_files`` opens the
``.skye`` files for ``skye.base.dsl``, and is public as ``skye.load_config``. The file is JSON in
version 1 (decision D92); YAML is refused (decision D62).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skye.base.config import ConfigLoader, SkyeConfig, reject_yaml
from skye.base.exceptions import ConfigurationError
from skye.utils.skye_files import read_text


def load_config(
    path: str | Path | None = None, *, overrides: dict[str, Any] | None = None
) -> SkyeConfig:
    """Load the configuration: the JSON file, then the ``SKYE_`` environment, then ``overrides``.

    Args:
        path: The JSON configuration file. When ``None``, the file that ``SKYE_CONFIG`` names is
            read, and with neither only the environment and ``overrides`` count.
        overrides: Values that win over the file and the environment.

    Returns:
        SkyeConfig: The validated configuration.

    Raises:
        ConfigurationError: If the file is YAML, is not ``.json``, is missing or unreadable, is not
            a JSON object, or the merged values do not validate.

    Example:
        >>> import skye
        >>> config = skye.load_config(overrides={"log_level": "DEBUG"})  # no file: environment, code
        >>> config.log_level
        'DEBUG'
    """
    if path is None:
        path = ConfigLoader.config_path_from_env()
        if path is None:
            return ConfigLoader.from_dict({}, overrides)
    target = Path(path)
    reject_yaml(target)  # say it plainly: the library reads no YAML (D62)
    if target.suffix.lower() != ".json":
        raise ConfigurationError(
            f"Unsupported configuration file format: {target.suffix or '(none)'};"
            " the configuration file is JSON.",
            details={"path": str(target), "suffix": target.suffix, "supported": [".json"]},
        )
    if not target.exists():
        raise ConfigurationError(
            f"Configuration file not found: {target}", details={"path": str(target)}
        )
    return ConfigLoader.from_text(read_text(target), source=str(target), overrides=overrides)


__all__ = ["load_config"]
