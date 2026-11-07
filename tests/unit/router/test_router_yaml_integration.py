"""Integration tests for ModelRouter YAML configuration loading.

Tests the ModelRouter.from_yaml() and ModelRouter.from_config_dict() methods
to ensure proper router instantiation from configuration.
"""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import pytest

from skye.base.completion import CompleteRequest, CompleteResponse, StreamChunk, TokenUsage
from skye.base.exceptions import ConfigurationError
from skye.base.interfaces.router import RoutingStrategy
from skye.models.base import BaseModelProvider
from skye.models.registry import ProviderRegistry
from skye.router.model_router import ModelRouter


class MockProvider(BaseModelProvider):
    """Mock provider for testing."""
    
    def _initialize_client(self) -> Any:
        return {"mock": "client"}
    
    def _transform_request(self, request: CompleteRequest) -> dict[str, Any]:
        return {"model": request.model, "messages": []}
    
    def _transform_response(self, response: Any) -> CompleteResponse:
        return CompleteResponse(
            id="test_id",
            model="test_model",
            provider="mock",
            content="Mock response",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            created_at=datetime.now(timezone.utc)
        )
    
    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        return StreamChunk(id="test", delta="", index=0)
    
    def _call_provider(self, request: dict[str, Any]) -> Any:
        return {"content": "Mock response"}
    
    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        yield {"delta": "Mock response"}
    
    def _transform_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        return [{"role": "user", "content": "test"}]
    
    def _transform_capabilities(self, capabilities: list[Any]) -> list[dict[str, Any]]:
        return []
    
    def _extract_capability_calls(self, response: Any) -> list[Any] | None:
        return None
    
    def format_capability_results(self, results: list[Any]) -> list[dict[str, Any]]:
        """Format capability results for mock provider."""
        return [{"mock_result": "formatted"} for _ in results]
    
    def get_model_info(self) -> dict[str, Any]:
        """Get model information."""
        return {"provider": "mock", "model": "test-model"}


class TestModelRouterFromConfigDict:
    """Tests for ModelRouter.from_config_dict() class method."""

    def setup_method(self):
        """Set up test fixtures."""
        # Register mock provider for testing
        ProviderRegistry.register_model_provider("mock", MockProvider)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clear provider registry
        ProviderRegistry._model_providers = {}

    def test_from_config_dict_minimal(self):
        """Test creating router from minimal config dict."""
        config = {"routes": []}

        router = ModelRouter.from_config_dict(config)

        assert router is not None
        assert router.strategy == RoutingStrategy.ROUND_ROBIN
        assert router.cooldown_seconds == 60.0
        assert router.pre_call_checks_enabled is True

    def test_from_config_dict_with_strategy(self):
        """Test creating router with custom strategy."""
        config = {"routes": [], "strategy": "least_busy"}

        router = ModelRouter.from_config_dict(config)

        assert router.strategy == RoutingStrategy.LEAST_BUSY

    def test_from_config_dict_with_settings(self):
        """Test creating router with custom settings."""
        config = {
            "routes": [],
            "strategy": "rate_limit_aware",
            "cooldown_seconds": 120.0,
            "enable_pre_call_checks": False,
        }

        router = ModelRouter.from_config_dict(config)

        assert router.strategy == RoutingStrategy.RATE_LIMIT_AWARE
        assert router.cooldown_seconds == 120.0
        assert router.pre_call_checks_enabled is False

    def test_from_config_dict_invalid_strategy(self):
        """Test that invalid strategy raises ConfigurationError."""
        config = {"routes": [], "strategy": "invalid_strategy"}

        with pytest.raises(ConfigurationError) as exc_info:
            ModelRouter.from_config_dict(config)

        assert "invalid_strategy" in str(exc_info.value).lower()

    def test_from_config_dict_with_routes(self):
        """Test creating router with route configurations."""
        config = {
            "routes": [
                {
                    "alias": "test-model",
                    "targets": [
                        {
                            "model": "gpt-3.5-turbo",
                            "provider": "mock",
                            "api_key": "sk-test",
                            "tpm": 200000,
                            "rpm": 2000,
                        }
                    ],
                    "strategy": "round_robin",
                }
            ]
        }

        router = ModelRouter.from_config_dict(config)

        assert router.is_alias("test-model")
        assert "test-model" in router.list_aliases()

    def test_from_config_dict_with_fallbacks(self):
        """Test creating router with fallback configurations."""
        config = {
            "routes": [
                {
                    "alias": "gpt-4",
                    "targets": [
                        {"model": "gpt-4", "provider": "mock", "api_key": "sk-test"}
                    ],
                },
                {
                    "alias": "gpt-3.5-turbo",
                    "targets": [
                        {"model": "gpt-3.5-turbo", "provider": "mock", "api_key": "sk-test"}
                    ],
                },
            ],
            "fallbacks": [{"primary": "gpt-4", "fallbacks": ["gpt-3.5-turbo"]}],
        }

        router = ModelRouter.from_config_dict(config)

        assert "gpt-4" in router.fallbacks
        assert router.fallbacks["gpt-4"] == ["gpt-3.5-turbo"]

    def test_from_config_dict_with_retry_policies(self):
        """Test creating router with retry policies."""
        config = {
            "routes": [],
            "retry_policies": [
                {"error_type": "RateLimitError", "max_retries": 5},
                {"error_type": "TimeoutError", "max_retries": 3},
            ],
        }

        router = ModelRouter.from_config_dict(config)

        assert router.retry_policy["RateLimitError"] == 5
        assert router.retry_policy["TimeoutError"] == 3

    def test_from_config_dict_with_allowed_fails_policies(self):
        """Test creating router with allowed fails policies."""
        config = {
            "routes": [],
            "allowed_fails_policies": [
                {"error_type": "RateLimitError", "allowed_fails_per_minute": 50}
            ],
        }

        router = ModelRouter.from_config_dict(config)

        assert router.allowed_fails_policy["RateLimitError"] == 50

    def test_from_config_dict_missing_required_route_field(self):
        """Test that missing required route field raises ConfigurationError."""
        config = {
            "routes": [
                {
                    # Missing 'alias' field
                    "targets": [
                        {"model": "gpt-3.5-turbo", "provider": "mock", "api_key": "sk-test"}
                    ]
                }
            ]
        }

        with pytest.raises(ConfigurationError) as exc_info:
            ModelRouter.from_config_dict(config)

        assert "missing" in str(exc_info.value).lower()

    def test_from_config_dict_kwargs_override(self):
        """Test that kwargs override config dict values."""
        config = {"routes": [], "strategy": "round_robin", "cooldown_seconds": 60.0}

        router = ModelRouter.from_config_dict(
            config, strategy="least_busy", cooldown_seconds=120.0
        )

        assert router.strategy == RoutingStrategy.LEAST_BUSY
        assert router.cooldown_seconds == 120.0


class TestModelRouterFromYAML:
    """Tests for ModelRouter.from_yaml() class method."""

    def setup_method(self):
        """Set up test fixtures."""
        # Register mock provider for testing
        ProviderRegistry.register_model_provider("mock", MockProvider)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clear provider registry
        ProviderRegistry._model_providers = {}

    def test_from_yaml_minimal(self):
        """Test creating router from minimal YAML file."""
        yaml_content = """
routes: []
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            router = ModelRouter.from_yaml(temp_path)

            assert router is not None
            assert router.strategy == RoutingStrategy.ROUND_ROBIN
        finally:
            os.unlink(temp_path)

    def test_from_yaml_with_routes(self):
        """Test creating router from YAML with routes."""
        yaml_content = """
routes:
  - alias: "test-model"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "mock"
        api_key: "sk-test"
        tpm: 200000
        rpm: 2000
    strategy: "rate_limit_aware"

strategy: "round_robin"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            router = ModelRouter.from_yaml(temp_path)

            assert router.is_alias("test-model")
            route = router.get_route("test-model")
            assert route is not None
            assert route.strategy == RoutingStrategy.RATE_LIMIT_AWARE
        finally:
            os.unlink(temp_path)

    def test_from_yaml_with_env_vars(self):
        """Test creating router from YAML with environment variables."""
        # Set test environment variable
        os.environ["TEST_API_KEY"] = "sk-real-key-123"

        yaml_content = """
routes:
  - alias: "test-model"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "mock"
        api_key: "${TEST_API_KEY}"
        tpm: 200000
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            router = ModelRouter.from_yaml(temp_path)

            assert router.is_alias("test-model")
            # The API key should have been substituted during target creation
        finally:
            os.unlink(temp_path)
            del os.environ["TEST_API_KEY"]

    def test_from_yaml_with_path_object(self):
        """Test creating router from YAML using Path object."""
        yaml_content = """
routes:
  - alias: "test-model"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "mock"
        api_key: "sk-test"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            router = ModelRouter.from_yaml(temp_path)

            assert router.is_alias("test-model")
        finally:
            temp_path.unlink()

    def test_from_yaml_kwargs_override(self):
        """Test that kwargs override YAML values."""
        yaml_content = """
routes: []
strategy: "round_robin"
cooldown_seconds: 60.0
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            router = ModelRouter.from_yaml(
                temp_path, strategy="least_busy", cooldown_seconds=120.0
            )

            assert router.strategy == RoutingStrategy.LEAST_BUSY
            assert router.cooldown_seconds == 120.0
        finally:
            os.unlink(temp_path)

    def test_from_yaml_file_not_found(self):
        """Test that missing YAML file raises ConfigurationError."""
        with pytest.raises(ConfigurationError):
            ModelRouter.from_yaml("/nonexistent/path/config.yaml")

    def test_from_yaml_complex_configuration(self):
        """Test creating router from complex YAML configuration."""
        yaml_content = """
routes:
  - alias: "gpt-4"
    targets:
      - model: "gpt-4"
        provider: "mock"
        api_key: "sk-test-1"
        tpm: 100000
        rpm: 1000
        tags: ["premium"]
      - model: "gpt-4-turbo"
        provider: "mock"
        api_key: "sk-test-2"
        api_base: "https://api.openai.com/v1"
        tpm: 80000
        rpm: 800
    strategy: "rate_limit_aware"

  - alias: "gpt-3.5-turbo"
    targets:
      - model: "gpt-3.5-turbo"
        provider: "mock"
        api_key: "sk-test-3"
        tpm: 200000
        rpm: 2000
    strategy: "round_robin"

fallbacks:
  - primary: "gpt-4"
    fallbacks: ["gpt-3.5-turbo"]

retry_policies:
  - error_type: "RateLimitError"
    max_retries: 3

allowed_fails_policies:
  - error_type: "RateLimitError"
    allowed_fails_per_minute: 100

strategy: "least_busy"
cooldown_seconds: 120.0
enable_pre_call_checks: false
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            router = ModelRouter.from_yaml(temp_path)

            # Verify router settings
            assert router.strategy == RoutingStrategy.LEAST_BUSY
            assert router.cooldown_seconds == 120.0
            assert router.pre_call_checks_enabled is False

            # Verify routes
            assert router.is_alias("gpt-4")
            assert router.is_alias("gpt-3.5-turbo")

            # Verify fallbacks
            assert "gpt-4" in router.fallbacks
            assert router.fallbacks["gpt-4"] == ["gpt-3.5-turbo"]

            # Verify policies
            assert router.retry_policy["RateLimitError"] == 3
            assert router.allowed_fails_policy["RateLimitError"] == 100
        finally:
            os.unlink(temp_path)


class TestModelTargetEnvVarSubstitution:
    """Tests for ModelTarget environment variable substitution."""

    def test_model_target_env_var_substitution(self):
        """Test that ModelTarget substitutes environment variables."""
        from skye.base.config import _env_var_cache
        from skye.router.model_router import ModelTarget

        # Clear cache to avoid interference from other tests
        _env_var_cache.clear()

        # Set test environment variables
        os.environ["TEST_API_KEY_UNIQUE"] = "sk-real-key-456"
        os.environ["TEST_API_BASE_UNIQUE"] = "https://test.example.com"

        try:
            target = ModelTarget(
                model="gpt-4",
                provider="mock",
                api_key="${TEST_API_KEY_UNIQUE}",
                api_base="${TEST_API_BASE_UNIQUE}",
            )

            # Environment variables should be substituted
            assert target.api_key == "sk-real-key-456"
            assert target.api_base == "https://test.example.com"
        finally:
            del os.environ["TEST_API_KEY_UNIQUE"]
            del os.environ["TEST_API_BASE_UNIQUE"]
            _env_var_cache.clear()

    def test_model_target_missing_env_var(self):
        """Test that missing environment variable raises ConfigurationError."""
        from skye.router.model_router import ModelTarget

        with pytest.raises(ConfigurationError) as exc_info:
            ModelTarget(
                model="gpt-4", provider="mock", api_key="${NONEXISTENT_VAR}"
            )

        assert "NONEXISTENT_VAR" in str(exc_info.value)

    def test_model_target_no_env_var(self):
        """Test that ModelTarget works without environment variables."""
        from skye.router.model_router import ModelTarget

        target = ModelTarget(
            model="gpt-4", provider="mock", api_key="sk-plain-key"
        )

        assert target.api_key == "sk-plain-key"

    def test_model_target_partial_env_var(self):
        """Test that partial environment variable patterns are not substituted."""
        from skye.router.model_router import ModelTarget

        # This should not trigger substitution (missing closing brace)
        target = ModelTarget(
            model="gpt-4", provider="mock", api_key="sk-${PARTIAL"
        )

        # Should remain unchanged
        assert target.api_key == "sk-${PARTIAL"
