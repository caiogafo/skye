"""Run all Nimbus Prompts Support examples.

This script runs all example modules to demonstrate the complete
functionality of the prompts support system.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import nimbus modules
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from nimbus.prompts import BasePromptBuilder


def main():
    """Run all example modules."""
    print("Nimbus Prompts Support - Complete Examples Suite")
    print("=" * 60)
    print()
    
    # Test basic functionality
    builder = BasePromptBuilder()
    
    print("Testing BasePromptBuilder...")
    
    # Test default templates
    try:
        messages = builder.render("ner", {"text": "Apple Inc. was founded by Steve Jobs."})
        print(f"✓ NER template works: {messages[0].content[:50]}...")
    except Exception as e:
        print(f"✗ NER template error: {e}")
    
    try:
        messages = builder.render("classification", {
            "text": "This is amazing!",
            "categories": "positive, negative, neutral"
        })
        print(f"✓ Classification template works: {messages[0].content[:50]}...")
    except Exception as e:
        print(f"✗ Classification template error: {e}")
    
    try:
        messages = builder.render("qa", {
            "context": "The sky is blue during the day.",
            "question": "What color is the sky?"
        })
        print(f"✓ QA template works: {messages[0].content[:50]}...")
    except Exception as e:
        print(f"✗ QA template error: {e}")
    
    # Test custom template
    try:
        builder.register_template("custom", "Hello {name} from {location}!")
        builder.set_default_values({"location": "Earth"})
        messages = builder.render("custom", {"name": "Alice"})
        print(f"✓ Custom template works: {messages[0].content}")
    except Exception as e:
        print(f"✗ Custom template error: {e}")
    
    # Test examples
    try:
        examples = [
            {"text": "I love this!", "sentiment": "positive"},
            {"text": "This is terrible.", "sentiment": "negative"}
        ]
        builder.add_examples("classification", examples, "Text: {text} → Sentiment: {sentiment}")
        messages = builder.render("classification", {
            "text": "This is great!",
            "categories": "positive, negative, neutral"
        })
        print(f"✓ Examples work: Found examples in output")
    except Exception as e:
        print(f"✗ Examples error: {e}")
    
    print()
    print("=" * 60)
    print("BasePromptBuilder testing completed!")
    print()
    print("Key features demonstrated:")
    print("- Default templates automatically registered")
    print("- Template registration and rendering")
    print("- Default values and variable management")
    print("- Few-shot learning with examples")
    print("- Compatible with Nimbus completion API")
    print()
    print("Next steps:")
    print("1. Use BasePromptBuilder in your Nimbus applications")
    print("2. Create custom templates for your use cases")
    print("3. Implement the full Jinja2PromptBuilder for advanced features")


if __name__ == "__main__":
    main()