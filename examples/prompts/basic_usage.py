"""Basic usage examples for Skye BasePromptBuilder.

This script demonstrates the fundamental features of the BasePromptBuilder.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from skye.prompts import BasePromptBuilder
from skye.models.registry import provider as create_provider


def complete_with_provider(messages, model="gpt-4", temperature=0.7, max_tokens=200, provider_name="openai"):
    """Helper function to complete messages using a provider.
    
    Args:
        messages: List of SkyeMessage objects from template rendering
        model: Model name to use (default: gpt-4)
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens to generate (default: 200)
        provider_name: Provider to use (default: openai)
    
    Returns:
        CompletionResponse or None if API key not available
    """
    api_key = os.getenv(f"{provider_name.upper()}_API_KEY")
    if not api_key:
        print(f"💡 Set {provider_name.upper()}_API_KEY to test completion")
        return None
    
    try:
        provider = create_provider(provider_name, api_key=api_key)
        response = provider.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        print(f"✓ Completion successful!")
        print(f"  Provider: {response.provider}")
        print(f"  Model: {response.model}")
        print(f"  Content: {response.content[:150]}{'...' if len(response.content) > 150 else ''}")
        print(f"  Tokens used: {response.usage.total_tokens}")
        print(f"  Finish reason: {response.finish_reason}")
        return response
    except ImportError:
        print(f"⚠️  {provider_name.title()} provider not available")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def basic_template_registration():
    """Demonstrate basic template registration and rendering."""
    print("=== Basic Template Registration ===")
    
    builder = BasePromptBuilder()
    
    # Register a simple template
    builder.register_template("greeting", "Hello {name}! Welcome to {platform}.")
    
    # Render with variables
    messages = builder.render("greeting", {
        "name": "Alice",
        "platform": "Skye"
    })
    
    print(f"Rendered message: {messages[0].content}")
    print(f"Message type: {type(messages[0]).__name__}")
    print(f"✓ Compatible with Skye completion API")
    print()
    
    # Direct completion call using provider interface
    complete_with_provider(messages, temperature=0.7, max_tokens=100)
    print()


def default_templates_demo():
    """Demonstrate built-in default templates."""
    print("=== Default Templates Demo ===")
    
    builder = BasePromptBuilder()
    
    # Test NER template
    print("--- NER Template ---")
    messages = builder.render("ner", {"text": "Apple Inc. was founded by Steve Jobs."})
    print(f"NER template: {messages[0].content[:100]}...")
    complete_with_provider(messages, max_tokens=150)
    
    # Test classification template
    print("--- Classification Template ---")
    messages = builder.render("classification", {
        "text": "This is amazing!",
        "categories": ["positive", "negative", "neutral"]
    })
    print(f"Classification template: {messages[0].content[:100]}...")
    complete_with_provider(messages, max_tokens=50)
    
    # Test question answering template
    print("--- Question Answering Template ---")
    messages = builder.render("question_answering", {
        "context": "The sky is blue during the day.",
        "question": "What color is the sky?"
    })
    print(f"Q&A template: {messages[0].content[:100]}...")
    complete_with_provider(messages, max_tokens=50)
    
    # Test agent templates
    print("--- Memory Agent Template ---")
    messages = builder.render("memory_agent", {
        "user_input": "What did we discuss about AI?",
        "memory": [{"content": "We talked about machine learning", "timestamp": "2024-01-15"}]
    })
    print(f"Memory agent template: {messages[0].content[:100]}...")
    complete_with_provider(messages, max_tokens=100)
    
    # Test tool agent template
    print("--- Tool Agent Template ---")
    messages = builder.render("tool_agent", {
        "user_input": "What's the weather like?",
        "available_tools": [{"name": "get_weather", "description": "Get current weather"}]
    })
    print(f"Tool agent template: {messages[0].content[:100]}...")
    complete_with_provider(messages, max_tokens=100)
    
    print("✓ All templates return SkyeMessage objects ready for completion")
    print()


def default_values_example():
    """Demonstrate default values and allowed missing variables."""
    print("=== Default Values Example ===")
    
    builder = BasePromptBuilder()
    
    # Register template with optional variables
    builder.register_template("task_prompt", "Task: {task}\nDomain: {domain}\nOutput: {output_format}")
    
    # Set default values
    builder.set_default_values({
        "domain": "general",
        "output_format": "text"
    })
    
    # Render with minimal variables
    messages = builder.render("task_prompt", {"task": "Extract entities"})
    print(f"With defaults: {messages[0].content}")
    
    # Override defaults
    messages = builder.render("task_prompt", {
        "task": "Extract entities",
        "domain": "medical",
        "output_format": "json"
    })
    print(f"With overrides: {messages[0].content}")
    print()


def few_shot_examples():
    """Demonstrate few-shot learning."""
    print("=== Few-Shot Learning ===")
    
    builder = BasePromptBuilder()
    
    # Add examples to classification template
    examples = [
        {"text": "I love this product!", "sentiment": "positive"},
        {"text": "This is terrible.", "sentiment": "negative"},
        {"text": "It's okay, I guess.", "sentiment": "neutral"}
    ]
    
    builder.add_examples("classification", examples, "Text: {text} → Sentiment: {sentiment}")
    
    # Render with examples
    messages = builder.render("classification", {
        "text": "This is fantastic!",
        "categories": "positive, negative, neutral"
    })
    
    print(f"With examples: {messages[0].content}")
    print()


def template_composition():
    """Demonstrate template composition."""
    print("=== Template Composition ===")
    
    builder = BasePromptBuilder()
    
    # Register component templates
    builder.register_template("system_msg", "You are a helpful AI assistant.")
    builder.register_template("task_desc", "Your task is to {task}.")
    builder.register_template("output_format", "Please format your response as {format}.")
    
    # Compose them
    builder.compose_templates("full_prompt", ["system_msg", "task_desc", "output_format"])
    
    # Render composed template
    messages = builder.render("full_prompt", {
        "task": "extract named entities",
        "format": "JSON"
    })
    
    print(f"Composed template: {messages[0].content}")
    print()


def partial_binding_example():
    """Demonstrate partial variable binding."""
    print("=== Partial Variable Binding ===")
    
    builder = BasePromptBuilder()
    
    builder.register_template("analysis", "Analyze {text} for {task} using {method} approach.")
    
    # Create partial with some variables bound
    partial_builder = builder.partial(method="systematic", task="sentiment analysis")
    
    # Now only need to provide text
    messages = partial_builder.render("analysis", {"text": "customer feedback"})
    print(f"Partial result: {messages[0].content}")
    print()


def template_metadata():
    """Demonstrate template introspection."""
    print("=== Template Metadata ===")
    
    builder = BasePromptBuilder()
    
    builder.register_template("complex", "Process {input} with {method} and output {format}")
    builder.set_default_values({"format": "json"})
    builder.set_allowed_missing_variables(["method"])
    
    # Get metadata
    metadata = builder.get_template_metadata("complex")
    print(f"Variables: {metadata['variables']}")
    print(f"Optional variables: {metadata['optional_variables']}")
    
    # Validate template
    validation = builder.validate_template("complex")
    print(f"Valid: {validation['valid']}")
    print(f"Warnings: {validation['warnings']}")
    print()


def main():
    """Run all basic usage examples."""
    print("Skye BasePromptBuilder - Basic Usage Examples")
    print("=" * 55)
    
    basic_template_registration()
    default_templates_demo()
    default_values_example()
    few_shot_examples()
    template_composition()
    partial_binding_example()
    template_metadata()
    
    print("All basic examples completed successfully!")
    print()
    print("Key features:")
    print("- Default templates automatically available (NER, classification, agents, etc.)")
    print("- Returns SkyeMessage objects for completion API")
    print("- Template versioning and composition")
    print("- Few-shot learning support")
    print("- Variable defaults and validation")
    print("- Agent-focused templates (memory, tool, procedure, form, reasoning)")
    print("- Multimodal content support")
    print("- Code generation and specialized NLP tasks")


if __name__ == "__main__":
    main()