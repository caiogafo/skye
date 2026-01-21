"""Nimbus Prompts Support Module.

This module provides comprehensive prompt template management using Jinja2,
including few-shot learning, multimodal content support, and structured output generation.

The implementation follows Nimbus's clean architecture principles and is available
as an optional extra (nimbus[prompts]).

Key Features:
- Jinja2 template engine with custom filters and macros
- Template versioning and composition
- Few-shot learning with dynamic example selection
- Multimodal content support (text, images, audio, video)
- Message role management (system, user, assistant, capability)
- Output schema validation and structured generation
- Performance optimization through caching

Example:
    >>> from nimbus.prompts import BasePromptBuilder
    >>> 
    >>> builder = BasePromptBuilder()
    >>> builder.register_template("greeting", "Hello {name}!")
    >>> messages = builder.render("greeting", {"name": "Alice"})
    >>> print(messages[0].content)
    'Hello Alice!'
"""

from nimbus.interfaces.prompt import PromptBuilderInterface

# Import base implementation
from .base import BasePromptBuilder

# Alias for backward compatibility and examples
MockPromptBuilder = BasePromptBuilder

__all__ = [
    "PromptBuilderInterface",
    "BasePromptBuilder",
    "MockPromptBuilder",  # Alias for examples
]