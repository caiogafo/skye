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
    """Test that all exceptions are importable from nimbus.base.exceptions."""
    from nimbus.base.exceptions import (
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
    """Test that all message types are importable from nimbus.base.messages."""
    from nimbus.base.messages import (
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
    """Test that completion models are importable from nimbus.base.completion."""
    from nimbus.base.completion import (
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
    """Test that configuration models and loader are importable from nimbus.base.config."""
    from nimbus.base.config import (
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
    """Test that all interfaces are importable from nimbus.base.interfaces."""
    from nimbus.base.interfaces import (
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


CURATED = ["messages", "completion", "exceptions", "config"]


def test_all_exports_in_all_list():
    """__all__ is exactly the version plus the four curated base modules (Req 6.5)."""
    from nimbus import __all__

    assert __all__ == ["__version__", *CURATED]


def test_curated_top_level_modules():
    """The four curated re-exports are the base modules."""
    import types

    import nimbus

    for name in CURATED:
        assert isinstance(getattr(nimbus, name), types.ModuleType), name


def test_combined_import():
    """Multiple symbols can be imported together from their Component paths."""
    from nimbus.base.config import ConfigLoader
    from nimbus.base.exceptions import NimbusError
    from nimbus.base.interfaces import ModelInterface
    from nimbus.base.messages import UserMessage

    assert ModelInterface is not None
    assert UserMessage is not None
    assert NimbusError is not None
    assert ConfigLoader is not None


def test_removed_names_not_reexported():
    """Names re-exported before task 10.1 are no longer on the top-level package."""
    import nimbus

    for name in ["provider", "ModelRouter", "UserMessage", "NimbusError",
                 "ConfigLoader", "ModelInterface", "MemoryInterface"]:
        assert not hasattr(nimbus, name), name


def test_all_exports_exist():
    """Every item in __all__ exists."""
    import nimbus

    for export_name in nimbus.__all__:
        assert getattr(nimbus, export_name) is not None, export_name
