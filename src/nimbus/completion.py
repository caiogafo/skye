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
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from nimbus.messages import NimbusMessage

if TYPE_CHECKING:
    from nimbus.capabilities.registry import CapabilityRegistry
    from nimbus.capabilities.capability_models import CapabilityResult


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
        capabilities: List of capabilities/tools available to the model
            (requires nimbus[capabilities]).
        capability_choice: How the model should choose capabilities ('auto', 'required', or specific capability name).
        mcp_servers: List of MCP server configurations to load tools from
            (requires nimbus[mcp]). Each config should contain server connection details.
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

    Example (With nimbus[capabilities]):
        >>> # Using capabilities/tools (requires nimbus[capabilities])
        >>> from nimbus.capabilities import LocalFunctionCapability
        >>>
        >>> def get_weather(location: str) -> str:
        ...     return f"Weather for {location}"
        >>>
        >>> capability = LocalFunctionCapability(
        ...     func=get_weather,
        ...     name="get_weather",
        ...     description="Get weather for a location"
        ... )
        >>>
        >>> request = CompletionRequest(
        ...     messages=[UserMessage(content="What's the weather in NYC?")],
        ...     model="gpt-4",
        ...     capabilities=[capability],
        ...     capability_choice="auto"
        ... )
        >>> len(request.capabilities)
        1

    Example (With nimbus[mcp]):
        >>> # Using MCP servers (requires nimbus[mcp])
        >>> request = CompletionRequest(
        ...     messages=[UserMessage(content="What's the weather in NYC?")],
        ...     model="gpt-4",
        ...     mcp_servers=[
        ...         {
        ...             "name": "weather_server",
        ...             "command": "mcp-server-weather",
        ...             "args": ["--port", "8080"]
        ...         }
        ...     ]
        ... )
        >>> len(request.mcp_servers)
        1
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
    # List of CapabilityInterface (requires nimbus[capabilities])
    capabilities: list[Any] | None = None
    capability_choice: str | None = None  # "auto", "required", or specific capability name
    # MCP server configurations (requires nimbus[mcp])
    mcp_servers: list[dict[str, Any]] | None = None
    response_format: dict[str, Any] | None = None
    response_schema: type[BaseModel] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("capability_choice")
    @classmethod
    def validate_capability_choice(cls, v: str | None) -> str | None:
        """Validate capability_choice is 'auto', 'required', or a capability name."""
        if v is not None and v not in ["auto", "required"]:
            # If not a standard value, assume it's a specific capability name
            # Capability names should be non-empty strings
            if not isinstance(v, str) or not v.strip():
                raise ValueError(
                    "capability_choice must be 'auto', 'required', or a non-empty capability name"
                )
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate that either messages or prompt is provided, but not both."""
        if self.messages is None and self.prompt is None:
            raise ValueError("Either 'messages' or 'prompt' must be provided")
        if self.messages is not None and self.prompt is not None:
            raise ValueError("Cannot provide both 'messages' and 'prompt' - use one or the other")


class CompletionResponse(BaseModel):
    """Response from model completion.

    Represents the response from an LLM provider, including the generated content,
    token usage, optional structured output, and tool calls.

    Attributes:
        id: Unique identifier for the response.
        model: Model identifier that generated the response.
        provider: Provider name (e.g., 'openai', 'anthropic', 'bedrock').
        content: The generated text content.
        structured_output: Parsed structured output if response_schema was provided.
        role: Role of the responder (typically 'assistant').
        finish_reason: Reason the generation stopped ('stop', 'length', 'tool_calls', etc.).
        usage: Token usage statistics.
        tool_calls: List of tool calls requested by the model (requires nimbus[capabilities]).
        created_at: Timestamp when the response was created.
        metadata: Additional metadata about the response.

    Example (Basic Response):
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

    Example (With Tool Calls):
        >>> from nimbus.capabilities.capability_models import CapabilityCall
        >>> response = CompletionResponse(
        ...     model="gpt-4",
        ...     provider="openai",
        ...     content="",
        ...     role="assistant",
        ...     finish_reason="tool_calls",
        ...     usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
        ...     tool_calls=[
        ...         CapabilityCall(
        ...             id="call_123",
        ...             name="weather.get_current",
        ...             arguments={"location": "San Francisco"}
        ...         )
        ...     ]
        ... )
        >>> response.has_tool_calls()
        True
        >>> # Execute tool calls (requires nimbus[capabilities])
        >>> from nimbus.capabilities.registry import CapabilityRegistry
        >>> registry = CapabilityRegistry.get_instance()
        >>> results = await response.execute_tool_calls(registry)
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    model: str
    provider: str
    content: str
    structured_output: BaseModel | None = None
    role: str = "assistant"
    finish_reason: str
    usage: TokenUsage
    tool_calls: list[Any] | None = None  # List of CapabilityCall (requires nimbus[capabilities])
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

    def has_tool_calls(self) -> bool:
        """Check if the response contains tool calls.

        Returns:
            True if the response contains one or more tool calls, False otherwise.

        Example:
            >>> from nimbus.capabilities.capability_models import CapabilityCall
            >>> response = CompletionResponse(
            ...     model="gpt-4",
            ...     provider="openai",
            ...     content="",
            ...     finish_reason="tool_calls",
            ...     usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            ...     tool_calls=[
            ...         CapabilityCall(id="call_1", name="get_weather", arguments={"city": "NYC"})
            ...     ]
            ... )
            >>> response.has_tool_calls()
            True
            >>>
            >>> response_no_tools = CompletionResponse(
            ...     model="gpt-4",
            ...     provider="openai",
            ...     content="Hello",
            ...     finish_reason="stop",
            ...     usage=TokenUsage(prompt_tokens=5, completion_tokens=2, total_tokens=7)
            ... )
            >>> response_no_tools.has_tool_calls()
            False
        """
        return self.tool_calls is not None and len(self.tool_calls) > 0

    async def execute_tool_calls(
        self,
        registry: "CapabilityRegistry",
    ) -> list["CapabilityResult"]:
        """Execute all tool calls using the provided capability registry.

        Executes all tool calls in the response using the provided registry
        and returns a list of CapabilityResult objects. This method is async to
        support asynchronous capability execution.

        Args:
            registry: CapabilityRegistry instance to use for executing capabilities

        Returns:
            List of CapabilityResult objects containing execution results

        Raises:
            ImportError: If nimbus[capabilities] is not installed
            ValueError: If the response has no tool calls

        Example:
            >>> from nimbus.capabilities.registry import CapabilityRegistry
            >>> from nimbus.capabilities.capability_models import CapabilityCall
            >>>
            >>> # Create response with tool calls
            >>> response = CompletionResponse(
            ...     model="gpt-4",
            ...     provider="openai",
            ...     content="",
            ...     finish_reason="tool_calls",
            ...     usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
            ...     tool_calls=[
            ...         CapabilityCall(
            ...             id="call_123",
            ...             name="weather.get_current",
            ...             arguments={"location": "San Francisco"}
            ...         )
            ...     ]
            ... )
            >>>
            >>> # Execute tool calls
            >>> registry = CapabilityRegistry.get_instance()
            >>> results = await response.execute_tool_calls(registry)
            >>> for result in results:
            ...     print(f"{result.name}: {result.result}")
        """
        # Import here to avoid circular dependency and allow optional capabilities
        try:
            from nimbus.capabilities.capability_models import CapabilityResult
        except ImportError as e:
            raise ImportError(
                "Tool call execution requires nimbus[capabilities]. "
                "Install with: pip install nimbus[capabilities]"
            ) from e

        if not self.has_tool_calls():
            raise ValueError("Response has no tool calls to execute")

        results: list[CapabilityResult] = []

        for tool_call in self.tool_calls:  # type: ignore
            try:
                # Execute the capability asynchronously
                result = await registry.aexecute(
                    capability_name=tool_call.name,
                    arguments=tool_call.arguments,
                    tool_call_id=tool_call.id,
                    return_raw=True,
                )

                # Create successful result
                results.append(
                    CapabilityResult(
                        capability_call_id=tool_call.id,
                        name=tool_call.name,
                        result=result,
                        error=None,
                    )
                )

            except Exception as e:
                # Create error result
                results.append(
                    CapabilityResult(
                        capability_call_id=tool_call.id,
                        name=tool_call.name,
                        result=None,
                        error=str(e),
                    )
                )

        return results


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
