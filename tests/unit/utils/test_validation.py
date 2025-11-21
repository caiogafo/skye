"""Tests for validation utilities."""

from abc import ABC, abstractmethod

import pytest
from pydantic import BaseModel, Field

from nimbus.completion import CompletionRequest
from nimbus.exceptions import ValidationError
from nimbus.interfaces import ModelInterface
from nimbus.messages import AssistantMessage, ContentChunk, UserMessage
from nimbus.utils.validation import generate_schema, validate_interface_compliance


# Test fixtures - Mock interfaces and implementations
class SimpleInterface(ABC):
    """Simple test interface."""

    @abstractmethod
    def method_one(self) -> str:
        """First method."""
        pass

    @abstractmethod
    def method_two(self, arg: int) -> int:
        """Second method."""
        pass


class CompliantImplementation(SimpleInterface):
    """Compliant implementation of SimpleInterface."""

    def method_one(self) -> str:
        return "implemented"

    def method_two(self, arg: int) -> int:
        return arg * 2


class PartialImplementation(SimpleInterface):
    """Partial implementation missing method_two."""

    def method_one(self) -> str:
        return "implemented"


class NonInheritingClass:
    """Class that doesn't inherit from the interface."""

    def method_one(self) -> str:
        return "implemented"

    def method_two(self, arg: int) -> int:
        return arg * 2


# Test interface compliance validation
def test_interface_compliance_with_compliant_implementation():
    """Test that compliant implementations pass validation."""
    impl = CompliantImplementation()
    # Should not raise any exception
    validate_interface_compliance(impl, SimpleInterface)


def test_interface_compliance_with_class():
    """Test that validation works with classes (not just instances)."""
    # Should not raise any exception
    validate_interface_compliance(CompliantImplementation, SimpleInterface)


def test_interface_compliance_with_partial_implementation():
    """Test that partial implementations fail validation."""
    # Pass the class itself since we can't instantiate abstract classes
    with pytest.raises(ValidationError) as exc_info:
        validate_interface_compliance(PartialImplementation, SimpleInterface)

    error = exc_info.value
    assert "missing required methods" in error.message.lower()
    assert "method_two" in error.message
    assert error.details["field"] == "abstract_methods"
    assert "method_two" in error.details["value"]


def test_interface_compliance_with_non_inheriting_class():
    """Test that non-inheriting classes fail validation."""
    impl = NonInheritingClass()
    with pytest.raises(ValidationError) as exc_info:
        validate_interface_compliance(impl, SimpleInterface)

    error = exc_info.value
    assert "does not inherit" in error.message.lower()
    assert error.details["field"] == "interface_inheritance"


def test_interface_compliance_with_model_interface():
    """Test validation with a real Nimbus interface."""

    # Create a partial implementation of ModelInterface
    class PartialModel(ModelInterface):
        def complete(self, request):
            return None

        def get_model_info(self):
            return {}

        # Missing: stream, acomplete, astream

    # Pass the class itself since we can't instantiate abstract classes
    with pytest.raises(ValidationError) as exc_info:
        validate_interface_compliance(PartialModel, ModelInterface)

    error = exc_info.value
    assert "missing required methods" in error.message.lower()
    # Should mention at least one missing method
    missing_methods = error.details["value"]
    assert any(method in missing_methods for method in ["stream", "acomplete", "astream"])


def test_interface_compliance_error_includes_helpful_context():
    """Test that ValidationError includes helpful context."""
    # Pass the class itself since we can't instantiate abstract classes
    with pytest.raises(ValidationError) as exc_info:
        validate_interface_compliance(PartialImplementation, SimpleInterface)

    error = exc_info.value
    # Check that error details include useful information
    assert "interface" in error.details
    assert "implementation" in error.details
    assert error.details["interface"] == "SimpleInterface"
    assert error.details["implementation"] == "PartialImplementation"


# Test schema generation
def test_schema_generation_for_user_message():
    """Test schema generation for UserMessage."""
    schema = generate_schema(UserMessage)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "content" in schema["properties"]
    assert "role" in schema["properties"]
    assert "metadata" in schema["properties"]


def test_schema_generation_for_assistant_message():
    """Test schema generation for AssistantMessage."""
    schema = generate_schema(AssistantMessage)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "content" in schema["properties"]
    assert "capability_calls" in schema["properties"]


def test_schema_generation_for_content_chunk():
    """Test schema generation for ContentChunk."""
    schema = generate_schema(ContentChunk)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "text" in schema["properties"]
    assert "metadata" in schema["properties"]


def test_schema_generation_for_completion_request():
    """Test schema generation for CompletionRequest."""
    schema = generate_schema(CompletionRequest)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "messages" in schema["properties"]
    assert "model" in schema["properties"]
    assert "temperature" in schema["properties"]


def test_schema_generation_for_nested_model():
    """Test schema generation for models with nested structures."""

    class Address(BaseModel):
        street: str
        city: str
        zip_code: str

    class Person(BaseModel):
        name: str
        age: int
        address: Address

    schema = generate_schema(Person)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "address" in schema["properties"]
    # Check that nested model is properly referenced
    assert "$defs" in schema or "definitions" in schema


def test_schema_generation_with_field_constraints():
    """Test that schema generation includes field constraints."""

    class ConstrainedModel(BaseModel):
        name: str = Field(min_length=1, max_length=100)
        age: int = Field(gt=0, le=150)
        score: float = Field(ge=0.0, le=1.0)

    schema = generate_schema(ConstrainedModel)

    assert schema["type"] == "object"
    properties = schema["properties"]

    # Check string constraints
    assert properties["name"]["minLength"] == 1
    assert properties["name"]["maxLength"] == 100

    # Check integer constraints
    assert properties["age"]["exclusiveMinimum"] == 0
    assert properties["age"]["maximum"] == 150

    # Check float constraints
    assert properties["score"]["minimum"] == 0.0
    assert properties["score"]["maximum"] == 1.0


def test_schema_generation_with_invalid_input():
    """Test that schema generation fails with non-Pydantic models."""

    class NotAPydanticModel:
        def __init__(self):
            self.value = 42

    with pytest.raises(ValidationError) as exc_info:
        generate_schema(NotAPydanticModel)

    error = exc_info.value
    assert "expected a pydantic basemodel" in error.message.lower()
    assert error.details["field"] == "model_type"


def test_schema_generation_with_instance_instead_of_class():
    """Test that schema generation fails when passed an instance."""
    msg = UserMessage(content="test")

    with pytest.raises(ValidationError) as exc_info:
        generate_schema(msg)  # type: ignore

    error = exc_info.value
    assert "expected a pydantic basemodel" in error.message.lower()
