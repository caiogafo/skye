"""Nimbus - Modular GenAI library with optional extras.

Nimbus provides a foundational layer for building AI agents and intelligent applications
with a Clean Architecture approach. The base package includes only interfaces and models,
while all implementations are available as optional extras. The top level re-exports only
the four base modules (messages, completion, exceptions, config); import everything else
from its Component path (nimbus.models, nimbus.router, nimbus.tools, ...).

Installation:
    pip install nimbus                    # Base only
    pip install nimbus[bedrock]           # + Bedrock provider
    pip install nimbus[agents,memory]     # + Multiple extras
    pip install nimbus[all]               # Everything

Example:
    >>> from nimbus.base.messages import UserMessage
    >>> from nimbus.models.registry import provider
    >>>
    >>> client = provider("bedrock", region="us-east-1")
    >>> response = client.complete(
    ...     messages=[UserMessage("Hello")],
    ...     model="anthropic.claude-3-sonnet-20240229-v1:0"
    ... )
    >>> print(response.text)
"""

__version__ = "0.1.0"

from nimbus.base import completion, config, exceptions, messages

__all__ = ["__version__", "messages", "completion", "exceptions", "config"]
