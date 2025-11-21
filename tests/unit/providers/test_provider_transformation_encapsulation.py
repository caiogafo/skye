"""Tests for provider transformation encapsulation.

This module tests that all provider-specific transformation logic is properly
encapsulated within provider client classes, and that the core library remains
provider-agnostic.

**Validates: Requirements 9.1, 9.2, 9.3**
"""

import inspect
from typing import Any

import pytest

from nimbus.capabilities.capability_transformer import CapabilityTransformer
from nimbus.capabilities.interface import CapabilityInterface
from nimbus.messages import NimbusMessage, UserMessage
from nimbus.providers.base import BaseModelProvider
from nimbus.providers.transformers import MessageTransformer


class TestMessageTransformerProviderAgnostic:
    """Test that MessageTransformer has no provider-specific logic."""

    def test_message_transformer_only_has_delegation_method(self):
        """MessageTransformer should only have the delegation method."""
        methods = [
            name for name, method in inspect.getmembers(MessageTransformer, predicate=inspect.isfunction)
            if not name.startswith('_')
        ]
        
        # Should only have transform_for_provider
        assert methods == ['transform_for_provider'], \
            f"MessageTransformer should only have transform_for_provider, found: {methods}"

    def test_message_transformer_has_no_provider_specific_methods(self):
        """MessageTransformer should not have any provider-specific methods."""
        methods = dir(MessageTransformer)
        
        # Check that no provider-specific methods exist
        provider_specific_methods = [
            'to_openai_format',
            'to_anthropic_format',
            'to_bedrock_format',
            'to_vertex_format',
            'to_azure_format'
        ]
        
        for method in provider_specific_methods:
            assert method not in methods, \
                f"MessageTransformer should not have {method} method"

    def test_message_transformer_delegation_calls_provider_method(self):
        """transform_for_provider should delegate to provider's _transform_messages."""
        
        class MockProvider:
            def _transform_messages(self, messages: list[NimbusMessage]) -> list[dict[str, Any]]:
                return [{"role": "user", "content": "mocked"}]
        
        messages = [UserMessage(content="test")]
        provider = MockProvider()
        
        result = MessageTransformer.transform_for_provider(messages, provider)
        
        assert result == [{"role": "user", "content": "mocked"}]


class TestCapabilityTransformerProviderAgnostic:
    """Test that CapabilityTransformer has no provider-specific logic."""

    def test_capability_transformer_only_has_delegation_method(self):
        """CapabilityTransformer should only have the delegation method."""
        methods = [
            name for name, method in inspect.getmembers(CapabilityTransformer, predicate=inspect.isfunction)
            if not name.startswith('_')
        ]
        
        # Should only have transform_for_provider
        assert methods == ['transform_for_provider'], \
            f"CapabilityTransformer should only have transform_for_provider, found: {methods}"

    def test_capability_transformer_has_no_provider_specific_methods(self):
        """CapabilityTransformer should not have any provider-specific methods."""
        methods = dir(CapabilityTransformer)
        
        # Check that no provider-specific methods exist
        provider_specific_methods = [
            'to_openai_format',
            'to_anthropic_format',
            'to_bedrock_format',
            'to_vertex_format',
            'to_azure_format'
        ]
        
        for method in provider_specific_methods:
            assert method not in methods, \
                f"CapabilityTransformer should not have {method} method"

    def test_capability_transformer_delegation_calls_provider_method(self):
        """transform_for_provider should delegate to provider's _transform_capabilities."""
        
        class MockCapability(CapabilityInterface):
            def get_schema(self):
                return type('Schema', (), {
                    'name': 'test',
                    'description': 'test',
                    'parameters': {}
                })()
            
            def execute(self, **kwargs):
                return "test"
            
            async def aexecute(self, **kwargs):
                return "test"
        
        class MockProvider:
            def _transform_capabilities(self, capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
                return [{"type": "function", "function": {"name": "mocked"}}]
        
        capabilities = [MockCapability()]
        provider = MockProvider()
        
        result = CapabilityTransformer.transform_for_provider(capabilities, provider)
        
        assert result == [{"type": "function", "function": {"name": "mocked"}}]


class TestProviderTransformationMethods:
    """Test that providers have all required transformation methods."""

    def test_base_provider_defines_transformation_methods(self):
        """BaseModelProvider should define all transformation methods as abstract."""
        # Check that the abstract methods are defined
        abstract_methods = BaseModelProvider.__abstractmethods__
        
        assert '_transform_messages' in abstract_methods, \
            "BaseModelProvider should have abstract _transform_messages method"
        assert '_transform_capabilities' in abstract_methods, \
            "BaseModelProvider should have abstract _transform_capabilities method"
        assert '_extract_capability_calls' in abstract_methods, \
            "BaseModelProvider should have abstract _extract_capability_calls method"

    def test_openai_provider_implements_transformation_methods(self):
        """OpenAIProvider should implement all transformation methods."""
        from nimbus.providers.llm.openai_provider import OpenAIProvider
        
        # Check that methods are implemented
        assert hasattr(OpenAIProvider, '_transform_messages'), \
            "OpenAIProvider should implement _transform_messages"
        assert hasattr(OpenAIProvider, '_transform_capabilities'), \
            "OpenAIProvider should implement _transform_capabilities"
        assert hasattr(OpenAIProvider, '_extract_capability_calls'), \
            "OpenAIProvider should implement _extract_capability_calls"
        
        # Check that they're not abstract
        assert '_transform_messages' not in OpenAIProvider.__abstractmethods__, \
            "OpenAIProvider._transform_messages should not be abstract"
        assert '_transform_capabilities' not in OpenAIProvider.__abstractmethods__, \
            "OpenAIProvider._transform_capabilities should not be abstract"
        assert '_extract_capability_calls' not in OpenAIProvider.__abstractmethods__, \
            "OpenAIProvider._extract_capability_calls should not be abstract"

    def test_bedrock_provider_implements_transformation_methods(self):
        """BedrockProvider should implement all transformation methods."""
        from nimbus.providers.llm.bedrock_provider import BedrockProvider
        
        # Check that methods are implemented
        assert hasattr(BedrockProvider, '_transform_messages'), \
            "BedrockProvider should implement _transform_messages"
        assert hasattr(BedrockProvider, '_transform_capabilities'), \
            "BedrockProvider should implement _transform_capabilities"
        assert hasattr(BedrockProvider, '_extract_capability_calls'), \
            "BedrockProvider should implement _extract_capability_calls"
        
        # Check that they're not abstract
        assert '_transform_messages' not in BedrockProvider.__abstractmethods__, \
            "BedrockProvider._transform_messages should not be abstract"
        assert '_transform_capabilities' not in BedrockProvider.__abstractmethods__, \
            "BedrockProvider._transform_capabilities should not be abstract"
        assert '_extract_capability_calls' not in BedrockProvider.__abstractmethods__, \
            "BedrockProvider._extract_capability_calls should not be abstract"


class TestDelegationPattern:
    """Test that the delegation pattern works correctly."""

    def test_message_transformer_delegates_to_provider(self):
        """MessageTransformer should delegate to provider's internal method."""
        
        class TestProvider:
            def __init__(self):
                self.called = False
                self.received_messages = None
            
            def _transform_messages(self, messages: list[NimbusMessage]) -> list[dict[str, Any]]:
                self.called = True
                self.received_messages = messages
                return [{"transformed": True}]
        
        provider = TestProvider()
        messages = [UserMessage(content="test")]
        
        result = MessageTransformer.transform_for_provider(messages, provider)
        
        assert provider.called, "Provider's _transform_messages should be called"
        assert provider.received_messages == messages, "Provider should receive the messages"
        assert result == [{"transformed": True}], "Should return provider's result"

    def test_capability_transformer_delegates_to_provider(self):
        """CapabilityTransformer should delegate to provider's internal method."""
        
        class MockCapability(CapabilityInterface):
            def get_schema(self):
                return type('Schema', (), {
                    'name': 'test',
                    'description': 'test',
                    'parameters': {}
                })()
            
            def execute(self, **kwargs):
                return "test"
            
            async def aexecute(self, **kwargs):
                return "test"
        
        class TestProvider:
            def __init__(self):
                self.called = False
                self.received_capabilities = None
            
            def _transform_capabilities(self, capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
                self.called = True
                self.received_capabilities = capabilities
                return [{"transformed": True}]
        
        provider = TestProvider()
        capabilities = [MockCapability()]
        
        result = CapabilityTransformer.transform_for_provider(capabilities, provider)
        
        assert provider.called, "Provider's _transform_capabilities should be called"
        assert provider.received_capabilities == capabilities, "Provider should receive the capabilities"
        assert result == [{"transformed": True}], "Should return provider's result"

    def test_provider_encapsulates_all_transformation_logic(self):
        """Provider should handle all its own transformations without external helpers."""
        from nimbus.providers.llm.openai_provider import OpenAIProvider
        
        # Get the source code of _transform_request
        source = inspect.getsource(OpenAIProvider._transform_request)
        
        # Should not call external transformer classes
        assert 'MessageTransformer.to_' not in source, \
            "Provider should not call MessageTransformer.to_* methods"
        assert 'CapabilityTransformer.to_' not in source, \
            "Provider should not call CapabilityTransformer.to_* methods"
        
        # Should call internal methods
        assert 'self._transform_messages' in source or '_transform_messages' in source, \
            "Provider should call its own _transform_messages method"
