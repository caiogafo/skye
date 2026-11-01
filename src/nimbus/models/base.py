"""Base provider classes for model and embedding providers.

This module provides abstract base classes that all provider implementations
must inherit from. These classes handle common functionality like lazy client
initialization, error handling, request/response transformation, and retry logic.

## Provider Transformation Architecture

All provider-specific transformation logic MUST be encapsulated within provider
client classes. This ensures the core library remains completely provider-agnostic
and makes it easy to add new providers without modifying core code.

### Transformation Responsibilities

Each provider client handles ALL transformations for that provider:
- Message format conversion (Nimbus messages → provider format)
- Capability format conversion (Nimbus capabilities → provider capabilities)
- Capability call extraction (provider response → Nimbus CapabilityCall objects)
- Parameter mapping and provider-specific options

### Core Library Provider Agnosticism

Core library modules MUST NOT contain provider-specific code:
- src/nimbus/router/ - Router and routing logic
- src/nimbus/tools/ - Capability system
- src/nimbus/base/completion.py - Completion models
- src/nimbus/base/messages.py - Message models

### Adding a New Provider

To add a new provider, you only need to:
1. Create a new provider class inheriting from BaseModelProvider
2. Implement all required transformation methods
3. No changes to core library code required

See docs/provider-transformation-architecture.md for detailed documentation.
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, AsyncIterator

from nimbus.base.backend_select import Selection, select_impl
from nimbus.base.completion import CompletionRequest, CompletionResponse, StreamChunk
from nimbus.base.exceptions import ProviderError
from nimbus.base.interfaces.model import ModelInterface
from nimbus.base.interfaces.vector_encoder import VectorEncoderInterface
from nimbus.base.health import HealthMetrics
from nimbus.models.transport.retry import with_retry


class BaseModelProvider(ModelInterface, ABC):
    """Abstract base class for model providers.
    
    This class provides common functionality for all LLM provider implementations,
    including lazy client initialization, error handling, and a template method
    pattern for request/response transformation.
    
    **Provider-Specific Transformation Encapsulation:**
    
    All provider-specific transformation logic MUST be contained within the
    provider client class. This ensures the core library remains provider-agnostic
    and makes it easy to add new providers without modifying core code.
    
    Each provider client handles ALL transformations for that provider:
    - Message format conversion (Nimbus messages → provider format)
    - Capability format conversion (Nimbus capabilities → provider capabilities)
    - Capability call extraction (provider response → Nimbus CapabilityCall objects)
    - Parameter mapping and provider-specific options
    
    Subclasses must implement:
    - _initialize_client(): Create the provider-specific client
    - _transform_request(): Convert CompletionRequest to provider format
    - _transform_response(): Convert provider response to CompletionResponse
    - _transform_stream_chunk(): Convert provider stream chunk to StreamChunk
    - _transform_messages(): Convert Nimbus messages to provider format
    - _transform_capabilities(): Convert Nimbus capabilities to provider format
    - _extract_capability_calls(): Extract capability calls from provider response
    - _call_provider(): Make the actual provider API call
    - _call_provider_stream(): Make streaming provider API call
    - get_model_info(): Return model metadata
    
    Example:
        >>> class OpenAIProvider(BaseModelProvider):
        ...     def _initialize_client(self):
        ...         import openai
        ...         return openai.OpenAI(api_key=self.config["api_key"])
        ...
        ...     def _transform_request(self, request):
        ...         # Use internal transformation methods
        ...         return {
        ...             "model": request.model,
        ...             "messages": self._transform_messages(request.messages),
        ...             "tools": self._transform_capabilities(request.capabilities)
        ...         }
        ...
        ...     def _transform_messages(self, messages):
        ...         # OpenAI-specific message transformation
        ...         return [{"role": m.role, "content": m.content} for m in messages]
        ...
        ...     def _transform_capabilities(self, capabilities):
        ...         # OpenAI-specific capability transformation
        ...         return [{"type": "function", "function": {...}} for c in capabilities]
        ...
        ...     def _extract_capability_calls(self, response):
        ...         # Extract capability calls from OpenAI response
        ...         return [CapabilityCall(...) for tc in response.capability_calls]
        ...
        ...     # ... implement other abstract methods
    """
    
    #: Backend name in ``SDK_REFERENCE`` / ``NIMBUS_<BACKEND>_IMPL``; None opts out of selection.
    impl_backend: str | None = None

    def __init__(self, model: str | None = None, router: Any | None = None, **config: Any) -> None:
        """Initialize base provider with configuration.
        
        Args:
            model: Model identifier (optional, can be provided in request)
            router: Model router for load balancing (optional)
            **config: Provider-specific configuration parameters
        """
        if model is not None and router is not None:
            raise ValueError("Cannot provide both 'model' and 'router'")
        
        self.model = model
        self.router = router
        self.config = config
        # Backend selection (Req 17): decided once per instance. Every adapter today only has
        # the SDK path, so "sdk" is the sole available implementation.
        self.selection: Selection | None = (
            select_impl(self.impl_backend, available=("sdk",)) if self.impl_backend else None
        )
        self._client = None
        self.health_metrics = HealthMetrics()
    
    @property
    def default_model(self) -> str | None:
        """Get the default model for this provider.
        
        Returns:
            The default model identifier, or None if not set
        """
        return self.model
    
    @property
    def client(self) -> Any:
        """Lazy-load the provider client.
        
        The client is only initialized when first accessed, reducing startup
        time and memory usage.
        
        Returns:
            The provider-specific client instance
        """
        if self._client is None:
            self._client = self._initialize_client()
        return self._client
    
    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the provider-specific client.
        
        This method should create and return the provider's SDK client.
        It will be called lazily when the client is first accessed.
        
        Returns:
            The initialized provider client
            
        Example:
            >>> def _initialize_client(self):
            ...     import openai
            ...     return openai.OpenAI(api_key=self.config["api_key"])
        """
        pass
    
    @abstractmethod
    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """Transform CompletionRequest to provider-specific format.
        
        Args:
            request: The nimbus CompletionRequest
            
        Returns:
            Dictionary in provider-specific format
            
        Example:
            >>> def _transform_request(self, request):
            ...     return {
            ...         "model": request.model,
            ...         "messages": [{"role": "user", "content": "..."}],
            ...         "temperature": request.temperature
            ...     }
        """
        pass
    
    @abstractmethod
    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform provider response to CompletionResponse.
        
        Args:
            response: The provider-specific response object
            
        Returns:
            CompletionResponse in nimbus format
            
        Example:
            >>> def _transform_response(self, response):
            ...     return CompletionResponse(
            ...         id=response.id,
            ...         model=response.model,
            ...         provider="openai",
            ...         content=response.choices[0].message.content,
            ...         finish_reason=response.choices[0].finish_reason,
            ...         usage=TokenUsage(...)
            ...     )
        """
        pass
    
    @abstractmethod
    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform provider stream chunk to StreamChunk.
        
        Args:
            chunk: The provider-specific stream chunk
            
        Returns:
            StreamChunk in nimbus format
            
        Example:
            >>> def _transform_stream_chunk(self, chunk):
            ...     return StreamChunk(
            ...         id=chunk.id,
            ...         delta=chunk.choices[0].delta.content or "",
            ...         finish_reason=chunk.choices[0].finish_reason,
            ...         index=chunk.choices[0].index
            ...     )
        """
        pass
    
    @abstractmethod
    def _call_provider(self, request: dict[str, Any]) -> Any:
        """Make the actual provider API call.
        
        Args:
            request: Provider-specific request dictionary
            
        Returns:
            Provider-specific response object
            
        Example:
            >>> def _call_provider(self, request):
            ...     return self.client.chat.completions.create(**request)
        """
        pass
    
    @abstractmethod
    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        """Make streaming provider API call.
        
        Args:
            request: Provider-specific request dictionary
            
        Yields:
            Provider-specific stream chunks
            
        Example:
            >>> def _call_provider_stream(self, request):
            ...     return self.client.chat.completions.create(**request)
        """
        pass
    
    @abstractmethod
    def _transform_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Transform Nimbus messages to provider-specific format.
        
        This method encapsulates all provider-specific message transformation logic.
        Each provider has different requirements for message format, and this method
        handles those differences.
        
        **Provider-Specific Responsibilities:**
        - Convert Nimbus message objects to provider's message format
        - Handle system messages (some providers require separate handling)
        - Handle capability messages and results
        - Handle multimodal content (images, etc.)
        - Map message roles to provider-specific roles
        
        Args:
            messages: List of Nimbus message objects (UserMessage, AssistantMessage, etc.)
            
        Returns:
            List of dictionaries in provider-specific message format
            
        Example (OpenAI):
            >>> def _transform_messages(self, messages):
            ...     return [
            ...         {"role": msg.role, "content": msg.content}
            ...         for msg in messages
            ...     ]
        
        Example (Bedrock):
            >>> def _transform_messages(self, messages):
            ...     return [
            ...         {"role": msg.role, "content": [{"text": msg.content}]}
            ...         for msg in messages
            ...     ]
        """
        pass
    
    @abstractmethod
    def _transform_capabilities(self, capabilities: list[Any]) -> list[dict[str, Any]]:
        """Transform Nimbus capabilities to provider-specific capability format.
        
        This method encapsulates all provider-specific capability transformation
        logic. Each provider has different requirements for capability definitions, and this
        method handles those differences.
        
        **Provider-Specific Responsibilities:**
        - Convert CapabilityInterface objects to provider's capability format
        - Generate proper JSON Schema for capability parameters
        - Handle provider-specific capability metadata
        - Map capability names and descriptions appropriately
        
        Args:
            capabilities: List of CapabilityInterface objects
            
        Returns:
            List of dictionaries in provider-specific capability format
            
        Example (OpenAI):
            >>> def _transform_capabilities(self, capabilities):
            ...     return [
            ...         {
            ...             "type": "function",
            ...             "function": {
            ...                 "name": cap.get_schema().name,
            ...                 "description": cap.get_schema().description,
            ...                 "parameters": cap.get_schema().parameters
            ...             }
            ...         }
            ...         for cap in capabilities
            ...     ]
        
        Example (Bedrock):
            >>> def _transform_capabilities(self, capabilities):
            ...     return [
            ...         {
            ...             "toolSpec": {
            ...                 "name": cap.get_schema().name,
            ...                 "description": cap.get_schema().description,
            ...                 "inputSchema": {"json": cap.get_schema().parameters}
            ...             }
            ...         }
            ...         for cap in capabilities
            ...     ]
        """
        pass
    
    @abstractmethod
    def _extract_capability_calls(self, response: Any) -> list[Any] | None:
        """Extract capability calls from provider response.
        
        This method encapsulates provider-specific logic for extracting capability
        calls from the provider's response and converting them to Nimbus CapabilityCall
        objects.
        
        **Provider-Specific Responsibilities:**
        - Parse capability calls from provider response format
        - Extract capability call ID, name, and arguments
        - Convert to CapabilityCall objects
        - Handle JSON parsing of arguments if needed
        - Return None if no capability calls present
        
        Args:
            response: Provider-specific response object
            
        Returns:
            List of CapabilityCall objects, or None if no capability calls
            
        Example (OpenAI):
            >>> def _extract_capability_calls(self, response):
            ...     if not hasattr(response.choices[0].message, "capability_calls"):
            ...         return None
            ...     
            ...     from nimbus.tools.capability_models import CapabilityCall
            ...     import json
            ...     
            ...     capability_calls = []
            ...     for tc in response.choices[0].message.capability_calls:
            ...         capability_calls.append(
            ...             CapabilityCall(
            ...                 id=tc.id,
            ...                 name=tc.function.name,
            ...                 arguments=json.loads(tc.function.arguments)
            ...             )
            ...         )
            ...     return capability_calls
        
        Example (Bedrock):
            >>> def _extract_capability_calls(self, response):
            ...     capability_calls = []
            ...     for block in response["output"]["message"].get("content", []):
            ...         if "toolUse" in block:
            ...             tool_use = block["toolUse"]
            ...             capability_calls.append(
            ...                 CapabilityCall(
            ...                     id=tool_use["toolUseId"],
            ...                     name=tool_use["name"],
            ...                     arguments=tool_use["input"]
            ...                 )
            ...             )
            ...     return capability_calls if capability_calls else None
        """
        pass

    def parse_capability_calls(self, response: Any) -> list[Any]:
        """Parse capability calls from provider response using provider-specific logic.
        
        This is a public interface that delegates to the provider-specific
        _extract_capability_calls method. It provides a consistent interface
        for the CapabilityCallHandler to use.
        
        Args:
            response: Provider-specific response object (CompletionResponse or raw response)
            
        Returns:
            List of CapabilityCall objects (empty list if none found)
            
        Example:
            >>> provider = OpenAIProvider(api_key="...")
            >>> response = provider.complete(request)
            >>> capability_calls = provider.parse_capability_calls(response)
        """
        # If it's a CompletionResponse and already has capability_calls, return them
        if hasattr(response, 'capability_calls') and response.capability_calls is not None:
            return response.capability_calls
        
        # Handle both CompletionResponse and raw provider response
        if hasattr(response, 'metadata') and 'raw_response' in response.metadata:
            # Use raw response if available in metadata
            raw_response = response.metadata['raw_response']
        else:
            # Assume it's already a raw response
            raw_response = response
            
        capability_calls = self._extract_capability_calls(raw_response)
        return capability_calls or []

    @abstractmethod
    def format_capability_results(self, results: list[Any]) -> list[dict[str, Any]]:
        """Format capability results for sending back to provider.
        
        This method encapsulates provider-specific logic for formatting
        CapabilityResult objects into the format expected by the provider
        for continuing the conversation.
        
        **Provider-Specific Responsibilities:**
        - Convert CapabilityResult objects to provider message format
        - Handle both successful results and errors
        - Format JSON content appropriately
        - Include required provider-specific fields
        
        Args:
            results: List of CapabilityResult objects to format
            
        Returns:
            List of formatted result dictionaries in provider format
            
        Example (OpenAI):
            >>> def format_capability_results(self, results):
            ...     formatted = []
            ...     for result in results:
            ...         content = json.dumps({"error": result.error}) if result.error else json.dumps(result.result)
            ...         formatted.append({
            ...             "tool_call_id": result.capability_call_id,
            ...             "role": "tool",
            ...             "content": content
            ...         })
            ...     return formatted
        
        Example (Bedrock):
            >>> def format_capability_results(self, results):
            ...     formatted = []
            ...     for result in results:
            ...         result_data = {"error": result.error} if result.error else result.result
            ...         formatted.append({
            ...             "toolResult": {
            ...                 "toolUseId": result.capability_call_id,
            ...                 "content": [{"json": result_data}]
            ...             }
            ...         })
            ...     return formatted
        """
        pass
    
    def complete(
        self,
        messages: list[Any] | str | CompletionRequest | None = None,
        model: str | None = None,
        router: Any | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Execute synchronous completion.
        
        Supports both boto3-style direct calls and CompletionRequest objects.
        
        Boto3-style usage:
            >>> # With specific model
            >>> response = client.complete(
            ...     messages=[UserMessage("Hello")],
            ...     model="gpt-4"
            ... )
            >>>
            >>> # With router for load balancing
            >>> response = client.complete(
            ...     messages=[UserMessage("Hello")],
            ...     router=my_router
            ... )
        
        CompletionRequest usage (internal):
            >>> request = CompletionRequest(messages=[...], model="gpt-4")
            >>> response = provider.complete(request)
        
        Args:
            messages: List of NimbusMessage objects, string, or CompletionRequest
            model: Model identifier (mutually exclusive with router)
            router: Router instance for load balancing (mutually exclusive with model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            CompletionResponse with the model's output
            
        Raises:
            ProviderError: If the provider API call fails
            ValueError: If required parameters are missing or both model and router provided
        """
        # Handle polymorphic input
        if isinstance(messages, CompletionRequest):
            request = messages
        else:
            # Convert to CompletionRequest
            if messages is None:
                raise ValueError("messages parameter is required")
            
            # Validate model/router parameters
            if model is not None and router is not None:
                raise ValueError("Cannot specify both 'model' and 'router' parameters")
            
            # Use provided model, router, or fall back to default
            effective_model = model or self.default_model
            
            if router is not None:
                # Router will select the model
                effective_model = router.select_model(messages)
            elif effective_model is None:
                raise ValueError(
                    "Either 'model' or 'router' parameter is required"
                )
            
            # Convert string to UserMessage if needed
            if isinstance(messages, str):
                from nimbus.base.messages import UserMessage
                messages = [UserMessage(content=messages)]
            
            request = CompletionRequest(
                messages=messages,
                model=effective_model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        
        start_time = time.time()
        try:
            response = self._complete_with_retry(request)
            
            # Attach capabilities to response for direct execution
            if request.capabilities:
                response._capabilities = request.capabilities
            
            # Record success with latency (only on final success)
            latency_ms = (time.time() - start_time) * 1000
            self.health_metrics.record_success(latency_ms)
            
            return response
        except Exception as e:
            # Record failure (only on final failure after all retries)
            self.health_metrics.record_failure()
            raise
    
    @with_retry(max_retries=3, min_wait=4, max_wait=10, multiplier=1)
    def _complete_with_retry(self, request: CompletionRequest) -> CompletionResponse:
        """Internal method with retry logic.
        
        This method is wrapped with retry decorator and does not track health metrics
        to avoid counting retries as separate failures.
        """
        try:
            provider_request = self._transform_request(request)
            provider_response = self._call_provider(provider_request)
            return self._transform_response(provider_response)
        except Exception as e:
            # Get provider name from model info if available
            provider_name = "unknown"
            try:
                provider_name = self.get_model_info().get("provider", "unknown")
            except Exception:
                pass
            
            raise ProviderError(
                f"Provider call failed: {str(e)}",
                provider=provider_name,
                original_error=str(e),
                error_type=type(e).__name__
            ) from e
    
    def stream(
        self,
        messages: list[Any] | str | CompletionRequest | None = None,
        model: str | None = None,
        router: Any | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        """Execute streaming completion.
        
        Supports both boto3-style direct calls and CompletionRequest objects.
        
        Boto3-style usage:
            >>> # With specific model
            >>> for chunk in client.stream(
            ...     messages=[UserMessage("Hello")],
            ...     model="gpt-4"
            ... ):
            ...     print(chunk.delta, end="")
            >>>
            >>> # With router for load balancing
            >>> for chunk in client.stream(
            ...     messages=[UserMessage("Hello")],
            ...     router=my_router
            ... ):
            ...     print(chunk.delta, end="")
        
        CompletionRequest usage (internal):
            >>> request = CompletionRequest(messages=[...], model="gpt-4", stream=True)
            >>> for chunk in provider.stream(request):
            ...     print(chunk.delta, end="")
        
        Args:
            messages: List of NimbusMessage objects, string, or CompletionRequest
            model: Model identifier (mutually exclusive with router)
            router: Router instance for load balancing (mutually exclusive with model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Yields:
            StreamChunk objects with incremental content
            
        Raises:
            ProviderError: If the provider API call fails
            ValueError: If required parameters are missing or both model and router provided
        """
        # Handle polymorphic input
        if isinstance(messages, CompletionRequest):
            request = messages
        else:
            # Convert to CompletionRequest
            if messages is None:
                raise ValueError("messages parameter is required")
            
            # Validate model/router parameters
            if model is not None and router is not None:
                raise ValueError("Cannot specify both 'model' and 'router' parameters")
            
            # Use provided model, router, or fall back to default
            effective_model = model or self.default_model
            
            if router is not None:
                # Router will select the model
                effective_model = router.select_model(messages)
            elif effective_model is None:
                raise ValueError(
                    "Either 'model' or 'router' parameter is required"
                )
            
            # Convert string to UserMessage if needed
            if isinstance(messages, str):
                from nimbus.base.messages import UserMessage
                messages = [UserMessage(content=messages)]
            
            request = CompletionRequest(
                messages=messages,
                model=effective_model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )
        
        start_time = time.time()
        try:
            yield from self._stream_with_retry(request)
            
            # Record success with latency after all chunks are yielded
            latency_ms = (time.time() - start_time) * 1000
            self.health_metrics.record_success(latency_ms)
        except Exception as e:
            # Record failure (only on final failure after all retries)
            self.health_metrics.record_failure()
            raise
    
    @with_retry(max_retries=3, min_wait=4, max_wait=10, multiplier=1)
    def _stream_with_retry(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        """Internal method with retry logic for streaming.
        
        This method is wrapped with retry decorator and does not track health metrics
        to avoid counting retries as separate failures.
        """
        try:
            provider_request = self._transform_request(request)
            provider_request["stream"] = True
            
            for chunk in self._call_provider_stream(provider_request):
                yield self._transform_stream_chunk(chunk)
        except Exception as e:
            # Get provider name from model info if available
            provider_name = "unknown"
            try:
                provider_name = self.get_model_info().get("provider", "unknown")
            except Exception:
                pass
            
            raise ProviderError(
                f"Provider streaming failed: {str(e)}",
                provider=provider_name,
                original_error=str(e),
                error_type=type(e).__name__
            ) from e
    
    async def invoke(self, input: CompletionRequest) -> CompletionResponse:
        """Runnable Port entry point: one request in, one response out.

        Delegates to :meth:`acomplete`; satisfies ``Runnable`` structurally.
        """
        return await self.acomplete(input)

    async def acomplete(
        self,
        messages: list[Any] | str | CompletionRequest | None = None,
        model: str | None = None,
        router: Any | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Execute asynchronous completion.
        
        Default implementation uses synchronous version. Override this method
        in subclasses to provide true async support using the provider's
        async client.
        
        Args:
            messages: List of NimbusMessage objects, string, or CompletionRequest
            model: Model identifier (mutually exclusive with router)
            router: Router instance for load balancing (mutually exclusive with model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            CompletionResponse with the model's output
            
        Raises:
            ProviderError: If the provider API call fails
        """
        return self.complete(messages, model, router, temperature, max_tokens, **kwargs)
    
    async def astream(self, request: CompletionRequest) -> Iterator[StreamChunk]:  # type: ignore[misc,override]
        """Execute asynchronous streaming completion.
        
        Default implementation uses synchronous version. Override this method
        in subclasses to provide true async support using the provider's
        async client.
        
        Args:
            request: The completion request
            
        Yields:
            StreamChunk objects with incremental content
            
        Raises:
            ProviderError: If the provider API call fails
        """
        for chunk in self.stream(request):
            yield chunk
    
    def get_health_metrics(self) -> dict[str, Any]:
        """Get health metrics for this provider.
        
        Returns health statistics including success rate, error rate, latency,
        and request counts.
        
        Returns:
            Dictionary containing health metrics with keys:
            - success_count: Number of successful requests
            - failure_count: Number of failed requests
            - total_requests: Total requests (success + failure)
            - success_rate: Success rate as decimal (0.0-1.0)
            - error_rate: Error rate as decimal (0.0-1.0)
            - average_latency_ms: Average latency in milliseconds
            - min_latency_ms: Minimum latency observed (None if no requests)
            - max_latency_ms: Maximum latency observed (None if no requests)
            - last_success_time: Unix timestamp of last successful request
            - last_failure_time: Unix timestamp of last failed request
            
        Example:
            >>> provider = OpenAIProvider(api_key="...")
            >>> # Make some requests...
            >>> metrics = provider.get_health_metrics()
            >>> print(f"Success rate: {metrics['success_rate']:.1%}")
            >>> print(f"Avg latency: {metrics['average_latency_ms']:.0f}ms")
        """
        return self.health_metrics.get_health_metrics()


class BaseEmbeddingProvider(VectorEncoderInterface, ABC):
    """Abstract base class for embedding providers.
    
    This class provides common functionality for all embedding provider
    implementations, including lazy client initialization and batch encoding.
    
    Subclasses must implement:
    - _initialize_client(): Create the provider-specific client
    - encode_batch(): Encode multiple texts to vectors
    - get_vector_dimension(): Return the vector dimension
    
    The encode() method is implemented using encode_batch() for consistency.
    
    Example:
        >>> class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
        ...     def _initialize_client(self):
        ...         import openai
        ...         return openai.OpenAI(api_key=self.config["api_key"])
        ...
        ...     def encode_batch(self, texts):
        ...         response = self.client.embeddings.create(
        ...             model=self.model,
        ...             input=texts
        ...         )
        ...         return [item.embedding for item in response.data]
        ...
        ...     def get_vector_dimension(self):
        ...         return 1536
    """
    
    def __init__(self, model: str, **config: Any) -> None:
        """Initialize base embedding provider.
        
        Args:
            model: Model identifier (e.g., 'text-embedding-3-small')
            **config: Provider-specific configuration parameters
        """
        self.model = model
        self.config = config
        self._client = None
        self.health_metrics = HealthMetrics()
    
    @property
    def client(self) -> Any:
        """Lazy-load the provider client.
        
        The client is only initialized when first accessed, reducing startup
        time and memory usage.
        
        Returns:
            The provider-specific client instance
        """
        if self._client is None:
            self._client = self._initialize_client()
        return self._client
    
    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the provider-specific client.
        
        This method should create and return the provider's SDK client.
        It will be called lazily when the client is first accessed.
        
        Returns:
            The initialized provider client
            
        Example:
            >>> def _initialize_client(self):
            ...     import openai
            ...     return openai.OpenAI(api_key=self.config["api_key"])
        """
        pass
    
    def encode(self, text: str) -> list[float]:
        """Encode single text to vector.
        
        This method uses encode_batch() internally for consistency.
        Health metrics are NOT tracked here to avoid double counting
        (encode_batch already tracks metrics).
        
        Args:
            text: The text to encode
            
        Returns:
            Vector representation of the text
        """
        return self.encode_batch([text])[0]
    
    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors.
        
        This method wraps _encode_batch_impl() with health tracking.
        Subclasses should implement _encode_batch_impl() instead.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
        """
        start_time = time.time()
        try:
            result = self._encode_batch_impl(texts)
            latency_ms = (time.time() - start_time) * 1000
            self.health_metrics.record_success(latency_ms)
            return result
        except Exception as e:
            self.health_metrics.record_failure()
            raise
    
    @abstractmethod
    def _encode_batch_impl(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors (implementation).
        
        Subclasses must implement this method instead of encode_batch().
        The encode_batch() method wraps this with health tracking.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
            
        Example:
            >>> def _encode_batch_impl(self, texts):
            ...     response = self.client.embeddings.create(
            ...         model=self.model,
            ...         input=texts
            ...     )
            ...     return [item.embedding for item in response.data]
        """
        pass
    
    async def aencode(self, text: str) -> list[float]:
        """Encode single text to vector asynchronously.
        
        This method uses aencode_batch() internally for consistency.
        Health metrics are NOT tracked here to avoid double counting
        (aencode_batch already tracks metrics).
        
        Args:
            text: The text to encode
            
        Returns:
            Vector representation of the text
        """
        results = await self.aencode_batch([text])
        return results[0]
    
    async def aencode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors asynchronously.
        
        This method wraps _aencode_batch_impl() with health tracking.
        Default implementation uses synchronous version.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
        """
        start_time = time.time()
        try:
            result = await self._aencode_batch_impl(texts)
            latency_ms = (time.time() - start_time) * 1000
            self.health_metrics.record_success(latency_ms)
            return result
        except Exception as e:
            self.health_metrics.record_failure()
            raise
    
    async def _aencode_batch_impl(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors asynchronously (implementation).
        
        Default implementation uses synchronous version. Override this method
        in subclasses to provide true async support using the provider's
        async client.
        
        Note: Calls _encode_batch_impl() directly to avoid double metric tracking.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
        """
        return self._encode_batch_impl(texts)
    
    @abstractmethod
    def get_vector_dimension(self) -> int:
        """Return the dimension of vectors produced by this encoder.
        
        Returns:
            The vector dimension size
            
        Example:
            >>> def get_vector_dimension(self):
            ...     return 1536  # For text-embedding-3-small
        """
        pass
    
    def get_health_metrics(self) -> dict[str, Any]:
        """Get health metrics for this embedding provider.
        
        Returns health statistics including success rate, error rate, latency,
        and request counts.
        
        Returns:
            Dictionary containing health metrics with keys:
            - success_count: Number of successful encoding requests
            - failure_count: Number of failed encoding requests
            - total_requests: Total requests (success + failure)
            - success_rate: Success rate as decimal (0.0-1.0)
            - error_rate: Error rate as decimal (0.0-1.0)
            - average_latency_ms: Average latency in milliseconds
            - min_latency_ms: Minimum latency observed (None if no requests)
            - max_latency_ms: Maximum latency observed (None if no requests)
            - last_success_time: Unix timestamp of last successful request
            - last_failure_time: Unix timestamp of last failed request
            
        Example:
            >>> provider = OpenAIEmbeddingProvider(model="text-embedding-3-small")
            >>> # Make some encoding requests...
            >>> metrics = provider.get_health_metrics()
            >>> print(f"Success rate: {metrics['success_rate']:.1%}")
        """
        return self.health_metrics.get_health_metrics()
