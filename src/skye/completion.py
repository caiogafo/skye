"""Completion request, response and stream contracts (public path of `skye.base.completion`).

The code lives in `skye.base.completion`; import from here (or from `skye` for the commonest names).
"""

from skye.base.completion import (
    CapabilityCall,
    CompletionRequest,
    CompletionResponse,
    ExecutableCapabilityCall,
    StreamChunk,
    TokenUsage,
)

__all__ = [
    "CapabilityCall",
    "CompletionRequest",
    "CompletionResponse",
    "ExecutableCapabilityCall",
    "StreamChunk",
    "TokenUsage",
]
