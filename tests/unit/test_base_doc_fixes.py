"""Regression tests for base findings 27, 28 and 29 of the documentation review (2026-11-11)."""

from __future__ import annotations

import tomllib
from pathlib import Path

import skye
from skye.base.interfaces import storage

ROOT = Path(__file__).resolve().parents[2]


def test_the_package_docstring_describes_the_library_as_it_is() -> None:
    """Item 27: no "Clean Architecture", no "implementations are optional extras"."""
    doc = skye.__doc__ or ""
    assert "Clean Architecture" not in doc
    assert "implementations are available as optional extras" not in doc
    assert "standard library" in doc and "skye.dsl" in doc


def test_the_all_bundle_holds_every_optional_store_driver_but_boto3() -> None:
    """Item 28: `all` gains valkey and asyncpg; boto3 (the AWS SDK, in Lambda already) stays out."""
    extras = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "optional-dependencies"
    ]
    names = {req.split(">")[0].split("[")[0].strip() for req in extras["all"]}
    assert {"valkey", "asyncpg", "redis", "pg8000", "tiktoken", "rsa", "fastmcp-slim"} <= names
    assert "boto3" not in names


def test_scan_store_docstring_names_the_five_backends() -> None:
    """Item 29: five backends implement ``keys``, every one but the durable function."""
    doc = storage.__doc__ or ""
    assert "agents archive" not in doc
    assert "five backends" in doc and "durable function" in doc
    import skye.store as store

    backends = [
        getattr(store, name)
        for name in store.__all__
        if name.endswith("Backend") and name != "StorageBackend"
    ]
    scanning = sorted(cls.__name__ for cls in backends if hasattr(cls, "keys"))
    assert scanning == [
        "DynamoDBBackend",
        "FileSystemBackend",
        "InMemoryBackend",
        "PostgreSQLBackend",
        "RedisBackend",
    ]
