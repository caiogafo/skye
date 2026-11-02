"""Skye - Modular GenAI library with optional extras.

Skye provides a foundational layer for building AI agents and intelligent applications
with a Clean Architecture approach. The base package includes only interfaces and models,
while all implementations are available as optional extras. The top level re-exports only
the four base modules (messages, completion, exceptions, config); import everything else
from its Component path (skye.models, skye.router, skye.tools, ...).

Installation:
    pip install skyeai                    # Base only
    pip install skyeai[bedrock]           # + Bedrock provider
    pip install skyeai[agents,memory]     # + Multiple extras
    pip install skyeai[all]               # Everything

Example:
    >>> from skye.base.messages import UserMessage
    >>> from skye.models.registry import provider
    >>>
    >>> client = provider("bedrock", region="us-east-1")
    >>> response = client.complete(
    ...     messages=[UserMessage("Hello")],
    ...     model="anthropic.claude-3-sonnet-20240229-v1:0"
    ... )
    >>> print(response.text)
"""

__version__ = "0.1.0"

from skye.base import completion, config, exceptions, messages

__all__ = ["__version__", "messages", "completion", "exceptions", "config"]
