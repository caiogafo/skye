"""Simple boto3-style client interface for Nimbus.

This module provides a simplified API that mimics boto3's client pattern,
making it easier to use Nimbus with a familiar interface.

Example:
    >>> import nimbus
    >>> from nimbus.messages import UserMessage
    >>>
    >>> client = nimbus.provider("bedrock", region="us-east-1")
    >>> response = client.complete(
    ...     messages=[UserMessage("Hello")],
    ...     model="anthropic.claude-3-sonnet-20240229-v1:0"
    ... )
    >>> print(response.text)
"""

from typing import Any, Iterator

from nimbus.completion import CompletionRequest, CompletionResponse
from nimbus.messages import AssistantMessage, NimbusMessage
from nimbus.providers.registry import ProviderRegistry


class ResponseMetadata:
    """Metadata about the completion response."""

    def __init__(self, response: CompletionResponse):
        self._response = response

    @property
    def model(self) -> str:
        """The model that generated the response."""
        return self._response.model

    @property
    def tokens(self) -> int:
        """Total tokens used (prompt + completion)."""
        return self._response.usage.total_tokens

    @property
    def prompt_tokens(self) -> int:
        """Tokens used in the prompt."""
        return self._response.usage.prompt_tokens

    @property
    def completion_tokens(self) -> int:
        """Tokens used in the completion."""
        return self._response.usage.completion_tokens

    @property
    def finish(self) -> str:
        """Finish reason (e.g., 'stop', 'length', 'content_filter')."""
        return self._response.finish_reason or "unknown"

    @property
    def provider(self) -> str:
        """The provider that generated the response."""
        return self._response.provider


class SimpleResponse:
    """Simplified response object with boto3-style attributes."""

    def __init__(self, response: CompletionResponse):
        self._response = response
        self._meta = ResponseMetadata(response)

    @property
    def text(self) -> str:
        """The generated text content."""
        return self._response.content

    @property
    def content(self) -> str:
        """Alias for text."""
        return self._response.content

    @property
    def meta(self) -> ResponseMetadata:
        """Response metadata (model, tokens, finish reason, etc.)."""
        return self._meta

    @property
    def metadata(self) -> ResponseMetadata:
        """Alias for meta."""
        return self._meta

    def to_message(self) -> AssistantMessage:
        """Convert response to an AssistantMessage for conversation history."""
        return self._response.to_message()


class SimpleClient:
    """Simplified boto3-style client for Nimbus providers.

    This client provides a simpler interface compared to the full ModelInterface,
    with methods that accept messages directly and return simplified response objects.

    Example:
        >>> client = nimbus.provider("openai", api_key="sk-...")
        >>> response = client.complete(
        ...     messages=[UserMessage("Hello")],
        ...     model="gpt-4"
        ... )
        >>> print(response.text)
        >>> print(response.meta.tokens)
    """

    def __init__(self, provider_name: str, **config: Any):
        """Initialize the simple client.

        Args:
            provider_name: Name of the provider (e.g., "openai", "bedrock").
            **config: Provider-specific configuration.
        """
        self._provider = ProviderRegistry.get_model_provider(provider_name, **config)
        self._provider_name = provider_name

    def complete(
        self,
        messages: list[NimbusMessage] | str,
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> SimpleResponse:
        """Generate a completion.

        Args:
            messages: List of NimbusMessage objects or a string prompt.
            model: Model identifier (e.g., "gpt-4", "claude-3-sonnet").
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Returns:
            SimpleResponse with .text and .meta attributes.

        Example:
            >>> from nimbus.messages import UserMessage
            >>> response = client.complete(
            ...     messages=[UserMessage("What is AI?")],
            ...     model="gpt-4",
            ...     temperature=0.7
            ... )
            >>> print(response.text)
        """
        # Convert string to UserMessage if needed
        if isinstance(messages, str):
            from nimbus.messages import UserMessage

            messages = [UserMessage(content=messages)]

        # Build request
        request = CompletionRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Get response
        response = self._provider.complete(request)

        return SimpleResponse(response)

    def stream(
        self,
        messages: list[NimbusMessage] | str,
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Generate a streaming completion.

        Args:
            messages: List of NimbusMessage objects or a string prompt.
            model: Model identifier.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Yields:
            Text chunks as they are generated.

        Example:
            >>> for chunk in client.stream(
            ...     messages=[UserMessage("Write a story")],
            ...     model="gpt-4"
            ... ):
            ...     print(chunk, end="", flush=True)
        """
        # Convert string to UserMessage if needed
        if isinstance(messages, str):
            from nimbus.messages import UserMessage

            messages = [UserMessage(content=messages)]

        # Build request with streaming enabled
        request = CompletionRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

        # Stream response
        for chunk in self._provider.stream(request):
            yield chunk.delta

    async def acomplete(
        self,
        messages: list[NimbusMessage] | str,
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> SimpleResponse:
        """Async version of complete().

        Args:
            messages: List of NimbusMessage objects or a string prompt.
            model: Model identifier.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Returns:
            SimpleResponse with .text and .meta attributes.
        """
        # Convert string to UserMessage if needed
        if isinstance(messages, str):
            from nimbus.messages import UserMessage

            messages = [UserMessage(content=messages)]

        # Build request
        request = CompletionRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Get response
        response = await self._provider.acomplete(request)

        return SimpleResponse(response)


def provider(name: str, **config: Any) -> SimpleClient:
    """Create a simple client for the specified provider.

    This is the main entry point for the simplified boto3-style API.

    Args:
        name: Provider name (e.g., "openai", "bedrock", "anthropic").
        **config: Provider-specific configuration.

    Returns:
        SimpleClient instance.

    Example:
        >>> import nimbus
        >>> from nimbus.messages import UserMessage
        >>>
        >>> # OpenAI
        >>> client = nimbus.provider("openai", api_key="sk-...")
        >>> response = client.complete(
        ...     messages=[UserMessage("Hello")],
        ...     model="gpt-4"
        ... )
        >>>
        >>> # Bedrock
        >>> client = nimbus.provider("bedrock", region="us-east-1")
        >>> response = client.complete(
        ...     messages=[UserMessage("Hello")],
        ...     model="anthropic.claude-3-sonnet-20240229-v1:0"
        ... )
        >>>
        >>> # Anthropic
        >>> client = nimbus.provider("anthropic", api_key="sk-ant-...")
        >>> response = client.complete(
        ...     messages=[UserMessage("Hello")],
        ...     model="claude-3-sonnet-20240229"
        ... )
    """
    return SimpleClient(name, **config)
