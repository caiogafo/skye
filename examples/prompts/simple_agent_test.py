"""Simple test of agent templates without complex Jinja2 features."""

import sys
import os
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from skye.prompts import BasePromptBuilder


def test_simple_templates():
    """Test templates that don't use complex Jinja2 features."""
    print("Testing Simple Agent Templates")
    print("=" * 40)
    
    builder = BasePromptBuilder()
    
    # Test memory agent with minimal variables
    print("=== Memory Agent (Simple) ===")
    try:
        messages = builder.render("memory_agent", {
            "input": "What did we discuss about machine learning yesterday?"
        })
        print(f"✓ Memory agent template rendered successfully")
        print(f"Content preview: {messages[0].content[:200]}...")
        print()
    except Exception as e:
        print(f"❌ Memory agent failed: {e}")
        print()
    
    # Test explanation template (likely simpler)
    print("=== Explanation Template ===")
    try:
        messages = builder.render("explanation", {
            "topic": "machine learning",
            "audience": "beginners",
            "style": "simple"
        })
        print(f"✓ Explanation template rendered successfully")
        print(f"Content preview: {messages[0].content[:200]}...")
        print()
    except Exception as e:
        print(f"❌ Explanation template failed: {e}")
        print()
    
    # Test question answering template
    print("=== Question Answering Template ===")
    try:
        messages = builder.render("question_answering", {
            "question": "What is machine learning?",
            "context": "Machine learning is a subset of artificial intelligence."
        })
        print(f"✓ Question answering template rendered successfully")
        print(f"Content preview: {messages[0].content[:200]}...")
        print()
    except Exception as e:
        print(f"❌ Question answering template failed: {e}")
        print()


if __name__ == "__main__":
    test_simple_templates()