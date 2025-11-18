"""Base provider classes for model and embedding providers.

This module provides abstract base classes that all provider implementations
must inherit from. These classes handle common functionality like lazy client
initialization, error handling, request/response transformation, and retry logic.
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, AsyncIterator

from nimbus.completion import CompletionRequest, CompletionResponse, StreamChunk
from nimbus.exceptions import ProviderError
from nimbus.interfaces.model import ModelInterface
from nimbus.interfaces.vector_encoder import VectorEncoderInterface
from nimbus.providers.health import HealthMetrics
from nimbus.providers.retry import with_retry


class BaseModelProvider(ModelInterface, ABC):
    """Abstract base class for model providers.
    
    This class provides common functionality for all LLM provider implementations,
    including lazy client initialization, error handling, and a template method
    pattern for request/response transformation.
    
    Subclasses must implement:
    - _initialize_client(): Create the provider-specific client
    - _transform_request(): Convert CompletionRequest to provider format
    - _transform_response(): Convert provider response to CompletionResponse
    - _transform_stream_chunk(): Convert provider stream chunk to StreamChunk
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
        ...         return {"model": request.model, "messages": [...]}
        ...
        ...     # ... implement other abstract methods
    """
    
    def __init__(self, **config: Any) -> None:
        """Initialize base provider with configuration.
        
        Args:
            **config: Provider-specific configuration parameters
        """
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
    
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute synchronous completion.
        
        This method handles the complete flow:
        1. Transform request to provider format
        2. Call provider API (with retry logic)
        3. Transform response to nimbus format
        4. Wrap any errors in ProviderError
        
        Includes automatic retry logic with exponential backoff for transient failures.
        Health metrics are tracked for all requests (only final result, not retries).
        
        Args:
            request: The completion request
            
        Returns:
            CompletionResponse with the model's output
            
        Raises:
            ProviderError: If the provider API call fails
        """
        start_time = time.time()
        try:
            response = self._complete_with_retry(request)
            
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
    
    def stream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        """Execute streaming completion.
        
        This method handles the streaming flow:
        1. Transform request to provider format
        2. Call provider streaming API (with retry logic)
        3. Transform each chunk to nimbus format
        4. Wrap any errors in ProviderError
        
        Includes automatic retry logic with exponential backoff for transient failures.
        Health metrics are tracked for all requests (only final result, not retries).
        
        Args:
            request: The completion request
            
        Yields:
            StreamChunk objects with incremental content
            
        Raises:
            ProviderError: If the provider API call fails
        """
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
    
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute asynchronous completion.
        
        Default implementation uses synchronous version. Override this method
        in subclasses to provide true async support using the provider's
        async client.
        
        Args:
            request: The completion request
            
        Returns:
            CompletionResponse with the model's output
            
        Raises:
            ProviderError: If the provider API call fails
        """
        return self.complete(request)
    
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
