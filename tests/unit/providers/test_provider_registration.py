"""Tests for automatic provider registration on import."""

import pytest


class TestProviderAutoRegistration:
    """Test suite for automatic provider registration."""

    def test_providers_auto_registered_on_import(self):
        """Test that providers are auto-registered when nimbus.models is imported."""
        # Import the providers module to trigger auto-registration
        from nimbus.models import ProviderRegistry

        # Verify model providers are registered
        model_providers = ProviderRegistry.list_model_providers()
        assert "openai" in model_providers
        assert "anthropic" in model_providers
        assert "bedrock" in model_providers
        assert "azure" in model_providers
        assert "vertex" in model_providers

    def test_embedding_providers_auto_registered_on_import(self):
        """Test that embedding providers are auto-registered when nimbus.models is imported."""
        from nimbus.models import ProviderRegistry

        # Verify embedding providers are registered
        embedding_providers = ProviderRegistry.list_embedding_providers()
        assert "openai" in embedding_providers
        assert "bedrock" in embedding_providers
        assert "cohere" in embedding_providers
        assert "vertex" in embedding_providers
        assert "vertex-multimodal" in embedding_providers

    def test_openai_provider_registered(self):
        """Test that OpenAI provider is properly registered."""
        from nimbus.models import ProviderRegistry

        # Verify OpenAI provider can be retrieved
        assert "openai" in ProviderRegistry.list_model_providers()

    def test_anthropic_provider_registered(self):
        """Test that Anthropic provider is properly registered."""
        from nimbus.models import ProviderRegistry

        # Verify Anthropic provider can be retrieved
        assert "anthropic" in ProviderRegistry.list_model_providers()

    def test_bedrock_provider_registered(self):
        """Test that Bedrock provider is properly registered."""
        from nimbus.models import ProviderRegistry

        # Verify Bedrock provider can be retrieved
        assert "bedrock" in ProviderRegistry.list_model_providers()

    def test_azure_provider_registered(self):
        """Test that Azure OpenAI provider is properly registered."""
        from nimbus.models import ProviderRegistry

        # Verify Azure provider can be retrieved
        assert "azure" in ProviderRegistry.list_model_providers()

    def test_vertex_provider_registered(self):
        """Test that Vertex AI provider is properly registered."""
        from nimbus.models import ProviderRegistry

        # Verify Vertex provider can be retrieved
        assert "vertex" in ProviderRegistry.list_model_providers()

    def test_openai_embedding_provider_registered(self):
        """Test that OpenAI embedding provider is properly registered."""
        from nimbus.models import ProviderRegistry

        # Verify OpenAI embedding provider can be retrieved
        assert "openai" in ProviderRegistry.list_embedding_providers()

    def test_bedrock_embedding_provider_registered(self):
        """Test that Bedrock embedding provider is properly registered."""
        from nimbus.models import ProviderRegistry

        # Verify Bedrock embedding provider can be retrieved
        assert "bedrock" in ProviderRegistry.list_embedding_providers()

    def test_cohere_embedding_provider_registered(self):
        """Test that Cohere embedding provider is properly registered."""
        from nimbus.models import ProviderRegistry

        # Verify Cohere embedding provider can be retrieved
        assert "cohere" in ProviderRegistry.list_embedding_providers()

    def test_vertex_embedding_provider_registered(self):
        """Test that Vertex embedding provider is properly registered."""
        from nimbus.models import ProviderRegistry

        # Verify Vertex embedding provider can be retrieved
        assert "vertex" in ProviderRegistry.list_embedding_providers()

    def test_vertex_multimodal_embedding_provider_registered(self):
        """Test that Vertex multimodal embedding provider is properly registered."""
        from nimbus.models import ProviderRegistry

        # Verify Vertex multimodal embedding provider can be retrieved
        assert "vertex-multimodal" in ProviderRegistry.list_embedding_providers()

    def test_all_model_providers_count(self):
        """Test that all expected model providers are registered."""
        from nimbus.models import ProviderRegistry

        model_providers = ProviderRegistry.list_model_providers()
        # Should have 5 model providers: openai, anthropic, bedrock, azure, vertex
        assert len(model_providers) == 5

    def test_all_embedding_providers_count(self):
        """Test that all expected embedding providers are registered."""
        from nimbus.models import ProviderRegistry

        embedding_providers = ProviderRegistry.list_embedding_providers()
        # Should have 5 embedding providers: openai, bedrock, cohere, vertex, vertex-multimodal
        assert len(embedding_providers) == 5

    def test_provider_classes_are_registered(self):
        """Test that provider classes are properly registered."""
        from nimbus.models import (
            AnthropicProvider,
            AzureOpenAIProvider,
            BedrockProvider,
            OpenAIProvider,
            ProviderRegistry,
            VertexAIProvider,
        )

        # Verify that the registered classes match the expected classes
        assert ProviderRegistry._model_providers["openai"] == OpenAIProvider
        assert ProviderRegistry._model_providers["anthropic"] == AnthropicProvider
        assert ProviderRegistry._model_providers["bedrock"] == BedrockProvider
        assert ProviderRegistry._model_providers["azure"] == AzureOpenAIProvider
        assert ProviderRegistry._model_providers["vertex"] == VertexAIProvider

    def test_embedding_provider_classes_are_registered(self):
        """Test that embedding provider classes are properly registered."""
        from nimbus.models import (
            BedrockEmbeddingProvider,
            CohereEmbeddingProvider,
            OpenAIEmbeddingProvider,
            ProviderRegistry,
            VertexEmbeddingProvider,
            VertexMultimodalEmbeddingProvider,
        )

        # Verify that the registered classes match the expected classes
        assert ProviderRegistry._embedding_providers["openai"] == OpenAIEmbeddingProvider
        assert ProviderRegistry._embedding_providers["bedrock"] == BedrockEmbeddingProvider
        assert ProviderRegistry._embedding_providers["cohere"] == CohereEmbeddingProvider
        assert ProviderRegistry._embedding_providers["vertex"] == VertexEmbeddingProvider
        assert (
            ProviderRegistry._embedding_providers["vertex-multimodal"]
            == VertexMultimodalEmbeddingProvider
        )

    def test_registry_lists_all_providers(self):
        """Test that registry lists all registered providers."""
        from nimbus.models import ProviderRegistry

        model_providers = ProviderRegistry.list_model_providers()
        embedding_providers = ProviderRegistry.list_embedding_providers()

        # Verify both lists are non-empty
        assert len(model_providers) > 0
        assert len(embedding_providers) > 0

        # Verify they contain expected providers
        expected_models = {"openai", "anthropic", "bedrock", "azure", "vertex"}
        expected_embeddings = {"openai", "bedrock", "cohere", "vertex", "vertex-multimodal"}

        assert set(model_providers) == expected_models
        assert set(embedding_providers) == expected_embeddings
