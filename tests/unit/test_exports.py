"""Tests for package exports."""

import skye


def test_version_export():
    """Test that __version__ is exported."""
    assert hasattr(skye, "__version__")
    assert isinstance(skye.__version__, str)


def test_all_defined():
    """Test that __all__ is properly defined."""
    assert hasattr(skye, "__all__")
    assert isinstance(skye.__all__, list)
    assert len(skye.__all__) > 0


def test_provider_is_exported_and_loads_the_registry_only_when_called():
    """`skye.provider(name, **config)` is the boto3-style way to create a client; `import skye` must not import `skye.models`."""
    import subprocess
    import sys

    assert "provider" in skye.__all__
    code = (
        "import sys, skye; assert 'skye.models' not in sys.modules; "
        "c = skye.provider('openai', api_key='k'); assert hasattr(c, 'complete') and hasattr(c, 'stream'); "
        "e = skye.provider('openai', model='text-embedding-3-small', api_key='k', provider_type='embedding'); "
        "assert hasattr(e, 'encode_batch'); assert 'skye.models' in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_exception_exports():
    """Test that all exceptions are importable from skye.base.exceptions."""
    from skye.base.exceptions import (
        CapabilityExecutionError,
        ConfigurationError,
        SkyeError,
        ProviderError,
        ValidationError,
    )

    # Verify they are exception classes
    assert issubclass(SkyeError, Exception)
    assert issubclass(ProviderError, SkyeError)
    assert issubclass(ConfigurationError, SkyeError)
    assert issubclass(ValidationError, SkyeError)
    assert issubclass(CapabilityExecutionError, SkyeError)


def test_message_exports():
    """Test that all message types are importable from skye.base.messages."""
    from skye.base.messages import (
        AssistantMessage,
        CapabilityMessage,
        ContentChunk,
        SkyeMessage,
        SystemMessage,
        UserMessage,
    )

    # Verify they are classes
    assert isinstance(SkyeMessage, type)
    assert isinstance(UserMessage, type)
    assert isinstance(AssistantMessage, type)
    assert isinstance(SystemMessage, type)
    assert isinstance(CapabilityMessage, type)
    assert isinstance(ContentChunk, type)


def test_completion_exports():
    """Test that completion models are importable from skye.base.completion."""
    from skye.base.completion import (
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
    """Test that configuration models and loader are importable from skye.base.config."""
    from skye.base.config import (
        ConfigLoader,
        CooldownConfig,
        ModelConfig,
        SkyeConfig,
        RateLimitConfig,
        RetryConfig,
    )

    # Verify they are classes
    assert isinstance(RateLimitConfig, type)
    assert isinstance(RetryConfig, type)
    assert isinstance(CooldownConfig, type)
    assert isinstance(ModelConfig, type)
    assert isinstance(SkyeConfig, type)
    assert isinstance(ConfigLoader, type)


def test_interface_exports():
    """Test that all interfaces are importable from skye.base.interfaces."""
    from skye.base.interfaces import (
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
    """__all__ is the version, the four curated base modules and the lazy `provider` function (Requirement 7.8, decision D28)."""
    from skye import __all__

    assert __all__ == ["__version__", *CURATED, "provider"]


def test_curated_top_level_modules():
    """The four curated re-exports are the base modules."""
    import types

    import skye

    for name in CURATED:
        assert isinstance(getattr(skye, name), types.ModuleType), name


def test_combined_import():
    """Multiple symbols can be imported together from their Component paths."""
    from skye.base.config import ConfigLoader
    from skye.base.exceptions import SkyeError
    from skye.base.interfaces import ModelInterface
    from skye.base.messages import UserMessage

    assert ModelInterface is not None
    assert UserMessage is not None
    assert SkyeError is not None
    assert ConfigLoader is not None


def test_removed_names_not_reexported():
    """Names re-exported before task 10.1 are no longer on the top-level package (`provider` came back as a lazy function, D28)."""
    import skye

    for name in ["ModelRouter", "UserMessage", "SkyeError",
                 "ConfigLoader", "ModelInterface", "MemoryInterface"]:
        assert not hasattr(skye, name), name


def test_all_exports_exist():
    """Every item in __all__ exists."""
    import skye

    for export_name in skye.__all__:
        assert getattr(skye, export_name) is not None, export_name
