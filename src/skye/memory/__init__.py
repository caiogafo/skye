"""Persistent memory implementations (optional extra).

This module provides persistent memory implementations for episodic, semantic,
and persona memory. Available with skyeai[memory].

Component: memory. Layer: services (2).

Codename: dew.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    """A single memory entry.

    Represents a piece of information stored in memory, with support for
    different memory types (episodic, semantic, persona) and optional
    vector embeddings for semantic search.

    Attributes:
        id: Unique identifier for the memory entry.
        content: The text content of the memory.
        memory_type: Type of memory (episodic, semantic, persona).
        embedding: Optional vector embedding for semantic search.
        metadata: Additional metadata about the memory.
        created_at: Timestamp when the memory was created.

    Example:
        >>> entry = MemoryEntry(
        ...     content="The user's name is Alice",
        ...     memory_type="persona",
        ...     metadata={"source": "conversation", "confidence": 0.95}
        ... )
        >>> entry.memory_type
        'persona'
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    memory_type: str  # episodic, semantic, persona
    embedding: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = ["MemoryEntry"]
