"""Vector encoder interface for embeddings.

This module defines the abstract interface for vector encoding (embeddings)
with support for both synchronous and asynchronous operations.

Raises: ProviderError when the provider call fails, ValidationError for an empty or oversized input.
Missing: an empty list of texts yields an empty list of vectors.
Concurrency: ``encode`` blocks the thread, ``aencode`` runs on the event loop; an instance is shared by many calls.
"""

from abc import ABC, abstractmethod


class VectorEncoderInterface(ABC):
    """Abstract interface for vector encoders.

    This interface defines the contract for embedding implementations that
    convert text into vector representations for semantic search and similarity.
    """

    @abstractmethod
    def encode(self, text: str) -> list[float]:
        """Encode text into a vector.

        Args:
            text: The text to encode.

        Returns:
            Vector representation of the text.
        """
        pass

    @abstractmethod
    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts into vectors.

        Args:
            texts: List of texts to encode.

        Returns:
            List of vector representations.
        """
        pass

    @abstractmethod
    async def aencode(self, text: str) -> list[float]:
        """Encode text into a vector asynchronously.

        Args:
            text: The text to encode.

        Returns:
            Vector representation of the text.
        """
        pass

    @abstractmethod
    async def aencode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts into vectors asynchronously.

        Args:
            texts: List of texts to encode.

        Returns:
            List of vector representations.
        """
        pass

    @abstractmethod
    def get_vector_dimension(self) -> int:
        """Return the dimension of the vectors produced.

        Returns:
            The vector dimension size.
        """
        pass
