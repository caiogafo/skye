"""Prompt templates rendered into role-based messages.

Part of the base install (``pip install skyeai``): the template engine is the standard
library's, with ``{{ var }}``, ``if``/``elif``/``else``, ``for`` and filters, and no Jinja2.

Key features:
- Template registration, versioning and composition
- Default values, optional variables and partial builders
- Few-shot examples with an example selector
- Roles from ``[SYSTEM]``, ``[USER]`` and ``[ASSISTANT]`` markers
- Output instructions from a declared schema, as JSON, a Markdown table or XML
- Bundled templates (``classification``, ``chat``, ``summarization``, ...)
- ``.skye`` prompt blocks rendered with real roles (``load_prompt``, ``render_prompt``)
- Help for a prompt: its inputs and output (``describe_prompt``, ``prompt_help``,
  ``BasePromptBuilder.help``, ``skye prompt info``)

Example:
    >>> from skye.prompts import BasePromptBuilder
    >>> builder = BasePromptBuilder()
    >>> builder.register_template("greeting", "Hello {{ name }}!")
    >>> messages = builder.render("greeting", {"name": "Alice"})
    >>> messages[0].content
    'Hello Alice!'

Codename: cirrus.
"""

from skye.base.dsl.info import (
    InputInfo,
    OutputFieldInfo,
    OutputInfo,
    PromptInfo,
    describe_prompt,
    prompt_help,
)
from skye.base.interfaces.prompt import PromptBuilderInterface

from .messages import BasePromptBuilder
from .skye_prompts import (
    PromptRunnable,
    active_output,
    load_prompt,
    output_instructions,
    render_prompt,
)

__all__ = [
    "PromptBuilderInterface",
    "BasePromptBuilder",
    "InputInfo",
    "OutputFieldInfo",
    "OutputInfo",
    "PromptInfo",
    "PromptRunnable",
    "describe_prompt",
    "prompt_help",
    "active_output",
    "load_prompt",
    "output_instructions",
    "render_prompt",
]
