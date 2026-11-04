"""Completion request and response models for Skye.

This module provides dataclass models for LLM completion requests and responses,
including support for streaming, structured outputs, and token usage tracking.

Example:
    >>> from skye.base.completion import CompletionRequest, TokenUsage
    >>> from skye.base.messages import UserMessage
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

from skye.base.exceptions import ValidationError
from skye.base.messages import CapabilityMessage, SkyeMessage
from skye.base.validated import Validated, field, validated

if TYPE_CHECKING:
    from skye.base.capability_schema import CapabilityRegistryLike


@validated
class CapabilityCall(Validated):
    """Represents a capability call request from an LLM.

    When an LLM decides to invoke a capability, it generates a capability call
    containing the capability name and arguments. This model represents
    that request in a provider-agnostic format.

    Lives in base so provider adapters in ``models`` need no import of the tools
    Component (Requirement 2); ``skye.tools.capability_models`` re-exports it.

    Attributes:
        id: Unique identifier for this capability call (from the provider)
        name: Name of the capability to invoke
        arguments: Dictionary of arguments to pass to the capability

    Example:
        >>> capability_call = CapabilityCall(
        ...     id="call_123",
        ...     name="weather.get_current",
        ...     arguments={"location": "San Francisco"}
        ... )
    """

    id: str = field(description="Unique identifier for this capability call from the provider")
    name: str = field(description="Name of the capability to invoke")
    arguments: dict[str, Any] = field(
        default_factory=dict, description="Arguments to pass to the capability"
    )


@validated
class ExecutableCapabilityCall(Validated):
    """A capability call that can execute itself.

    Wraps a capability call (id, name, arguments) with the capability
    implementation, allowing direct execution. Lives in base so that
    ``CompletionResponse.get_capability_calls`` needs no import of the tools
    Component (Requirement 2); ``skye.tools.capability_models`` re-exports it.
    """

    id: str = field(description="Unique identifier for this capability call")
    name: str = field(description="Name of the capability to invoke")
    arguments: dict[str, Any] = field(
        default_factory=dict, description="Arguments to pass to the capability"
    )
    capability: Any | None = field(
        default=None, description="The actual capability implementation"
    )

    def execute(self, **override_arguments: Any) -> CapabilityMessage:
        """Execute the capability and return a CapabilityMessage.

        ``override_arguments`` are merged over the LLM-provided arguments.
        Failures are reported as an error CapabilityMessage, never raised.
        """
        import json

        if self.capability is None:
            return CapabilityMessage(
                content=f"Error: Capability '{self.name}' not found",
                capability_id=self.id,
                capability_name=self.name,
            )
        try:
            final_arguments = {**self.arguments, **override_arguments}
            result = self.capability.execute(**final_arguments)
            if isinstance(result, str):
                content = result
            elif isinstance(result, (dict, list)):
                content = json.dumps(result)
            else:
                content = str(result)
            return CapabilityMessage(
                content=content, capability_id=self.id, capability_name=self.name
            )
        except Exception as e:
            return CapabilityMessage(
                content=f"Error: {str(e)}",
                capability_id=self.id,
                capability_name=self.name,
            )


@validated
class TokenUsage(Validated):
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


@validated
class CompletionRequest(Validated):
    """Request for model completion.

    Represents a request to an LLM provider with all necessary parameters
    including messages, model configuration, and optional structured output schema.

    **Polymorphic Input Support:**
    - **Base Skye**: Use `messages` parameter with list of SkyeMessage objects
    - **With skyeai[prompts]**: Use `prompt` parameter with template name and variables

    The interface accepts either messages OR prompt, making it work seamlessly
    with or without the optional prompts package installed.

    Attributes:
        messages: List of messages in the conversation (base Skye).
        prompt: Prompt template name (requires skyeai[prompts]).
        prompt_variables: Variables for prompt template rendering.
        model: Model identifier (e.g., 'gpt-4', 'claude-3-sonnet').
        temperature: Sampling temperature (0.0-2.0). Higher values make output more random.
        max_tokens: Maximum number of tokens to generate.
        top_p: Nucleus sampling parameter (0.0-1.0).
        stop: List of sequences that will stop generation.
        stream: Whether to stream the response.
        capabilities: List of capabilities available to the model
            (requires skyeai[capabilities]).
        capability_choice: How the model should choose capabilities ('auto', 'required', or specific capability name).
        mcp_servers: List of MCP server configurations to load capabilities from
            (requires skyeai[mcp]). Each config should contain server connection details.
        response_format: Format specification for structured outputs.
        response_schema: Class that describes the structured output (for example a pydantic model
            or a dataclass); the adapter validates the reply with it.
        metadata: Additional metadata for the request.

    Example (Base Skye):
        >>> from skye.base.messages import UserMessage
        >>> request = CompletionRequest(
        ...     messages=[UserMessage(content="What is 2+2?")],
        ...     model="gpt-4",
        ...     temperature=0.7
        ... )
        >>> request.model
        'gpt-4'

    Example (With skyeai[prompts]):
        >>> # Using prompt templates (requires skyeai[prompts])
        >>> request = CompletionRequest(
        ...     prompt="math_solver",
        ...     prompt_variables={"problem": "What is 2+2?"},
        ...     model="gpt-4"
        ... )
        >>> request.prompt
        'math_solver'

    Example (With skyeai[capabilities]):
        >>> # Using capabilities (requires skyeai[capabilities])
        >>> from skye.tools import LocalFunctionCapability
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

    Example (With skyeai[mcp]):
        >>> # Using MCP servers (requires skyeai[mcp])
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
    messages: list[SkyeMessage] | None = None
    prompt: str | None = None  # Template name (requires skyeai[prompts])
    prompt_variables: dict[str, Any] = field(default_factory=dict)

    model: str
    temperature: float = field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = field(default=None, gt=0)
    top_p: float = field(default=1.0, ge=0.0, le=1.0)
    stop: list[str] | None = None
    stream: bool = False
    # Capabilities can be provided as:
    # 1. List of CapabilityInterface objects (direct, no registry needed)
    # 2. CapabilityRegistry instance (enables search/discovery)
    capabilities: Any | None = None  # list of CapabilityInterface, or a CapabilityRegistry
    capability_choice: str | None = None  # "auto", "required", or specific capability name
    # MCP server configurations (requires skyeai[mcp])
    mcp_servers: list[dict[str, Any]] | None = None
    response_format: dict[str, Any] | None = None
    response_schema: type | None = None  # a dataclass (the standard); a user's pydantic model also works; base imports neither
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the fields, then that exactly one of messages and prompt is provided."""
        super().__post_init__()
        choice = self.capability_choice
        if choice is not None and choice not in ("auto", "required") and not choice.strip():
            raise ValidationError(
                "capability_choice must be 'auto', 'required', or a non-empty capability name",
                field="capability_choice",
                value=choice,
            )
        if self.messages is None and self.prompt is None:
            raise ValidationError(
                "Either 'messages' or 'prompt' must be provided", field="messages", value=None
            )
        if self.messages is not None and self.prompt is not None:
            raise ValidationError(
                "Cannot provide both 'messages' and 'prompt' - use one or the other",
                field="prompt",
                value=self.prompt,
            )


@validated
class CompletionResponse(Validated):
    """Response from model completion.

    Represents the response from an LLM provider, including the generated content,
    token usage, optional structured output, and capability calls.

    Attributes:
        id: Unique identifier for the response.
        model: Model identifier that generated the response.
        provider: Provider name (e.g., 'openai', 'anthropic', 'bedrock').
        content: The generated text content.
        structured_output: Parsed structured output if response_schema was provided.
        role: Role of the responder (typically 'assistant').
        finish_reason: Reason the generation stopped ('stop', 'length', 'capability_calls', etc.).
        usage: Token usage statistics.
        capability_calls: List of capability calls requested by the model (requires skyeai[capabilities]).
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

    Example (With Capability Calls):
        >>> from skye.tools.capability_models import CapabilityCall
        >>> response = CompletionResponse(
        ...     model="gpt-4",
        ...     provider="openai",
        ...     content="",
        ...     role="assistant",
        ...     finish_reason="capability_calls",
        ...     usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
        ...     capability_calls=[
        ...         CapabilityCall(
        ...             id="call_123",
        ...             name="weather.get_current",
        ...             arguments={"location": "San Francisco"}
        ...         )
        ...     ]
        ... )
        >>> response.has_capability_calls()
        True
        >>> # Execute capability calls (requires skyeai[capabilities])
        >>> from skye.tools.registry import CapabilityRegistry
        >>> registry = CapabilityRegistry.get_instance()
        >>> results = await response.execute_capability_calls(registry)
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    model: str
    provider: str
    content: str
    structured_output: Any | None = None  # an instance of response_schema
    role: str = "assistant"
    finish_reason: str
    usage: TokenUsage
    capability_calls: list[Any] | None = None  # List of CapabilityCall (requires skyeai[capabilities])
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Internal: the capabilities of the request, kept to execute the calls; not an argument
    _capabilities: list[Any] | None = field(default=None, init=False, repr=False, compare=False)

    def get_output(self) -> Any:
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
            >>>             >>> @dataclass
            ... class Person:
            ...     name: str
            >>> person = Person(name="Alice")
            >>> response.structured_output = person
            >>> response.get_output().name
            'Alice'
        """
        return self.structured_output if self.structured_output else self.content

    def to_message(self) -> "SkyeMessage":
        """Convert the response to an AssistantMessage for conversation continuation.

        Returns:
            AssistantMessage containing the response content and capability calls.

        Example:
            >>> response = CompletionResponse(
            ...     model="gpt-4",
            ...     provider="openai",
            ...     content="Let me check that for you.",
            ...     finish_reason="capability_calls",
            ...     usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            ...     capability_calls=[
            ...         CapabilityCall(id="call_1", name="get_weather", arguments={"city": "NYC"})
            ...     ]
            ... )
            >>> msg = response.to_message()
            >>> msg.role
            'assistant'
            >>> len(msg.capability_calls)
            1
        """
        from skye.base.messages import AssistantMessage

        # Convert CapabilityCall objects to dicts for AssistantMessage
        capability_calls_dicts = []
        if self.capability_calls:
            for call in self.capability_calls:
                capability_calls_dicts.append({
                    "id": call.id,
                    "name": call.name,
                    "arguments": call.arguments
                })

        return AssistantMessage(
            content=self.content,
            capability_calls=capability_calls_dicts
        )

    def has_capability_calls(self) -> bool:
        """Check if the response contains capability calls.

        Returns:
            True if the response contains one or more capability calls, False otherwise.

        Example:
            >>> from skye.tools.capability_models import CapabilityCall
            >>> response = CompletionResponse(
            ...     model="gpt-4",
            ...     provider="openai",
            ...     content="",
            ...     finish_reason="capability_calls",
            ...     usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            ...     capability_calls=[
            ...         CapabilityCall(id="call_1", name="get_weather", arguments={"city": "NYC"})
            ...     ]
            ... )
            >>> response.has_capability_calls()
            True
            >>>
            >>> response_no_capabilities = CompletionResponse(
            ...     model="gpt-4",
            ...     provider="openai",
            ...     content="Hello",
            ...     finish_reason="stop",
            ...     usage=TokenUsage(prompt_tokens=5, completion_tokens=2, total_tokens=7)
            ... )
            >>> response_no_capabilities.has_capability_calls()
            False
        """
        return self.capability_calls is not None and len(self.capability_calls) > 0
    
    def get_capability_calls(self) -> list[ExecutableCapabilityCall]:
        """Get capability calls as executable objects.

        Returns:
            List of ExecutableCapabilityCall objects that can execute themselves.

        Example:
            >>> response = client.complete(
            ...     messages=[UserMessage(content="What's the weather in SF?")],
            ...     model="gpt-4",
            ...     capabilities=[get_weather]
            ... )
            >>> if response.has_capability_calls():
            ...     for capability in response.get_capability_calls():
            ...         msg = capability.execute()  # Returns CapabilityMessage
        """
        if not self.has_capability_calls():
            return []
        
        # Create executable wrappers
        executable_calls = []
        for call in self.capability_calls or []:
            # Find the matching capability
            capability = None
            if self._capabilities:
                for cap in self._capabilities:
                    # Get capability name from schema
                    try:
                        schema = cap.get_schema()
                        if schema.name == call.name:
                            capability = cap
                            break
                    except Exception:
                        # If get_schema fails, try direct name attribute
                        if hasattr(cap, 'name') and cap.name == call.name:
                            capability = cap
                            break
            
            executable_calls.append(
                ExecutableCapabilityCall(
                    id=call.id,
                    name=call.name,
                    arguments=call.arguments,
                    capability=capability
                )
            )
        
        return executable_calls

    async def execute_capability_calls(
        self,
        registry: "CapabilityRegistryLike | None" = None,
        argument_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> list["SkyeMessage"]:
        """Execute all capability calls and return CapabilityMessage objects.

        Executes all capability calls in the response and returns a list of 
        CapabilityMessage objects that can be directly added to the conversation 
        messages for the next completion request.

        The method will use capabilities from the original request if available,
        otherwise it will use the provided registry to look them up.

        Args:
            registry: Optional CapabilityRegistry instance. If not provided, uses
                capabilities from the original request.
            argument_overrides: Optional dict mapping capability call IDs to argument overrides.
                Overrides will be merged with LLM-provided arguments, with overrides taking precedence.

        Returns:
            List of CapabilityMessage objects ready to be added to conversation

        Raises:
            ImportError: If skyeai[capabilities] is not installed
            ValueError: If the response has no capability calls
            ValueError: If no registry provided and capabilities not available from request

        Example:
            >>> from skye.base.messages import UserMessage
            >>>
            >>> # Initial request with capabilities
            >>> response = client.complete(
            ...     messages=[UserMessage(content="What's the weather in San Francisco?")],
            ...     model="gpt-4",
            ...     capabilities=[weather_capability]
            ... )
            >>>
            >>> # Execute capability calls (no registry needed!)
            >>> if response.has_capability_calls():
            ...     capability_messages = await response.execute_capability_calls()
            ...     
            ...     # Continue conversation with results
            ...     final_response = client.complete(
            ...         messages=[
            ...             UserMessage(content="What's the weather in San Francisco?"),
            ...             response.to_message(),
            ...             *capability_messages  # Spread the capability messages
            ...         ],
            ...         model="gpt-4"
            ...     )
            >>>
            >>> # Execute with argument overrides
            >>> if response.has_capability_calls():
            ...     overrides = {
            ...         "call_123": {"location": "New York"}  # Override location
            ...     }
            ...     capability_messages = await response.execute_capability_calls(
            ...         argument_overrides=overrides
            ...     )
            >>>
            >>> # Or use a registry if capabilities weren't in the request
            >>> from skye.tools.registry import CapabilityRegistry
            >>> registry = CapabilityRegistry.get_instance()
            >>> capability_messages = await response.execute_capability_calls(registry)
        """
        # Import here to avoid circular dependency and allow optional capabilities
        try:
            from skye.base.messages import CapabilityMessage
        except ImportError as e:
            raise ImportError(
                "Capability call execution requires skyeai[capabilities]. "
                "Install with: pip install skyeai[capabilities]"
            ) from e

        if not self.has_capability_calls():
            raise ValueError("Response has no capability calls to execute")

        import json
        messages: list[SkyeMessage] = []

        # Build capability lookup map
        capability_map: dict[str, Any] = {}
        if self._capabilities:
            # Use capabilities from the original request
            for cap in self._capabilities:
                try:
                    schema = cap.get_schema()
                    capability_map[schema.name] = cap
                except Exception:
                    # If get_schema fails, try direct name attribute
                    if hasattr(cap, 'name'):
                        capability_map[cap.name] = cap
        elif registry:
            # Use registry to look up capabilities
            for capability_call in self.capability_calls:  # type: ignore
                cap = registry.get(capability_call.name)
                if cap:
                    capability_map[capability_call.name] = cap
        else:
            raise ValueError(
                "No capabilities available. Either pass capabilities in the request "
                "or provide a CapabilityRegistry instance."
            )

        for capability_call in self.capability_calls:  # type: ignore
            try:
                # Merge LLM arguments with overrides if provided
                final_arguments = capability_call.arguments.copy()
                if argument_overrides and capability_call.id in argument_overrides:
                    final_arguments.update(argument_overrides[capability_call.id])

                # Get the capability
                capability = capability_map.get(capability_call.name)
                if not capability:
                    raise ValueError(f"Capability '{capability_call.name}' not found")

                # Execute the capability asynchronously
                result = await capability.aexecute(**final_arguments)

                # Format result as string
                if isinstance(result, str):
                    content = result
                elif isinstance(result, (dict, list)):
                    content = json.dumps(result)
                else:
                    content = str(result)

                # Create capability message
                messages.append(
                    CapabilityMessage(
                        content=content,
                        capability_id=capability_call.id,
                        capability_name=capability_call.name,
                    )
                )

            except Exception as e:
                # Create error message
                messages.append(
                    CapabilityMessage(
                        content=f"Error: {str(e)}",
                        capability_id=capability_call.id,
                        capability_name=capability_call.name,
                    )
                )

        return messages


@validated
class StreamChunk(Validated):
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
