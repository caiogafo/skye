"""Tests for package exports."""

import nimbus


def test_version_export():
    """Test that __version__ is exported."""
    assert hasattr(nimbus, "__version__")
    assert isinstance(nimbus.__version__, str)


def test_all_defined():
    """Test that __all__ is properly defined."""
    assert hasattr(nimbus, "__all__")
    assert isinstance(nimbus.__all__, list)
    assert len(nimbus.__all__) > 0


def test_exception_exports():
    """Test that all exceptions are importable from nimbus."""
    from nimbus import (
        CapabilityExecutionError,
        ConfigurationError,
        NimbusError,
        ProviderError,
        ValidationError,
    )

    # Verify they are exception classes
    assert issubclass(NimbusError, Exception)
    assert issubclass(ProviderError, NimbusError)
    assert issubclass(ConfigurationError, NimbusError)
    assert issubclass(ValidationError, NimbusError)
    assert issubclass(CapabilityExecutionError, NimbusError)


def test_message_exports():
    """Test that all message types are importable from nimbus."""
    from nimbus import (
        AssistantMessage,
        CapabilityMessage,
        ContentChunk,
        NimbusMessage,
        SystemMessage,
        UserMessage,
    )

    # Verify they are classes
    assert isinstance(NimbusMessage, type)
    assert isinstance(UserMessage, type)
    assert isinstance(AssistantMessage, type)
    assert isinstance(SystemMessage, type)
    assert isinstance(CapabilityMessage, type)
    assert isinstance(ContentChunk, type)


def test_completion_exports():
    """Test that completion models are importable from nimbus."""
    from nimbus import (
        CompletionRequest,
        CompletionResponse,
        StreamChunk,
        TokenUsage,
    )

    # Verify they are classes
    assert isinstance(TokenUsage, type)
    assert isinstance(CompletionRequest, type)
    assert isinstance(CompletionResponse, type)
    assert isinstance(StreamChunk, type)


def test_config_exports():
    """Test that configuration models and loader are importable from nimbus."""
    from nimbus import (
        ConfigLoader,
        CooldownConfig,
        ModelConfig,
        NimbusConfig,
        RateLimitConfig,
        RetryConfig,
    )

    # Verify they are classes
    assert isinstance(RateLimitConfig, type)
    assert isinstance(RetryConfig, type)
    assert isinstance(CooldownConfig, type)
    assert isinstance(ModelConfig, type)
    assert isinstance(NimbusConfig, type)
    assert isinstance(ConfigLoader, type)


def test_interface_exports():
    """Test that all interfaces are importable from nimbus."""
    from nimbus import (
        CapabilityInterface,
        CapabilitySchema,
        ContentReaderInterface,
        EventHandlerInterface,
        EventType,
        MemoryInterface,
        ModelInterface,
        ModelRouterInterface,
        ObserverInterface,
        PluginInterface,
        PromptBuilderInterface,
        RoutingStrategy,
        SafetyFilterInterface,
        SafetyResult,
        StorageAdapterInterface,
        VectorEncoderInterface,
    )

    # Verify they are classes or types
    assert isinstance(ModelInterface, type)
    assert isinstance(PromptBuilderInterface, type)
    assert isinstance(CapabilityInterface, type)
    assert isinstance(CapabilitySchema, type)
    assert isinstance(MemoryInterface, type)
    assert isinstance(SafetyFilterInterface, type)
    assert isinstance(SafetyResult, type)
    assert isinstance(ObserverInterface, type)
    assert isinstance(EventType, type)
    assert isinstance(StorageAdapterInterface, type)
    assert isinstance(PluginInterface, type)
    assert isinstance(EventHandlerInterface, type)
    assert isinstance(VectorEncoderInterface, type)
    assert isinstance(ContentReaderInterface, type)
    assert isinstance(ModelRouterInterface, type)
    assert isinstance(RoutingStrategy, type)


def test_all_exports_in_all_list():
    """Test that all exported symbols are in __all__."""
    from nimbus import __all__

    # Test a sample of key exports
    expected_exports = [
        "__version__",
        "NimbusError",
        "UserMessage",
        "CompletionRequest",
        "ModelConfig",
        "ConfigLoader",
        "ModelInterface",
        "CapabilityInterface",
        "MemoryInterface",
    ]

    for export in expected_exports:
        assert export in __all__, f"{export} not in __all__"


def test_combined_import():
    """Test that multiple symbols can be imported together."""
    from nimbus import ConfigLoader, ModelInterface, NimbusError, UserMessage

    # Verify all imports succeeded
    assert ModelInterface is not None
    assert UserMessage is not None
    assert NimbusError is not None
    assert ConfigLoader is not None


def test_all_list_matches_exports():
    """Test that __all__ contains all expected exports."""
    from nimbus import __all__

    # Count expected exports
    expected_count = (
        1  # __version__
        + 5  # Exceptions
        + 6  # Messages
        + 4  # Completion
        + 6  # Configuration
        + 16  # Interfaces
    )

    assert len(__all__) == expected_count, f"Expected {expected_count} exports, got {len(__all__)}"


def test_no_unexpected_exports():
    """Test that only expected symbols are exported."""
    import types

    import nimbus

    # Get all public attributes that are not modules
    public_attrs = [
        attr
        for attr in dir(nimbus)
        if not attr.startswith("_") and not isinstance(getattr(nimbus, attr), types.ModuleType)
    ]

    # All public non-module attributes should be in __all__
    for attr in public_attrs:
        assert attr in nimbus.__all__, f"Unexpected public export: {attr}"
