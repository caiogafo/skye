"""The cache of built documents (``skye.base.dsl.cache``) and the file reader that skips the parse
when a file did not change.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from skye.base.dsl import build_cached, cache_info, clear_cache
from skye.base.dsl.cache import MAX_ENTRIES
from skye.base.exceptions import ConfigurationError
from skye.router.skye_file import load_router_config
from skye.utils import skye_files
from skye.utils.skye_files import clear_files_cache, load_document

ROUTER = 'router "main" { route "fast" = ["openai/gpt-4o-mini", "anthropic/claude-haiku"] }\n'
OTHER = 'router "other" { route "slow" = ["openai/gpt-4"] }\n'


@pytest.fixture(autouse=True)
def _empty_caches() -> None:
    clear_cache()
    clear_files_cache()


def test_the_same_text_is_built_once() -> None:
    first = build_cached(ROUTER, filename="a.skye")
    second = build_cached(ROUTER, filename="a.skye")
    assert second is first
    info = cache_info()
    assert (info.hits, info.misses, info.size) == (1, 1, 1)


def test_another_text_another_file_name_or_other_registry_names_build_again() -> None:
    base = build_cached(ROUTER, filename="a.skye")
    assert build_cached(OTHER, filename="a.skye") is not base
    assert build_cached(ROUTER, filename="b.skye") is not base
    assert build_cached(ROUTER, filename="a.skye", registry_names=["x"]) is not base
    assert build_cached(ROUTER, filename="a.skye", registry_names=["x"]) is build_cached(
        ROUTER, filename="a.skye", registry_names=("x",)
    )


def test_a_document_with_mistakes_is_cached_too() -> None:
    bad = 'flow "f" { step "A" { run = registry.a } }\n'
    first = build_cached(bad, filename="f.skye")
    assert first.diagnostics
    assert build_cached(bad, filename="f.skye") is first


def test_the_cache_is_bounded() -> None:
    for number in range(MAX_ENTRIES + 10):
        build_cached(f'router "r{number}" {{ route "x" = ["openai/gpt-4"] }}\n')
    assert cache_info().size == MAX_ENTRIES


def test_clear_cache_forgets_everything() -> None:
    build_cached(ROUTER)
    clear_cache()
    info = cache_info()
    assert (info.hits, info.misses, info.size) == (0, 0, 0)


def _count_reads(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    reads: list[str] = []
    original = skye_files.read_text

    def counting(path: str | Path) -> str:
        reads.append(str(path))
        return original(path)

    monkeypatch.setattr(skye_files, "read_text", counting)
    return reads


def test_a_file_that_did_not_change_is_neither_read_nor_parsed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "router.skye"
    path.write_text(ROUTER, encoding="utf-8")
    reads = _count_reads(monkeypatch)
    first = load_document(path)
    second = load_document(path)
    third = load_document(path)
    assert second is first and third is first
    assert len(reads) == 1
    assert first.ok


def test_a_file_that_was_touched_but_not_changed_keeps_its_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "router.skye"
    path.write_text(ROUTER, encoding="utf-8")
    first = load_document(path)
    stamp = path.stat().st_mtime_ns + 5_000_000_000
    os.utime(path, ns=(stamp, stamp))
    reads = _count_reads(monkeypatch)
    assert load_document(path) is first
    assert len(reads) == 1  # read and hashed, not parsed again
    assert load_document(path) is first
    assert len(reads) == 1  # and the new time is remembered


def test_a_file_that_changed_is_built_again(tmp_path: Path) -> None:
    path = tmp_path / "router.skye"
    path.write_text(ROUTER, encoding="utf-8")
    first = load_document(path)
    path.write_text(OTHER, encoding="utf-8")
    stamp = path.stat().st_mtime_ns + 5_000_000_000
    os.utime(path, ns=(stamp, stamp))
    second = load_document(path)
    assert second is not first
    assert second.routers[0].name == "other"


def test_use_cache_false_reads_and_parses_every_time(tmp_path: Path) -> None:
    path = tmp_path / "router.skye"
    path.write_text(ROUTER, encoding="utf-8")
    assert load_document(path, use_cache=False) is not load_document(path, use_cache=False)


def test_a_missing_file_is_a_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError) as caught:
        load_document(tmp_path / "nothing.skye")
    assert "not found" in str(caught.value).lower()


def test_the_router_loader_uses_the_cache_and_returns_a_new_dictionary_each_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "router.skye"
    path.write_text(ROUTER, encoding="utf-8")
    reads = _count_reads(monkeypatch)
    first = load_router_config(path)
    first["routes"].append("changed by the caller")
    second = load_router_config(path)
    assert len(reads) == 1
    assert second is not first
    assert "changed by the caller" not in second["routes"]
