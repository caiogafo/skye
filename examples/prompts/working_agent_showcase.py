"""Working Agent Templates Showcase for Nimbus Prompts Support.

This script demonstrates agent templates that work with the current
BasePromptBuilder implementation, avoiding complex Jinja2 syntax.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from nimbus.prompts import BasePromptBuilder
from nimbus.models.registry import provider as create_provider


def complete_with_provider(messages, model="gpt-4", temperature=0.7, max_tokens=200, provider_name="openai"):
    """Helper function to complete messages using a provider."""
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


def showcase_working_templates():
    """Demonstrate templates that work with current implementation."""
    print("=== Working Templates ===")
    
    builder = BasePromptBuilder()
    
    # Test simple templates that work
    templates_to_test = [
        ("ner", {
            "text": "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
            "labels": "PERSON, ORGANIZATION, LOCATION"
        }),
        ("classification", {
            "text": "This product is amazing! I love it.",
            "categories": "positive, negative, neutral"
        }),
        ("question_answering", {
            "question": "What is machine learning?",
            "context": "Machine learning is a subset of artificial intelligence that learns from data."
        }),
        ("summarization", {
            "text": "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
            "max_length": "50 words"
        }),
        ("explanation", {
            "topic": "neural networks",
            "audience": "beginners",
            "style": "simple"
        })
    ]
    
    for template_name, variables in templates_to_test:
        print(f"--- {template_name.title()} Template ---")
        try:
            messages = builder.render(template_name, variables)
            print(f"✓ Template rendered successfully")
            print(f"Content preview: {messages[0].content[:200]}...")
            print()
            
            # Test completion if API key available
            complete_with_provider(messages, temperature=0.7, max_tokens=150)
            print()
            
        except Exception as e:
            print(f"❌ Template failed: {e}")
            print()


def showcase_custom_agent_templates():
    """Create custom agent templates that work with simple syntax."""
    print("=== Custom Agent Templates ===")
    
    builder = BasePromptBuilder()
    
    # Simple memory agent template
    print("--- Simple Memory Agent ---")
    memory_template = """You are an AI assistant with memory capabilities.

Previous conversation context:
{memory_context}

User's current message: {user_input}

Please respond helpfully, taking into account the previous context."""
    
    builder.register_template("simple_memory_agent", memory_template)
    
    try:
        messages = builder.render("simple_memory_agent", {
            "memory_context": "User asked about machine learning basics yesterday. They are a beginner.",
            "user_input": "Can you explain neural networks to me?"
        })
        print(f"✓ Simple memory agent template works")
        print(f"Content: {messages[0].content}")
        print()
        complete_with_provider(messages, temperature=0.7, max_tokens=200)
        print()
    except Exception as e:
        print(f"❌ Simple memory agent failed: {e}")
        print()
    
    # Simple tool agent template
    print("--- Simple Tool Agent ---")
    tool_template = """You are an AI assistant that can use tools to help users.

Available tools:
{available_tools}

User request: {user_input}

Please respond with which tool you would use and why, or indicate if no tool is needed.
Format your response as: TOOL: [tool_name] - [reason]"""
    
    builder.register_template("simple_tool_agent", tool_template)
    
    try:
        messages = builder.render("simple_tool_agent", {
            "available_tools": "get_weather, send_email, search_web",
            "user_input": "What's the weather like in San Francisco?"
        })
        print(f"✓ Simple tool agent template works")
        print(f"Content: {messages[0].content}")
        print()
        complete_with_provider(messages, temperature=0.3, max_tokens=100)
        print()
    except Exception as e:
        print(f"❌ Simple tool agent failed: {e}")
        print()
    
    # Simple code agent template
    print("--- Simple Code Agent ---")
    code_template = """You are a programming assistant.

Task: {task}
Programming language: {language}
Requirements: {requirements}

Please provide a code solution with explanation."""
    
    builder.register_template("simple_code_agent", code_template)
    
    try:
        messages = builder.render("simple_code_agent", {
            "task": "Create a function to validate email addresses",
            "language": "Python",
            "requirements": "Use regex, handle edge cases, return boolean"
        })
        print(f"✓ Simple code agent template works")
        print(f"Content: {messages[0].content}")
        print()
        complete_with_provider(messages, temperature=0.2, max_tokens=300)
        print()
    except Exception as e:
        print(f"❌ Simple code agent failed: {e}")
        print()


def showcase_few_shot_learning():
    """Demonstrate few-shot learning capabilities."""
    print("=== Few-Shot Learning ===")
    
    builder = BasePromptBuilder()
    
    # Add examples for sentiment classification
    examples = [
        {"text": "I love this product!", "sentiment": "positive"},
        {"text": "This is terrible quality.", "sentiment": "negative"},
        {"text": "It's okay, nothing special.", "sentiment": "neutral"}
    ]
    
    builder.add_examples("classification", examples, "Text: '{text}' → Sentiment: {sentiment}")
    
    try:
        messages = builder.render("classification", {
            "text": "This is absolutely fantastic!",
            "categories": "positive, negative, neutral"
        })
        print(f"✓ Few-shot classification works")
        print(f"Content preview: {messages[0].content[:300]}...")
        print()
        complete_with_provider(messages, temperature=0.3, max_tokens=50)
        print()
    except Exception as e:
        print(f"❌ Few-shot learning failed: {e}")
        print()


def main():
    """Run all working agent template examples."""
    print("Nimbus Prompts Support - Working Agent Templates")
    print("=" * 55)
    print()
    
    showcase_working_templates()
    showcase_custom_agent_templates()
    showcase_few_shot_learning()
    
    print("Working templates showcase completed!")
    print()
    print("Summary:")
    print("✓ Basic templates (NER, classification, QA, summarization, explanation)")
    print("✓ Custom agent templates with simple syntax")
    print("✓ Few-shot learning with examples")
    print("✓ Compatible with Nimbus completion API")
    print()
    print("Note: Complex Jinja2 templates need proper Jinja2 dependency")
    print("Consider adding 'jinja2>=3.0' to prompts extra for full functionality")


if __name__ == "__main__":
    main()