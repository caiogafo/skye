"""Multimodal handler interface for processing images and other media.

This module defines the abstract interface for handling multimodal content
such as images, audio, and video in model requests.
"""

from abc import ABC, abstractmethod
from typing import Any


class MultimodalHandlerInterface(ABC):
    """Abstract interface for multimodal content handling.

    This interface defines the contract for processing and encoding multimodal
    content (images, audio, video) for use with LLM providers.

    Example:
        >>> class MyMultimodalHandler(MultimodalHandlerInterface):
        ...     def encode_image(self, image_source, format="base64"):
        ...         # Implementation
        ...         return "base64_encoded_image"
        ...
        ...     def supports_format(self, format):
        ...         return format in ["png", "jpg", "jpeg"]
    """

    @abstractmethod
    def encode_image(
        self, image_source: str | bytes, format: str = "base64"
    ) -> dict[str, Any]:
        """Encode an image for use in model requests.

        Args:
            image_source: Image file path, URL, or raw bytes.
            format: Encoding format ('base64', 'url', 'binary').

        Returns:
            Dictionary containing encoded image data in provider-specific format.

        Example:
            >>> encoded = handler.encode_image("path/to/image.jpg")
            >>> encoded = handler.encode_image("https://example.com/image.jpg")
            >>> encoded = handler.encode_image(image_bytes)
        """
        pass

    @abstractmethod
    def supports_format(self, format: str) -> bool:
        """Check if a media format is supported.

        Args:
            format: Media format (e.g., 'png', 'jpg', 'mp4', 'wav').

        Returns:
            True if the format is supported, False otherwise.

        Example:
            >>> if handler.supports_format("png"):
            ...     # Process PNG image
            ...     pass
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> list[str]:
        """Get list of supported media formats.

        Returns:
            List of supported format strings.

        Example:
            >>> formats = handler.get_supported_formats()
            >>> print(formats)
            ['png', 'jpg', 'jpeg', 'gif', 'webp']
        """
        pass

    @abstractmethod
    def validate_image(self, image_source: str | bytes) -> bool:
        """Validate that an image is valid and can be processed.

        Args:
            image_source: Image file path, URL, or raw bytes.

        Returns:
            True if the image is valid, False otherwise.

        Example:
            >>> if handler.validate_image("path/to/image.jpg"):
            ...     encoded = handler.encode_image("path/to/image.jpg")
        """
        pass

    @abstractmethod
    def get_image_dimensions(self, image_source: str | bytes) -> tuple[int, int]:
        """Get the dimensions of an image.

        Args:
            image_source: Image file path, URL, or raw bytes.

        Returns:
            Tuple of (width, height) in pixels.

        Example:
            >>> width, height = handler.get_image_dimensions("path/to/image.jpg")
            >>> print(f"{width}x{height}")
        """
        pass
