"""Read a ``.skye`` file, and skip the read and the parse when the file did not change.

``skye.base.dsl`` takes text; this module is the one that reads a file. It keeps, in memory, what it
last built from each
path:

1. If the file's modification time and size are the same as the last time, the document built then
   is returned and the
   file is not even read.
2. If they differ, the file is read and hashed (SHA-256). If the hash is the same (the file was
   touched, not changed) the
   document is kept; if it differs the text is built again.

The one case this does not see is an edit that keeps both the modification time (to the nanosecond)
and the size; call
``clear_files_cache()`` (or pass ``use_cache=False``) when a program writes a file that fast. The
documents are
**read-only** and shared (see ``skye.base.dsl.cache``). Keeping the result on disk, in a form that
is quicker to read than
the source, is open decision O37.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Collection
from pathlib import Path

from skye.base.dsl import Document, build
from skye.base.dsl.cache import MAX_ENTRIES, cache_key, recall, remember, text_digest
from skye.base.exceptions import ConfigurationError

_FileKey = tuple[str, frozenset[str] | None]
_Signature = tuple[int, int]

_lock = threading.Lock()
_files: OrderedDict[_FileKey, tuple[_Signature, str, Document]] = OrderedDict()


def clear_files_cache() -> None:
    """Forget what was built from files (the text cache of ``skye.base.dsl`` is separate)."""
    with _lock:
        _files.clear()


def read_text(path: str | Path) -> str:
    """The text of a file, with a ``ConfigurationError`` for a missing or unreadable one.

    Args:
        path: The file.

    Raises:
        ConfigurationError: If the file does not exist or cannot be read as UTF-8.
    """
    target = Path(path)
    try:
        return target.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigurationError(
            f"File not found: {target}", details={"path": str(target)}
        ) from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigurationError(
            f"Cannot read {target}: {exc}", details={"path": str(target)}
        ) from exc


def load_document(
    path: str | Path,
    *,
    registry_names: Collection[str] | None = None,
    use_cache: bool = True,
) -> Document:
    """Read a ``.skye`` file and build its blocks, from memory when the file did not change.

    Args:
        path: The ``.skye`` file.
        registry_names: The names the caller will pass in its registry (``None`` = not checked).
        use_cache: Pass ``False`` to read and parse every time.

    Returns:
        The document (with its diagnostics). **Treat it as read-only.**

    Raises:
        ConfigurationError: If the file does not exist or cannot be read.
    """
    target = Path(path)
    if not use_cache:
        return build(read_text(target), filename=str(target), registry_names=registry_names)
    try:
        stat = target.stat()
    except OSError as exc:
        raise ConfigurationError(
            f"File not found: {target}", details={"path": str(target)}
        ) from exc
    signature = (stat.st_mtime_ns, stat.st_size)
    names = None if registry_names is None else frozenset(registry_names)
    file_key: _FileKey = (str(target.resolve()), names)
    with _lock:
        known = _files.get(file_key)
        if known is not None:
            _files.move_to_end(file_key)
    if known is not None and known[0] == signature:
        return known[2]
    text = read_text(target)
    digest = text_digest(text)
    if known is not None and known[1] == digest:
        document = known[2]
    else:
        key = cache_key(text, str(target), registry_names)
        cached = recall(key)
        document = (
            cached
            if cached is not None
            else remember(key, build(text, filename=str(target), registry_names=registry_names))
        )
    with _lock:
        _files[file_key] = (signature, digest, document)
        _files.move_to_end(file_key)
        while len(_files) > MAX_ENTRIES:
            _files.popitem(last=False)
    return document


def diagnostics_error(document: Document) -> ConfigurationError:
    """A ``ConfigurationError`` that lists every diagnostic of ``document``, one per line.

    Each line is ``file:line:column reason fix``; the diagnostics are also in
    ``details["diagnostics"]``
    (a list of ``Diagnostic``). Call it only when ``document.diagnostics`` is not empty.
    """
    lines = "\n".join(item.format() for item in document.diagnostics)
    return ConfigurationError(
        f"{document.filename} has {len(document.diagnostics)} error(s):\n{lines}",
        details={"path": document.filename, "diagnostics": list(document.diagnostics)},
    )


def load(path: str | Path, *, registry_names: Collection[str] | None = None) -> Document:
    """Read, parse and check a ``.skye`` file: the routers, flows and prompts it holds.

    The file is read through :func:`load_document`, so an unchanged file is not parsed again. The
    returned document has no diagnostics. It is **read-only** and shared.

    Args:
        path: The ``.skye`` file.
        registry_names: The names the caller will pass in its registry. When given, every
            ``registry.NAME`` is checked against them.

    Returns:
        The :class:`~skye.base.dsl.Document` (``routers``, ``flows``, ``prompts``, ``diagnostics``);
        ``document.flow("name")``, ``document.router()`` and ``document.prompt()`` pick one block.

    Raises:
        ConfigurationError: If the file is missing, unreadable or has mistakes; the message lists
            every mistake with file, line, column, reason and fix.

    Example:
        >>> import skye
        >>> document = skye.load("app.skye")  # doctest: +SKIP
        >>> document.flow("research").start  # doctest: +SKIP
    """
    document = load_document(path, registry_names=registry_names)
    if document.diagnostics:
        raise diagnostics_error(document)
    return document


__all__ = ["clear_files_cache", "diagnostics_error", "load", "load_document", "read_text"]
