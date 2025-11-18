"""Basic Nimbus Usage Example.

This example demonstrates the core concepts of Nimbus:
- Creating completion requests with messages
- Using different message types
- Working with token usage
- Handling structured outputs
- Using prompt templates with PromptBuilderInterface
"""

import asyncio
from datetime import datetime
from typing import Any, Callable

from nimbus.completion import CompletionRequest, CompletionResponse, TokenUsage
from nimbus.messages import UserMessage, AssistantMessage, SystemMessage, NimbusMessage
from nimbus.interfaces.prompt import PromptBuilderInterface


def basic_completion_example():
    """Example of creating a basic completion request."""
    print("=" * 60)
    print("Basic Completion Request Example")
    print("=" * 60)
    
    # Create a simple completion request
    request = CompletionRequest(
        messages=[
            SystemMessage(content="You are a helpful AI assistant."),
            UserMessage(content="What is the capital of France?")
        ],
        model="gpt-4",
        temperature=0.7,
        max_tokens=100
    )
    
    print(f"\nModel: {request.model}")
    print(f"Temperature: {request.temperature}")
    print(f"Messages: {len(request.messages)}")
    
    for i, msg in enumerate(request.messages):
        print(f"  {i+1}. [{msg.role}] {msg.content[:50]}...")
    
    # Simulate a response (in real usage, this would come from a provider)
    response = CompletionResponse(
        model="gpt-4",
        provider="openai",
        content="The capital of France is Paris.",
        finish_reason="stop",
        usage=TokenUsage(
            prompt_tokens=25,
            completion_tokens=8,
            total_tokens=33
        )
    )
    
    print(f"\nResponse:")
    print(f"  Provider: {response.provider}")
    print(f"  Content: {response.content}")
    print(f"  Tokens used: {response.usage.total_tokens}")
    print(f"  Finish reason: {response.finish_reason}")


def conversation_example():
    """Example of a multi-turn conversation."""
    print("\n" + "=" * 60)
    print("Multi-Turn Conversation Example")
    print("=" * 60)
    
    # Build a conversation history
    messages = [
        SystemMessage(content="You are a helpful coding assistant."),
        UserMessage(content="How do I create a list in Python?"),
        AssistantMessage(content="You can create a list using square brackets: my_list = [1, 2, 3]"),
        UserMessage(content="How do I add an item to it?")
    ]
    
    request = CompletionRequest(
        messages=messages,
        model="gpt-3.5-turbo",
        temperature=0.5
    )
    
    print(f"\nConversation with {len(request.messages)} messages:")
    for msg in request.messages:
        role_emoji = {"system": "⚙️", "user": "👤", "assistant": "🤖"}.get(msg.role, "❓")
        print(f"  {role_emoji} [{msg.role}] {msg.content[:60]}...")


def structured_output_example():
    """Example of requesting structured output."""
    print("\n" + "=" * 60)
    print("Structured Output Example")
    print("=" * 60)
    
    from pydantic import BaseModel
    
    # Define output schema
    class Person(BaseModel):
        name: str
        age: int
        occupation: str
    
    request = CompletionRequest(
        messages=[
            UserMessage(content="Extract person info: John is a 30-year-old software engineer.")
        ],
        model="gpt-4",
        response_schema=Person
    )
    
    print(f"\nRequesting structured output with schema: {Person.__name__}")
    print(f"  Fields: {list(Person.model_fields.keys())}")
    
    # Simulate structured response
    person = Person(name="John", age=30, occupation="software engineer")
    response = CompletionResponse(
        model="gpt-4",
        provider="openai",
        content='{"name": "John", "age": 30, "occupation": "software engineer"}',
        structured_output=person,
        finish_reason="stop",
        usage=TokenUsage(prompt_tokens=20, completion_tokens=15, total_tokens=35)
    )
    
    print(f"\nStructured output received:")
    print(f"  Name: {response.structured_output.name}")
    print(f"  Age: {response.structured_output.age}")
    print(f"  Occupation: {response.structured_output.occupation}")


def message_metadata_example():
    """Example of using message metadata."""
    print("\n" + "=" * 60)
    print("Message Metadata Example")
    print("=" * 60)
    
    # Create messages with metadata
    user_msg = UserMessage(
        content="What's the weather like?",
        metadata={
            "user_id": "user_123",
            "session_id": "session_456",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    print(f"\nMessage with metadata:")
    print(f"  Content: {user_msg.content}")
    print(f"  Metadata: {user_msg.metadata}")
    print(f"  Message ID: {user_msg.id}")
    print(f"  Timestamp: {user_msg.timestamp}")


def capability_message_example():
    """Example of capability/tool calling."""
    print("\n" + "=" * 60)
    print("Capability Message Example")
    print("=" * 60)
    
    from nimbus.messages import CapabilityMessage
    
    # Assistant calls a capability
    assistant_msg = AssistantMessage(
        content="Let me check the weather for you.",
        capability_calls=[
            {
                "id": "call_123",
                "name": "get_weather",
                "arguments": {"location": "San Francisco"}
            }
        ]
    )
    
    # Capability returns result
    capability_msg = CapabilityMessage(
        content='{"temperature": 72, "condition": "sunny"}',
        capability_id="call_123",
        capability_name="get_weather"
    )
    
    print(f"\nAssistant message with capability call:")
    print(f"  Content: {assistant_msg.content}")
    print(f"  Capability calls: {len(assistant_msg.capability_calls)}")
    print(f"    - {assistant_msg.capability_calls[0]['name']}")
    
    print(f"\nCapability result:")
    print(f"  Capability: {capability_msg.capability_name}")
    print(f"  Result: {capability_msg.content}")


def provider_formatting_example():
    """Example of provider-specific message formatting."""
    print("\n" + "=" * 60)
    print("Provider-Specific Formatting Example")
    print("=" * 60)
    
    msg = UserMessage(content="Hello, world!")
    
    # Format for different providers
    openai_format = msg.format_for_provider("openai")
    anthropic_format = msg.format_for_provider("anthropic")
    
    print(f"\nOriginal message: {msg.content}")
    print(f"OpenAI format: {openai_format}")
    print(f"Anthropic format: {anthropic_format}")


def prompt_template_example():
    """Example of using prompt templates with PromptBuilderInterface."""
    print("\n" + "=" * 60)
    print("Prompt Template Example")
    print("=" * 60)
    
    # Create a simple implementation of PromptBuilderInterface
    class SimplePromptBuilder(PromptBuilderInterface):
        """Minimal prompt builder for demonstration."""
        
        def __init__(self):
            self.templates = {}
            self.defaults = {}
            self.allowed_missing = []
        
        def render(self, template_name: str, variables: dict[str, Any]) -> list[NimbusMessage]:
            template = self.get_template(template_name)
            merged = {**self.defaults, **variables}
            content = template.format(**merged)
            return [UserMessage(content=content)]
        
        def register_template(self, name: str, template: str, version: str = "1.0", from_string: bool = True) -> None:
            key = f"{name}:{version}"
            self.templates[key] = template
        
        def get_template(self, name: str, version: str | None = None) -> str:
            key = f"{name}:{version}" if version else f"{name}:1.0"
            return self.templates.get(key, "")
        
        def get_template_variables(self, template_name: str) -> list[str]:
            import re
            template = self.get_template(template_name)
            return re.findall(r'\{(\w+)\}', template)
        
        def set_default_values(self, defaults: dict[str, Any]) -> None:
            self.defaults.update(defaults)
        
        def set_allowed_missing_variables(self, variables: list[str]) -> None:
            self.allowed_missing.extend(variables)
        
        def partial(self, **kwargs) -> "PromptBuilderInterface":
            new_builder = SimplePromptBuilder()
            new_builder.templates = self.templates.copy()
            new_builder.defaults = {**self.defaults, **kwargs}
            return new_builder
        
        def invoke(self, template_name: str, variables: dict[str, Any]) -> list[NimbusMessage]:
            return self.render(template_name, variables)
        
        def format(self, template_name: str, variables: dict[str, Any]) -> str:
            messages = self.render(template_name, variables)
            return messages[0].content if messages else ""
        
        # Stub implementations for advanced features
        def add_examples(self, template_name: str, examples: list[dict], example_template: str | None = None) -> None:
            pass
        def set_example_selector(self, template_name: str, selector_type: str, max_examples: int = 5, **kwargs) -> None:
            pass
        def add_image_content(self, template_name: str, image_variable: str, image_format: str = "url") -> None:
            pass
        def add_multimodal_content(self, template_name: str, content_variables: dict[str, str]) -> None:
            pass
        def register_jinja_filter(self, filter_name: str, filter_func: Callable) -> None:
            pass
        def register_jinja_macro(self, macro_name: str, macro_template: str) -> None:
            pass
        def compose_templates(self, name: str, template_parts: list[str], separator: str = "\n\n") -> None:
            pass
        def set_message_roles(self, template_name: str, role_mapping: dict[str, str]) -> None:
            pass
        def add_message_placeholder(self, template_name: str, placeholder_name: str, role: str = "user") -> None:
            pass
        def set_output_schema(self, template_name: str, schema: dict | type) -> None:
            pass
        def get_output_instructions(self, template_name: str) -> str:
            return ""
        def get_template_metadata(self, template_name: str) -> dict:
            return {"variables": self.get_template_variables(template_name)}
        def validate_template(self, template_name: str) -> dict:
            return {"valid": True, "errors": [], "warnings": []}
    
    # Create prompt builder
    builder = SimplePromptBuilder()
    
    # Example 1: Basic template
    print("\n1. Basic Template:")
    builder.register_template(
        "greeting",
        "Hello {name}! Welcome to {place}."
    )
    messages = builder.render("greeting", {"name": "Alice", "place": "Nimbus"})
    print(f"   Template: 'Hello {{name}}! Welcome to {{place}}.'")
    print(f"   Rendered: {messages[0].content}")
    
    # Example 2: Default values
    print("\n2. Template with Defaults:")
    builder.set_default_values({"domain": "general", "format": "json"})
    builder.register_template(
        "extract",
        "Extract entities from: {text}\nDomain: {domain}\nFormat: {format}"
    )
    messages = builder.render("extract", {"text": "Alice works at Google"})
    print(f"   Defaults: domain='general', format='json'")
    print(f"   Rendered: {messages[0].content[:60]}...")
    
    # Example 3: Partial binding
    print("\n3. Partial Binding:")
    partial_builder = builder.partial(format="xml")
    messages = partial_builder.render("extract", {"text": "Bob lives in NYC"})
    print(f"   Partial: format='xml' (overrides default)")
    print(f"   Rendered: {messages[0].content[:60]}...")
    
    # Example 4: Template variables
    print("\n4. Template Introspection:")
    variables = builder.get_template_variables("extract")
    print(f"   Variables in 'extract' template: {variables}")
    
    # Example 5: Format to string
    print("\n5. Format to String (not messages):")
    prompt_str = builder.format("greeting", {"name": "Charlie", "place": "Cloud"})
    print(f"   String output: {prompt_str}")
    
    print("\n✨ PromptBuilderInterface Features:")
    print("  ✓ Template registration and versioning")
    print("  ✓ Variable substitution with validation")
    print("  ✓ Default values for optional parameters")
    print("  ✓ Partial binding (LangChain pattern)")
    print("  ✓ Template introspection and metadata")
    print("  ✓ Few-shot learning support")
    print("  ✓ Multimodal content (images, audio, video)")
    print("  ✓ Jinja2 filters and macros")
    print("  ✓ Output schema definition")
    
    print("\nSee examples/implementing_interfaces.py for more advanced usage!")


def main():
    """Run all examples."""
    print("\n" + "🌥️  " * 20)
    print("NIMBUS - Modular GenAI Library Examples")
    print("🌥️  " * 20)
    
    # Run all examples
    basic_completion_example()
    conversation_example()
    structured_output_example()
    message_metadata_example()
    capability_message_example()
    provider_formatting_example()
    prompt_template_example()
    
    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Implement a ModelInterface for your provider")
    print("  2. Use PromptBuilderInterface for template management")
    print("  3. Add CapabilityInterface for tool calling")
    print("  4. Use ModelRouterInterface for load balancing")
    print("\nSee the interfaces in src/nimbus/interfaces/ for more details.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
