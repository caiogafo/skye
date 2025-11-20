"""Tests for capability package exports.

This module verifies that all expected symbols are properly exported from
the nimbus.capabilities package and that __all__ is correctly defined.
"""

import pytest


def test_capability_interface_import():
    """Test that CapabilityInterface can be imported."""
    from nimbus.capabilities import CapabilityInterface
    
    assert CapabilityInterface is not None
    assert hasattr(CapabilityInterface, "get_schema")
    assert hasattr(CapabilityInterface, "execute")
    assert hasattr(CapabilityInterface, "aexecute")


def test_capability_schema_import():
    """Test that CapabilitySchema can be imported."""
    from nimbus.capabilities import CapabilitySchema
    
    assert CapabilitySchema is not None


def test_capability_registry_import():
    """Test that CapabilityRegistry can be imported."""
    from nimbus.capabilities import CapabilityRegistry
    
    assert CapabilityRegistry is not None
    assert hasattr(CapabilityRegistry, "register")
    assert hasattr(CapabilityRegistry, "get")
    assert hasattr(CapabilityRegistry, "list_all")
    assert hasattr(CapabilityRegistry, "unregister")


def test_local_function_capability_import():
    """Test that LocalFunctionCapability can be imported."""
    from nimbus.capabilities import LocalFunctionCapability
    
    assert LocalFunctionCapability is not None


def test_remote_api_capability_import():
    """Test that RemoteAPICapability can be imported."""
    from nimbus.capabilities import RemoteAPICapability
    
    assert RemoteAPICapability is not None


def test_tool_call_import():
    """Test that ToolCall can be imported."""
    from nimbus.capabilities import ToolCall
    
    assert ToolCall is not None


def test_tool_result_import():
    """Test that ToolResult can be imported."""
    from nimbus.capabilities import ToolResult
    
    assert ToolResult is not None


def test_exception_imports():
    """Test that all exception classes can be imported."""
    from nimbus.capabilities import (
        CapabilityError,
        CapabilityExecutionError,
        CapabilityNotFoundError,
        CapabilityValidationError,
        ToolCallParsingError,
    )
    
    assert CapabilityError is not None
    assert CapabilityExecutionError is not None
    assert CapabilityNotFoundError is not None
    assert CapabilityValidationError is not None
    assert ToolCallParsingError is not None
    
    # Verify inheritance
    assert issubclass(CapabilityExecutionError, CapabilityError)
    assert issubclass(CapabilityNotFoundError, CapabilityError)
    assert issubclass(CapabilityValidationError, CapabilityError)
    assert issubclass(ToolCallParsingError, CapabilityError)


def test_tool_transformer_import():
    """Test that ToolTransformer can be imported."""
    from nimbus.capabilities import ToolTransformer
    
    assert ToolTransformer is not None
    assert hasattr(ToolTransformer, "to_openai_format")
    assert hasattr(ToolTransformer, "to_anthropic_format")
    assert hasattr(ToolTransformer, "to_bedrock_format")
    assert hasattr(ToolTransformer, "to_vertex_format")


def test_tool_call_handler_import():
    """Test that ToolCallHandler can be imported."""
    from nimbus.capabilities import ToolCallHandler
    
    assert ToolCallHandler is not None
    assert hasattr(ToolCallHandler, "parse_tool_calls")
    assert hasattr(ToolCallHandler, "execute_tool_calls")
    assert hasattr(ToolCallHandler, "format_tool_results")


def test_mcp_capability_import():
    """Test that MCPCapability can be imported."""
    from nimbus.capabilities import MCPCapability
    
    assert MCPCapability is not None


def test_mcp_server_client_import():
    """Test that MCPServerClient can be imported."""
    from nimbus.capabilities import MCPServerClient
    
    assert MCPServerClient is not None


def test_capability_decorator_import():
    """Test that capability decorator can be imported."""
    from nimbus.capabilities import capability
    
    assert capability is not None
    assert callable(capability)


def test_all_defined():
    """Test that __all__ is properly defined."""
    import nimbus.capabilities
    
    assert hasattr(nimbus.capabilities, "__all__")
    assert isinstance(nimbus.capabilities.__all__, list)
    assert len(nimbus.capabilities.__all__) > 0


def test_all_contains_expected_symbols():
    """Test that __all__ contains all expected symbols."""
    import nimbus.capabilities
    
    expected_symbols = [
        "CapabilityInterface",
        "CapabilitySchema",
        "CapabilityRegistry",
        "LocalFunctionCapability",
        "RemoteAPICapability",
        "ToolCall",
        "ToolResult",
        "CapabilityError",
        "CapabilityExecutionError",
        "CapabilityNotFoundError",
        "CapabilityValidationError",
        "ToolCallParsingError",
        "ToolTransformer",
        "ToolCallHandler",
        "MCPCapability",
        "MCPServerClient",
        "capability",
    ]
    
    for symbol in expected_symbols:
        assert symbol in nimbus.capabilities.__all__, f"{symbol} not in __all__"


def test_all_symbols_are_importable():
    """Test that all symbols in __all__ can be imported."""
    import nimbus.capabilities
    
    for symbol in nimbus.capabilities.__all__:
        assert hasattr(nimbus.capabilities, symbol), f"{symbol} not importable"


def test_star_import():
    """Test that star import works correctly."""
    # This test verifies that 'from nimbus.capabilities import *' works
    namespace = {}
    exec("from nimbus.capabilities import *", namespace)
    
    expected_symbols = [
        "CapabilityInterface",
        "CapabilitySchema",
        "CapabilityRegistry",
        "LocalFunctionCapability",
        "RemoteAPICapability",
        "ToolCall",
        "ToolResult",
        "CapabilityError",
        "CapabilityExecutionError",
        "CapabilityNotFoundError",
        "CapabilityValidationError",
        "ToolCallParsingError",
    ]
    
    for symbol in expected_symbols:
        assert symbol in namespace, f"{symbol} not available via star import"


def test_combined_import():
    """Test that multiple symbols can be imported together."""
    from nimbus.capabilities import (
        CapabilityInterface,
        CapabilityRegistry,
        CapabilitySchema,
        LocalFunctionCapability,
        RemoteAPICapability,
        ToolCall,
        ToolResult,
    )
    
    assert CapabilityInterface is not None
    assert CapabilityRegistry is not None
    assert CapabilitySchema is not None
    assert LocalFunctionCapability is not None
    assert RemoteAPICapability is not None
    assert ToolCall is not None
    assert ToolResult is not None


def test_no_private_symbols_in_all():
    """Test that __all__ doesn't contain private symbols."""
    import nimbus.capabilities
    
    for symbol in nimbus.capabilities.__all__:
        assert not symbol.startswith("_"), f"Private symbol {symbol} in __all__"


def test_package_docstring():
    """Test that the package has a docstring."""
    import nimbus.capabilities
    
    assert nimbus.capabilities.__doc__ is not None
    assert len(nimbus.capabilities.__doc__) > 0
    assert "capability" in nimbus.capabilities.__doc__.lower()
