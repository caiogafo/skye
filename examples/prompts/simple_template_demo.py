"""Simple Template Demo for Skye Prompts Support.

This script demonstrates basic template functionality without complex dependencies.
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from skye.prompts import MockPromptBuilder


def simple_ner_demo():
    """Demonstrate simple NER template."""
    print("=== Simple NER Demo ===")
    
    builder = MockPromptBuilder()
    
    # Simple template using Python string formatting
    ner_template = """Extract named entities from the following text.

Text: {text}

Please identify and list all:
- PERSON: Names of people
- ORGANIZATION: Names of companies, institutions
- LOCATION: Names of places, cities, countries

Format your response as:
PERSON: [list of people]
ORGANIZATION: [list of organizations] 
LOCATION: [list of locations]"""
    
    builder.register_template("simple_ner", ner_template)
    
    # Test the template
    messages = builder.render("simple_ner", {
        "text": "Apple Inc. was founded by Steve Jobs in Cupertino, California."
    })
    
    print(f"Template rendered successfully!")
    print(f"Message type: {type(messages[0]).__name__}")
    print(f"Content: {messages[0].content}")
    print()


def simple_classification_demo():
    """Demonstrate simple classification template."""
    print("=== Simple Classification Demo ===")
    
    builder = MockPromptBuilder()
    
    builder.register_template(
        "simple_classification",
        """Classify the sentiment of the following text as positive, negative, or neutral.

Text: {text}

Sentiment:"""
    )
    
    messages = builder.render("simple_classification", {
        "text": "I love this product! It's amazing."
    })
    
    print(f"Template rendered successfully!")
    print(f"Content: {messages[0].content}")
    print()


def simple_qa_demo():
    """Demonstrate simple Q&A template."""
    print("=== Simple Q&A Demo ===")
    
    builder = MockPromptBuilder()
    
    builder.register_template(
        "simple_qa",
        """Answer the following question based on the provided context.

Context: {context}

Question: {question}

Answer:"""
    )
    
    messages = builder.render("simple_qa", {
        "context": "The sky appears blue during the day due to Rayleigh scattering of sunlight.",
        "question": "Why is the sky blue?"
    })
    
    print(f"Template rendered successfully!")
    print(f"Content: {messages[0].content}")
    print()


def template_with_defaults_demo():
    """Demonstrate template with default values."""
    print("=== Template with Defaults Demo ===")
    
    builder = MockPromptBuilder()
    
    builder.register_template(
        "greeting",
        "Hello {name}! Welcome to {platform}."
    )
    
    # Set default values
    builder.set_default_values({"platform": "Skye"})
    
    messages = builder.render("greeting", {"name": "Alice"})
    
    print(f"Template with defaults rendered successfully!")
    print(f"Content: {messages[0].content}")
    print()


def multimodal_content_demo():
    """Demonstrate multimodal content handling."""
    print("=== Multimodal Content Demo ===")
    
    builder = MockPromptBuilder()
    
    builder.register_template(
        "image_analysis",
        """Analyze the following image and provide a detailed description.

Image URL: {image_url}
Additional context: {context}

Please describe what you see in the image:"""
    )
    
    messages = builder.render("image_analysis", {
        "image_url": "https://example.com/image.jpg",
        "context": "This is a product photo for our e-commerce site."
    })
    
    print(f"Multimodal template rendered successfully!")
    print(f"Content: {messages[0].content}")
    print()


def main():
    """Run all simple template demos."""
    print("Skye Prompts Support - Simple Template Demo")
    print("=" * 50)
    print()
    
    simple_ner_demo()
    simple_classification_demo()
    simple_qa_demo()
    template_with_defaults_demo()
    multimodal_content_demo()
    
    print("Simple template demo completed!")
    print()
    print("Key features demonstrated:")
    print("- Template registration with MockPromptBuilder")
    print("- Variable substitution using {variable} syntax")
    print("- Default values for templates")
    print("- Multimodal content handling")
    print("- Compatible with Skye completion API")


if __name__ == "__main__":
    main()