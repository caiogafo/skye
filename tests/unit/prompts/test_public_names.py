"""The prompt names a user needs have a public path in ``skye.prompts`` (docs finding 22, D34)."""

from __future__ import annotations

import pytest

import skye.prompts
from skye.base import dsl as base_dsl
from skye.base import prompt_parts
from skye.prompts import skye_prompts

PUBLIC = {
    "PromptSpec": base_dsl,
    "OutputSpec": base_dsl,
    "PromptPartSpec": base_dsl,
    "PromptParts": prompt_parts,
    "OutputSchema": prompt_parts,
    "render_parts": skye_prompts,
    "output_json_schema": skye_prompts,
}


@pytest.mark.parametrize("name", sorted(PUBLIC))
def test_the_name_is_public_in_skye_prompts(name: str) -> None:
    assert name in skye.prompts.__all__
    assert getattr(skye.prompts, name) is getattr(PUBLIC[name], name)


def test_the_old_jinja_name_is_gone() -> None:
    assert not hasattr(skye.prompts.BasePromptBuilder, "register_jinja_filter")
