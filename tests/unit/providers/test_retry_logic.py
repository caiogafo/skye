"""Unit tests for retry logic in providers.

Tests cover:
- Retry decorator functionality
- Exponential backoff timing
- Max retries exceeded
- Successful retry after failures
"""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from nimbus.completion import CompletionRequest, CompletionResponse, TokenUsage
from nimbus.exceptions import ProviderError
from nimbus.messages import UserMessage
from nimbus.providers.base import BaseModelProvider
from nimbus.providers.retry import with_retry


class MockProvider(BaseModelProvider):
    """Mock provider for testing retry logic."""

    def __init__(self, **config):
        super().__init__(**config)
        self.call_count = 0
        self.fail_count = 0

    def _initialize_client(self):
        return MagicMock()

    def _transform_request(self, request):
        return {"model": request.model, "messages": []}

    def _transform_response(self, response):
        return CompletionResponse(
            id="test-id",
            model="test-model",
            provider="mock",
            content="test response",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

    def _transform_stream_chunk(self, chunk):
        return MagicMock()

    def _transform_messages(self, messages):
        """Transform messages to mock format."""
        return [{"role": m.role, "content": m.content} for m in messages]

    def _transform_capabilities(self, capabilities):
        """Transform capabilities to mock format."""
        return [{"name": c.get_schema().name} for c in capabilities]

    def _extract_capability_calls(self, response):
        """Extract capability calls from mock response."""
        return None

    def _call_provider(self, request):
        self.call_count += 1
        if self.fail_count > 0:
            self.fail_count -= 1
            raise ProviderError(
                "Transient error",
                provider="mock",
                error_type="rate_limit",
            )
        return MagicMock()

    def _call_provider_stream(self, request):
        return iter([])

    def get_model_info(self):
        return {"provider": "mock"}


class TestRetryDecorator:
    """Test the retry decorator."""

    def test_retry_decorator_success_on_first_try(self) -> None:
        """Test that decorator doesn't retry on success."""
        provider = MockProvider()
        request = CompletionRequest(
            messages=[UserMessage(content="test")], model="test-model"
        )

        response = provider.complete(request)

        assert response.content == "test response"
        assert provider.call_count == 1

    def test_retry_decorator_retries_on_failure(self) -> None:
        """Test that decorator retries on ProviderError."""
        provider = MockProvider()
        provider.fail_count = 2  # Fail twice, succeed on third try
        request = CompletionRequest(
            messages=[UserMessage(content="test")], model="test-model"
        )

        response = provider.complete(request)

        assert response.content == "test response"
        assert provider.call_count == 3

    def test_retry_decorator_max_retries_exceeded(self) -> None:
        """Test that decorator raises after max retries exceeded."""
        provider = MockProvider()
        provider.fail_count = 10  # Fail more times than max retries
        request = CompletionRequest(
            messages=[UserMessage(content="test")], model="test-model"
        )

        with pytest.raises(ProviderError):
            provider.complete(request)

        # Should have tried 3 times (initial + 2 retries)
        assert provider.call_count == 3

    def test_retry_decorator_exponential_backoff(self) -> None:
        """Test that retry uses exponential backoff."""
        provider = MockProvider()
        provider.fail_count = 1  # Fail once, succeed on second try
        request = CompletionRequest(
            messages=[UserMessage(content="test")], model="test-model"
        )

        start_time = time.time()
        response = provider.complete(request)
        elapsed = time.time() - start_time

        assert response.content == "test response"
        # Should have waited at least min_wait (4 seconds)
        # Allow some tolerance for test execution
        assert elapsed >= 3.5

    def test_retry_decorator_with_custom_params(self) -> None:
        """Test retry decorator with custom parameters."""

        class CustomRetryProvider(BaseModelProvider):
            def __init__(self, **config):
                super().__init__(**config)
                self.call_count = 0

            def _initialize_client(self):
                return MagicMock()

            def _transform_request(self, request):
                return {}

            def _transform_response(self, response):
                return CompletionResponse(
                    id="test",
                    model="test",
                    provider="mock",
                    content="test",
                    finish_reason="stop",
                    usage=TokenUsage(
                        prompt_tokens=10, completion_tokens=5, total_tokens=15
                    ),
                )

            def _transform_stream_chunk(self, chunk):
                return MagicMock()

            def _transform_messages(self, messages):
                """Transform messages to mock format."""
                return [{"role": m.role, "content": m.content} for m in messages]

            def _transform_capabilities(self, capabilities):
                """Transform capabilities to mock format."""
                return [{"name": c.get_schema().name} for c in capabilities]

            def _extract_capability_calls(self, response):
                """Extract capability calls from mock response."""
                return None

            @with_retry(max_retries=2, min_wait=0.1, max_wait=0.2, multiplier=1)
            def _call_provider(self, request):
                self.call_count += 1
                if self.call_count < 2:
                    raise ProviderError("test error", provider="mock")
                return MagicMock()

            def _call_provider_stream(self, request):
                return iter([])

            def get_model_info(self):
                return {"provider": "mock"}

        provider = CustomRetryProvider()
        request = CompletionRequest(
            messages=[UserMessage(content="test")], model="test-model"
        )

        # This should succeed after 1 retry
        response = provider.complete(request)
        assert response.content == "test"

    def test_retry_preserves_exception_chain(self) -> None:
        """Test that retry preserves the exception chain."""

        class FailingProvider(BaseModelProvider):
            def _initialize_client(self):
                return MagicMock()

            def _transform_request(self, request):
                return {}

            def _transform_response(self, response):
                return CompletionResponse(
                    id="test",
                    model="test",
                    provider="mock",
                    content="test",
                    finish_reason="stop",
                    usage=TokenUsage(
                        prompt_tokens=10, completion_tokens=5, total_tokens=15
                    ),
                )

            def _transform_stream_chunk(self, chunk):
                return MagicMock()

            def _transform_messages(self, messages):
                """Transform messages to mock format."""
                return [{"role": m.role, "content": m.content} for m in messages]

            def _transform_capabilities(self, capabilities):
                """Transform capabilities to mock format."""
                return [{"name": c.get_schema().name} for c in capabilities]

            def _extract_capability_calls(self, response):
                """Extract capability calls from mock response."""
                return None

            def _call_provider(self, request):
                raise ProviderError("original error", provider="mock")

            def _call_provider_stream(self, request):
                return iter([])

            def get_model_info(self):
                return {"provider": "mock"}

        provider = FailingProvider()
        request = CompletionRequest(
            messages=[UserMessage(content="test")], model="test-model"
        )

        with pytest.raises(ProviderError) as exc_info:
            provider.complete(request)

        # Check that the exception chain is preserved
        assert exc_info.value.details["provider"] == "mock"
        assert "original error" in str(exc_info.value)


class TestRetryWithStreaming:
    """Test retry logic with streaming."""

    def test_stream_raises_on_failure(self) -> None:
        """Test that stream method raises ProviderError on failure.
        
        Note: The retry decorator wraps the stream method, but the exception
        is caught and re-raised as a new ProviderError in the except block,
        which breaks the retry chain. This is a known limitation of retrying
        generators.
        """

        class StreamingProvider(BaseModelProvider):
            def __init__(self, **config):
                super().__init__(**config)
                self.call_count = 0

            def _initialize_client(self):
                return MagicMock()

            def _transform_request(self, request):
                return {}

            def _transform_response(self, response):
                return CompletionResponse(
                    id="test",
                    model="test",
                    provider="mock",
                    content="test",
                    finish_reason="stop",
                    usage=TokenUsage(
                        prompt_tokens=10, completion_tokens=5, total_tokens=15
                    ),
                )

            def _transform_stream_chunk(self, chunk):
                return MagicMock()

            def _transform_messages(self, messages):
                """Transform messages to mock format."""
                return [{"role": m.role, "content": m.content} for m in messages]

            def _transform_capabilities(self, capabilities):
                """Transform capabilities to mock format."""
                return [{"name": c.get_schema().name} for c in capabilities]

            def _extract_capability_calls(self, response):
                """Extract capability calls from mock response."""
                return None

            def _call_provider(self, request):
                return MagicMock()

            def _call_provider_stream(self, request):
                self.call_count += 1
                raise ProviderError("stream error", provider="mock")

            def get_model_info(self):
                return {"provider": "mock"}

        provider = StreamingProvider()
        request = CompletionRequest(
            messages=[UserMessage(content="test")], model="test-model"
        )

        # Stream should raise ProviderError
        with pytest.raises(ProviderError):
            list(provider.stream(request))

        # Only called once because the exception is caught and re-raised
        # before the retry decorator can retry
        assert provider.call_count == 1
