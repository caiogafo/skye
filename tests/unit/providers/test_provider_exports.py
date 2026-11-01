"""Tests for provider package exports."""

import types

import pytest


class TestProviderExports:
    """Test suite for provider package exports."""

    def test_provider_registry_importable(self):
        """Test that ProviderRegistry is importable from nimbus.models."""
        from nimbus.models import ProviderRegistry

        assert ProviderRegistry is not None

    def test_all_model_providers_importable(self):
        """Test that all model provider classes are importable."""
        from nimbus.models import (
            AnthropicProvider,
            AzureOpenAIProvider,
            BedrockProvider,
            OpenAIProvider,
            GoogleProvider,
        )

        assert OpenAIProvider is not None
        assert AnthropicProvider is not None
        assert BedrockProvider is not None
        assert AzureOpenAIProvider is not None
        assert GoogleProvider is not None

    def test_all_embedding_providers_importable(self):
        """Test that all embedding provider classes are importable."""
        from nimbus.models import (
            BedrockEmbeddingProvider,
            CohereEmbeddingProvider,
            OpenAIEmbeddingProvider,
            GoogleEmbeddingProvider,
            GoogleMultimodalEmbeddingProvider,
        )

        assert OpenAIEmbeddingProvider is not None
        assert BedrockEmbeddingProvider is not None
        assert CohereEmbeddingProvider is not None
        assert GoogleEmbeddingProvider is not None
        assert GoogleMultimodalEmbeddingProvider is not None

    def test_utility_classes_importable(self):
        """Test that utility classes are importable."""
        from nimbus.models import (
            CostCalculator,
            ImageHandler,
            LazyImporter,
            TokenCounter,
        )

        assert TokenCounter is not None
        assert CostCalculator is not None
        assert ImageHandler is not None
        assert LazyImporter is not None

    def test_base_classes_importable(self):
        """Test that base provider classes are importable."""
        from nimbus.models import BaseEmbeddingProvider, BaseModelProvider

        assert BaseModelProvider is not None
        assert BaseEmbeddingProvider is not None

    def test_all_defined(self):
        """Test that __all__ is properly defined in nimbus.models."""
        import nimbus.models

        assert hasattr(nimbus.models, "__all__")
        assert isinstance(nimbus.models.__all__, list)
        assert len(nimbus.models.__all__) > 0

    def test_all_contains_registry(self):
        """Test that __all__ contains ProviderRegistry."""
        from nimbus.models import __all__

        assert "ProviderRegistry" in __all__

    def test_all_contains_model_providers(self):
        """Test that __all__ contains all model provider classes."""
        from nimbus.models import __all__

        expected_providers = [
            "OpenAIProvider",
            "AnthropicProvider",
            "BedrockProvider",
            "AzureOpenAIProvider",
            "GoogleProvider",
        ]

        for provider in expected_providers:
            assert provider in __all__, f"{provider} not in __all__"

    def test_all_contains_embedding_providers(self):
        """Test that __all__ contains all embedding provider classes."""
        from nimbus.models import __all__

        expected_providers = [
            "OpenAIEmbeddingProvider",
            "BedrockEmbeddingProvider",
            "CohereEmbeddingProvider",
            "GoogleEmbeddingProvider",
            "GoogleMultimodalEmbeddingProvider",
        ]

        for provider in expected_providers:
            assert provider in __all__, f"{provider} not in __all__"

    def test_all_contains_utilities(self):
        """Test that __all__ contains utility classes."""
        from nimbus.models import __all__

        expected_utilities = [
            "TokenCounter",
            "CostCalculator",
            "ImageHandler",
            "LazyImporter",
        ]

        for utility in expected_utilities:
            assert utility in __all__, f"{utility} not in __all__"

    def test_all_contains_base_classes(self):
        """Test that __all__ contains base provider classes."""
        from nimbus.models import __all__

        expected_bases = [
            "BaseModelProvider",
            "BaseEmbeddingProvider",
        ]

        for base in expected_bases:
            assert base in __all__, f"{base} not in __all__"

    def test_all_exports_are_importable(self):
        """Test that all symbols in __all__ are actually importable."""
        import nimbus.models

        for symbol_name in nimbus.models.__all__:
            symbol = getattr(nimbus.models, symbol_name)
            assert symbol is not None, f"Symbol {symbol_name} is None"

    def test_no_unexpected_exports(self):
        """Test that only expected symbols are exported."""
        import nimbus.models

        # Get all public attributes that are not modules
        public_attrs = [
            attr
            for attr in dir(nimbus.models)
            if not attr.startswith("_")
            and not isinstance(getattr(nimbus.models, attr), types.ModuleType)
        ]

        # All public non-module attributes should be in __all__
        for attr in public_attrs:
            assert (
                attr in nimbus.models.__all__
            ), f"Unexpected public export: {attr}"

    def test_combined_import_from_providers(self):
        """Test that multiple symbols can be imported together from nimbus.models."""
        from nimbus.models import (
            CostCalculator,
            ImageHandler,
            LazyImporter,
            OpenAIProvider,
            ProviderRegistry,
            TokenCounter,
        )

        # Verify all imports succeeded
        assert ProviderRegistry is not None
        assert OpenAIProvider is not None
        assert TokenCounter is not None
        assert CostCalculator is not None
        assert ImageHandler is not None
        assert LazyImporter is not None

    def test_provider_registry_functionality(self):
        """Test that imported ProviderRegistry is functional."""
        from nimbus.models import ProviderRegistry

        # Verify registry methods exist
        assert hasattr(ProviderRegistry, "list_model_providers")
        assert hasattr(ProviderRegistry, "list_embedding_providers")
        assert hasattr(ProviderRegistry, "get_model_provider")
        assert hasattr(ProviderRegistry, "get_embedding_provider")

        # Verify providers are registered
        model_providers = ProviderRegistry.list_model_providers()
        embedding_providers = ProviderRegistry.list_embedding_providers()

        assert len(model_providers) > 0
        assert len(embedding_providers) > 0

    def test_provider_classes_are_types(self):
        """Test that all provider classes are actually types."""
        from nimbus.models import (
            AnthropicProvider,
            AzureOpenAIProvider,
            BedrockProvider,
            OpenAIProvider,
            GoogleProvider,
        )

        assert isinstance(OpenAIProvider, type)
        assert isinstance(AnthropicProvider, type)
        assert isinstance(BedrockProvider, type)
        assert isinstance(AzureOpenAIProvider, type)
        assert isinstance(GoogleProvider, type)

    def test_embedding_provider_classes_are_types(self):
        """Test that all embedding provider classes are actually types."""
        from nimbus.models import (
            BedrockEmbeddingProvider,
            CohereEmbeddingProvider,
            OpenAIEmbeddingProvider,
            GoogleEmbeddingProvider,
            GoogleMultimodalEmbeddingProvider,
        )

        assert isinstance(OpenAIEmbeddingProvider, type)
        assert isinstance(BedrockEmbeddingProvider, type)
        assert isinstance(CohereEmbeddingProvider, type)
        assert isinstance(GoogleEmbeddingProvider, type)
        assert isinstance(GoogleMultimodalEmbeddingProvider, type)

    def test_utility_classes_are_types(self):
        """Test that all utility classes are actually types."""
        from nimbus.models import (
            CostCalculator,
            ImageHandler,
            LazyImporter,
            TokenCounter,
        )

        assert isinstance(TokenCounter, type)
        assert isinstance(CostCalculator, type)
        assert isinstance(ImageHandler, type)
        assert isinstance(LazyImporter, type)

    def test_base_classes_are_types(self):
        """Test that base provider classes are actually types."""
        from nimbus.models import BaseEmbeddingProvider, BaseModelProvider

        assert isinstance(BaseModelProvider, type)
        assert isinstance(BaseEmbeddingProvider, type)

    def test_all_list_count(self):
        """Test that __all__ has the expected number of exports."""
        from nimbus.models import __all__

        # Count expected exports:
        # - 1 ProviderRegistry
        # - 5 model providers
        # - 5 embedding providers
        # - 4 utilities
        # - 2 base classes
        # Total: 17
        expected_count = 17

        assert len(__all__) == expected_count, f"Expected {expected_count} exports, got {len(__all__)}"

    def test_import_from_nimbus_providers_module(self):
        """Test importing from nimbus.models module directly."""
        import nimbus.models

        # Verify key exports are accessible
        assert hasattr(nimbus.models, "ProviderRegistry")
        assert hasattr(nimbus.models, "OpenAIProvider")
        assert hasattr(nimbus.models, "TokenCounter")
        assert hasattr(nimbus.models, "CostCalculator")
        assert hasattr(nimbus.models, "ImageHandler")
        assert hasattr(nimbus.models, "LazyImporter")

    def test_verify_import_command(self):
        """Test the verification command from task description."""
        # This tests: uv run python -c "from nimbus.models import ProviderRegistry, OpenAIProvider; print('OK')"
        from nimbus.models import OpenAIProvider, ProviderRegistry

        assert ProviderRegistry is not None
        assert OpenAIProvider is not None
        # If we got here, the import succeeded
        assert True
