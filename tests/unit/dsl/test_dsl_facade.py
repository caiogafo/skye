"""The public path ``skye.dsl`` (D78) carries every `.skye` name a user needs (finding 26)."""

from __future__ import annotations

from pathlib import Path

import pytest

import skye.dsl
from skye.base import dsl as base_dsl
from skye.utils import skye_files

PUBLIC = {
    "SkyeSyntaxError": base_dsl,
    "build": base_dsl,
    "to_text": base_dsl,
    "build_cached": base_dsl,
    "clear_cache": base_dsl,
    "load_document": skye_files,
}


@pytest.mark.parametrize("name", sorted(PUBLIC))
def test_the_name_is_on_the_public_path(name: str) -> None:
    assert name in skye.dsl.__all__
    assert getattr(skye.dsl, name) is getattr(PUBLIC[name], name)


def test_the_facade_round_trips_a_router(tmp_path: Path) -> None:
    text = 'router "r" {\n  route "a" = ["openai/gpt-4o-mini"]\n}\n'
    document = skye.dsl.build(text)
    assert document.diagnostics == [] and document.routers
    assert skye.dsl.build(skye.dsl.to_text(document)).routers == document.routers
    skye.dsl.clear_cache()
    assert skye.dsl.build_cached(text).routers == document.routers
    path = tmp_path / "app.skye"
    path.write_text(text, encoding="utf-8")
    assert skye.dsl.load_document(path).routers == document.routers
    assert issubclass(skye.dsl.SkyeSyntaxError, skye.exceptions.SkyeError)
