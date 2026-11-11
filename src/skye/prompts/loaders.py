"""Template loaders for Skye prompts (structure task 7.3).

Discovers template files in the `templates/` directory and registers them on a
prompt builder (liteprompt-style loaders and registry; rendering uses the stdlib engine in
`skye.prompts.engine`, not Jinja2, interpolation only). `*.skye` prompt files (D60) are read next
to `*.jinja`, `*.txt`, `*.template` and `*.tmpl` text templates (`{{ }}` and filters; a `{% %}`
tag makes the file fail to load, D76); when a `.skye` file and another file share a name, only
the `.skye` one is registered.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from skye.base.dsl.metadata import split_metadata

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"

#: Extensions read, in order of preference: a `.skye` file wins over a template of the same name.
TEMPLATE_EXTENSIONS: tuple[str, ...] = (".skye", ".jinja", ".txt", ".template", ".tmpl")


def discover_templates(directory: Path) -> dict[str, Path]:
    """Find the template files of ``directory``, one per name (the file stem).

    Args:
        directory: The folder to read.

    Returns:
        The file of each template name; a `.skye` file wins over the other extensions.
    """
    found: dict[str, Path] = {}
    for extension in TEMPLATE_EXTENSIONS:
        for path in sorted(directory.glob(f"*{extension}")):
            found.setdefault(path.stem, path)
    return found


def load_default_templates(builder: Any, directory: Path | None = None) -> int:
    """Register the templates of the templates folder.

    A ``.skye`` file is registered under the ``version`` of its front matter (``---`` ... ``---``);
    any other file, or one without a version, as ``1.0``.

    A file that cannot be read or parsed is skipped with a warning in the log.

    Args:
        builder: The prompt builder (anything with ``register_template``).
        directory: The folder to read (default: the bundled templates).

    Returns:
        How many templates were registered.
    """
    templates_dir = directory or TEMPLATES_DIR
    if not templates_dir.exists():
        logger.warning("Templates directory not found", extra={"directory": str(templates_dir)})
        return 0

    files = discover_templates(templates_dir)
    if not files:
        logger.warning("No template files found", extra={"directory": str(templates_dir)})
        return 0

    loaded = 0
    for name, path in files.items():
        try:
            version = _metadata_version(path) or "1.0"
            builder.register_template(name, str(path), version=version, from_string=False)
        except (OSError, ValueError) as e:
            logger.warning(
                "Could not load template",
                extra={"template": name, "path": str(path), "error": str(e)},
            )
            continue
        loaded += 1

    logger.debug(
        "Loaded prompt templates", extra={"count": loaded, "directory": str(templates_dir)}
    )
    return loaded


def _metadata_version(path: Path) -> str | None:
    """The ``version`` in the front matter of a ``.skye`` file, or ``None``."""
    if path.suffix != ".skye":
        return None
    metadata, _, errors = split_metadata(path.read_text(encoding="utf-8"), str(path))
    version = metadata.get("version")
    return str(version) if version is not None and not errors else None
