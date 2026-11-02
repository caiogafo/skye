"""Model interface for LLM providers.

This module defines the abstract interface that all LLM provider implementations
must follow. It supports both synchronous and asynchronous operations, streaming,
and provides a unified API regardless of the underlying provider.

**Polymorphic Input Support:**
The ModelInterface works with CompletionRequest which accepts either:
- **messages**: List of SkyeMessage objects (base Skye)
- **prompt**: Template name with variables (requires skyeai[prompts])

Implementations should handle both cases transparently. If a prompt is provided,
the implementation should resolve it to messages before calling the LLM.

Example (Base Skye):
    >>> from skye.base.interfaces.model import ModelInterface
    >>> from skye.base.completion import CompletionRequest
    >>> from skye.base.messages import UserMessage
    >>>
    >>> # Using messages directly
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="gpt-4"
    ... )
    >>> response = model.complete(request)

Example (With skyeai[prompts]):
    >>> # Using prompt templates
    >>> request = CompletionRequest(
    ...     prompt="greeting",
    ...     prompt_variables={"name": "Alice"},
    ...     model="gpt-4"
    ... )
    >>> response = model.complete(request)
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from skye.base.completion import CompletionRequest, CompletionResponse, StreamChunk


class ModelInterface(ABC):
    """Abstract interface for LLM providers.

    This interface defines the contract that all LLM provider implementations
    must follow. It provides methods for synchronous and asynchronous completion,
    streaming, and model metadata retrieval.

    All methods are abstract and must be implemented by concrete provider classes.

    **Polymorphic Input Handling:**
    Implementations should handle CompletionRequest with either:
    - `request.messages` - Direct message list (base Skye)
    - `request.prompt` - Template name to resolve (requires skyeai[prompts])

    When `request.prompt` is provided, implementations should:
    1. Check if a PromptBuilder is available (skyeai[prompts] installed)
    2. Resolve the prompt template to messages
    3. Proceed with the completion using the resolved messages

    This allows the same interface to work seamlessly with or without
    the optional prompts package.

    Example:
        >>> class OpenAIModel(ModelInterface):
        ...     def complete(self, request: CompletionRequest) -> CompletionResponse:
        ...         # Handle polymorphic input
        ...         if request.prompt:
        ...             # Resolve prompt to messages (if skyeai[prompts] available)
        ...             messages = self._resolve_prompt(request.prompt, request.prompt_variables)
        ...         else:
        ...             messages = request.messages
        ...
        ...         # Call OpenAI API with messages
        ...         return self._call_api(messages, request)
        ...
        ...     def stream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        ...         # Stream from OpenAI API
        ...         pass
        ...
        ...     async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        ...         # Async call to OpenAI API
        ...         pass
        ...
        ...     async def astream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        ...         # Async stream from OpenAI API
        ...         pass
        ...
        ...     def get_model_info(self) -> dict:
        ...         return {"name": "gpt-4", "provider": "openai"}
    """

    @abstractmethod
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a synchronous completion request.

        Accepts polymorphic input via CompletionRequest:
        - Use `request.messages` for direct message input (base Skye)
        - Use `request.prompt` + `request.prompt_variables` for template-based input
          (skyeai[prompts])

        Args:
            request: The completion request containing either messages or prompt template.

        Returns:
            CompletionResponse containing the model's response and metadata.

        Raises:
            ProviderError: If the provider API call fails.
            ValidationError: If the request is invalid.

        Example (Base Skye):
            >>> request = CompletionRequest(
            ...     messages=[UserMessage(content="Hello")],
            ...     model="gpt-4"
            ... )
            >>> response = model.complete(request)
            >>> print(response.content)

        Example (With skyeai[prompts]):
            >>> request = CompletionRequest(
            ...     prompt="greeting",
            ...     prompt_variables={"name": "Alice"},
            ...     model="gpt-4"
            ... )
            >>> response = model.complete(request)
            >>> print(response.content)
        """
        pass

    @abstractmethod
    def stream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        """Execute a streaming completion request.

        Args:
            request: The completion request containing messages and parameters.

        Yields:
            StreamChunk objects containing incremental response data.

        Raises:
            ProviderError: If the provider API call fails.
            ValidationError: If the request is invalid.

        Example:
            >>> request = CompletionRequest(
            ...     messages=[UserMessage(content="Hello")],
            ...     model="gpt-4",
            ...     stream=True
            ... )
            >>> for chunk in model.stream(request):
            ...     print(chunk.delta, end="")
        """
        pass

    @abstractmethod
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute an asynchronous completion request.

        Args:
            request: The completion request containing messages and parameters.

        Returns:
            CompletionResponse containing the model's response and metadata.

        Raises:
            ProviderError: If the provider API call fails.
            ValidationError: If the request is invalid.

        Example:
            >>> request = CompletionRequest(
            ...     messages=[UserMessage(content="Hello")],
            ...     model="gpt-4"
            ... )
            >>> response = await model.acomplete(request)
            >>> print(response.content)
        """
        pass

    @abstractmethod
    async def astream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        """Execute an asynchronous streaming completion request.

        Args:
            request: The completion request containing messages and parameters.

        Yields:
            StreamChunk objects containing incremental response data.

        Raises:
            ProviderError: If the provider API call fails.
            ValidationError: If the request is invalid.

        Example:
            >>> request = CompletionRequest(
            ...     messages=[UserMessage(content="Hello")],
            ...     model="gpt-4",
            ...     stream=True
            ... )
            >>> async for chunk in model.astream(request):
            ...     print(chunk.delta, end="")
        """
        pass

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Return metadata about the model.

        Returns:
            Dictionary containing model metadata such as name, provider,
            capabilities, and other relevant information.

        Example:
            >>> info = model.get_model_info()
            >>> print(info["provider"])
            'openai'
            >>> print(info["name"])
            'gpt-4'
        """
        pass
