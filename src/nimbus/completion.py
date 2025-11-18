"""Completion request and response models for Nimbus.

This module provides Pydantic models for LLM completion requests and responses,
including support for streaming, structured outputs, and token usage tracking.

Example:
    >>> from nimbus.completion import CompletionRequest, TokenUsage
    >>> from nimbus.messages import UserMessage
    >>>
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="gpt-4",
    ...     temperature=0.7
    ... )
    >>> request.temperature
    0.7
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from nimbus.messages import NimbusMessage


class TokenUsage(BaseModel):
    """Token usage statistics for a completion request.

    Tracks the number of tokens used in the prompt, completion, and total.
    This information is essential for cost tracking and rate limiting.

    Attributes:
        prompt_tokens: Number of tokens in the input prompt.
        completion_tokens: Number of tokens in the generated completion.
        total_tokens: Total tokens used (prompt + completion).

    Example:
        >>> usage = TokenUsage(
        ...     prompt_tokens=10,
        ...     completion_tokens=20,
        ...     total_tokens=30
        ... )
        >>> usage.total_tokens
        30
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionRequest(BaseModel):
    """Request for model completion.

    Represents a request to an LLM provider with all necessary parameters
    including messages, model configuration, and optional structured output schema.

    **Polymorphic Input Support:**
    - **Base Nimbus**: Use `messages` parameter with list of NimbusMessage objects
    - **With nimbus[prompts]**: Use `prompt` parameter with template name and variables

    The interface accepts either messages OR prompt, making it work seamlessly
    with or without the optional prompts package installed.

    Attributes:
        messages: List of messages in the conversation (base Nimbus).
        prompt: Prompt template name (requires nimbus[prompts]).
        prompt_variables: Variables for prompt template rendering.
        model: Model identifier (e.g., 'gpt-4', 'claude-3-sonnet').
        temperature: Sampling temperature (0.0-2.0). Higher values make output more random.
        max_tokens: Maximum number of tokens to generate.
        top_p: Nucleus sampling parameter (0.0-1.0).
        stop: List of sequences that will stop generation.
        stream: Whether to stream the response.
        capabilities: List of capabilities/tools available to the model.
        capability_choice: How the model should choose capabilities
            ('auto', 'none', or specific name).
        response_format: Format specification for structured outputs.
        response_schema: Pydantic model class for structured output validation.
        metadata: Additional metadata for the request.

    Example (Base Nimbus):
        >>> from nimbus.messages import UserMessage
        >>> request = CompletionRequest(
        ...     messages=[UserMessage(content="What is 2+2?")],
        ...     model="gpt-4",
        ...     temperature=0.7
        ... )
        >>> request.model
        'gpt-4'

    Example (With nimbus[prompts]):
        >>> # Using prompt templates (requires nimbus[prompts])
        >>> request = CompletionRequest(
        ...     prompt="math_solver",
        ...     prompt_variables={"problem": "What is 2+2?"},
        ...     model="gpt-4"
        ... )
        >>> request.prompt
        'math_solver'
    """

    # Polymorphic input: either messages OR prompt
    messages: list[NimbusMessage] | None = None
    prompt: str | None = None  # Template name (requires nimbus[prompts])
    prompt_variables: dict[str, Any] = Field(default_factory=dict)

    model: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stop: list[str] | None = None
    stream: bool = False
    capabilities: list[dict[str, Any]] | None = None
    capability_choice: str | None = None
    response_format: dict[str, Any] | None = None
    response_schema: type[BaseModel] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Validate that either messages or prompt is provided, but not both."""
        if self.messages is None and self.prompt is None:
            raise ValueError("Either 'messages' or 'prompt' must be provided")
        if self.messages is not None and self.prompt is not None:
            raise ValueError("Cannot provide both 'messages' and 'prompt' - use one or the other")


class CompletionResponse(BaseModel):
    """Response from model completion.

    Represents the response from an LLM provider, including the generated content,
    token usage, and optional structured output.

    Attributes:
        id: Unique identifier for the response.
        model: Model identifier that generated the response.
        provider: Provider name (e.g., 'openai', 'anthropic', 'bedrock').
        content: The generated text content.
        structured_output: Parsed structured output if response_schema was provided.
        role: Role of the responder (typically 'assistant').
        finish_reason: Reason the generation stopped ('stop', 'length', 'tool_calls', etc.).
        usage: Token usage statistics.
        created_at: Timestamp when the response was created.
        metadata: Additional metadata about the response.

    Example:
        >>> from datetime import datetime, timezone
        >>> response = CompletionResponse(
        ...     id="resp_123",
        ...     model="gpt-4",
        ...     provider="openai",
        ...     content="The answer is 4.",
        ...     role="assistant",
        ...     finish_reason="stop",
        ...     usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        ...     created_at=datetime.now(timezone.utc)
        ... )
        >>> response.get_output()
        'The answer is 4.'
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    model: str
    provider: str
    content: str
    structured_output: BaseModel | None = None
    role: str = "assistant"
    finish_reason: str
    usage: TokenUsage
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_output(self) -> str | BaseModel:
        """Get the output - structured if available, otherwise text content.

        Returns:
            The structured output if available, otherwise the text content.

        Example:
            >>> # With text content
            >>> response = CompletionResponse(
            ...     model="gpt-4",
            ...     provider="openai",
            ...     content="Hello",
            ...     finish_reason="stop",
            ...     usage=TokenUsage(prompt_tokens=5, completion_tokens=2, total_tokens=7)
            ... )
            >>> response.get_output()
            'Hello'
            >>>
            >>> # With structured output
            >>> from pydantic import BaseModel
            >>> class Person(BaseModel):
            ...     name: str
            >>> person = Person(name="Alice")
            >>> response.structured_output = person
            >>> response.get_output().name
            'Alice'
        """
        return self.structured_output if self.structured_output else self.content


class StreamChunk(BaseModel):
    """A chunk from a streaming response.

    Represents a single chunk of data received during streaming completion.
    Multiple chunks are received sequentially to build the complete response.

    Attributes:
        id: Unique identifier for the stream.
        delta: The incremental content in this chunk.
        finish_reason: Reason the generation stopped (only set in final chunk).
        index: Index of this chunk in the stream sequence.

    Example:
        >>> chunk = StreamChunk(
        ...     id="stream_123",
        ...     delta="Hello",
        ...     index=0
        ... )
        >>> chunk.delta
        'Hello'
        >>>
        >>> # Final chunk
        >>> final_chunk = StreamChunk(
        ...     id="stream_123",
        ...     delta="",
        ...     finish_reason="stop",
        ...     index=5
        ... )
        >>> final_chunk.finish_reason
        'stop'
    """

    id: str
    delta: str
    finish_reason: str | None = None
    index: int = 0
