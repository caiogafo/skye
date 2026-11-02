"""Skye Prompts Support Module.

This module provides comprehensive prompt template management with a standard-library template engine,
including few-shot learning, multimodal content support, and structured output generation.

The implementation follows Skye's clean architecture principles and is available
as an optional extra (skyeai[prompts]).

Key Features:
- Stdlib template engine ({{ var }}, if/elif/else, for, filters; no Jinja2)
- Template versioning and composition
- Few-shot learning with dynamic example selection
- Multimodal content support (text, images, audio, video)
- Message role management (system, user, assistant, capability)
- Output schema validation and structured generation
- Performance optimization through caching

Example:
    >>> from skye.prompts import BasePromptBuilder
    >>> 
    >>> builder = BasePromptBuilder()
    >>> builder.register_template("greeting", "Hello {name}!")
    >>> messages = builder.render("greeting", {"name": "Alice"})
    >>> print(messages[0].content)
    'Hello Alice!'

Codename: cirrus.
"""

from skye.base.interfaces.prompt import PromptBuilderInterface

# Import base implementation
from .messages import BasePromptBuilder

# Alias for backward compatibility and examples
MockPromptBuilder = BasePromptBuilder

__all__ = [
    "PromptBuilderInterface",
    "BasePromptBuilder",
    "MockPromptBuilder",  # Alias for examples
]