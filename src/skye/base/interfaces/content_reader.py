"""Content reader interface for document loading.

This module defines the abstract interface for content readers that load
and process documents from various sources.

Raises: ProviderError or ValidationError when a source cannot be read or has an unsupported type.
Missing: an empty source yields an empty list, never ``None``.
Concurrency: a reader holds no per-call state; ``read`` and ``aread`` may run in parallel.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from skye.base.messages import ContentChunk


class ContentReaderInterface(ABC):
    """Abstract interface for content readers.

    This interface defines the contract for loading and processing content
    from various sources (files, URLs, databases, etc.) into ContentChunk objects.
    """

    @abstractmethod
    def read(self, source: str) -> list[ContentChunk]:
        """Read content from a source.

        Args:
            source: Source identifier (file path, URL, etc.).

        Returns:
            List of content chunks.
        """
        pass

    @abstractmethod
    def read_stream(self, source: str) -> Iterator[ContentChunk]:
        """Read content from a source as a stream.

        Args:
            source: Source identifier (file path, URL, etc.).

        Yields:
            Content chunks as they are read.
        """
        pass

    @abstractmethod
    async def aread(self, source: str) -> list[ContentChunk]:
        """Read content from a source asynchronously.

        Args:
            source: Source identifier (file path, URL, etc.).

        Returns:
            List of content chunks.
        """
        pass

    @abstractmethod
    def get_reader_metadata(self) -> dict[str, Any]:
        """Return metadata about the reader.

        Returns:
            Dictionary containing reader metadata such as supported formats,
            capabilities, and configuration.
        """
        pass
