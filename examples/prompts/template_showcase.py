import sys
import os
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from nimbus.prompts import BasePromptBuilder
import nimbus


def complete_with_provider(messages, model="gpt-4", temperature=0.7, max_tokens=200, provider_name="openai"):
    """Helper function to complete messages using a provider."""
    api_key = os.getenv(f"{provider_name.upper()}_API_KEY")
    if not api_key:
        print(f"💡 Set {provider_name.upper()}_API_KEY to test completion")
        return None
    
    try:
        provider = nimbus.provider(provider_name, api_key=api_key)
        response = provider.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        print(f"✓ Completion successful!")
        print(f"  Content: {response.content[:200]}{'...' if len(response.content) > 200 else ''}")
        print(f"  Tokens used: {response.usage.total_tokens}")
        return response
    except ImportError:
        print(f"⚠️  {provider_name.title()} provider not available")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


"""Template showcase using current Nimbus templates.

This script demonstrates how to use the comprehensive Jinja2 templates
with real test data to create sophisticated prompts for various AI tasks.
"""


def showcase_ner_template():
    """Demonstrate NER template with real examples."""
    print("=== Named Entity Recognition Template ===")
    
    builder = BasePromptBuilder()
    
    # Use built-in NER template with enhanced features
    messages = builder.render("ner", {
        "text": "Sarah Johnson works at OpenAI in San Francisco and was born in 1985.",
        "domain": "professional",
        "labels": [
            {"name": "PERSON", "description": "Names of people"},
            {"name": "ORG", "description": "Organizations and companies"},
            {"name": "LOC", "description": "Locations and places"},
            {"name": "DATE", "description": "Dates and time expressions"}
        ],
        "examples": [
            {
                "text": "John Smith works at Google in Mountain View.",
                "entities": [
                    {"T": "PERSON", "E": "John Smith"},
                    {"T": "ORG", "E": "Google"},
                    {"T": "LOC", "E": "Mountain View"}
                ]
            }
        ],
        "output_format": "json"
    })
    
    print(f"Enhanced NER Prompt:\n{messages[0].content}")
    print()
    
    # Test completion
    complete_with_provider(messages, temperature=0.3, max_tokens=200)
    print()


def showcase_classification_template():
    """Demonstrate classification template with examples."""
    print("=== Text Classification Template ===")
    
    builder = BasePromptBuilder()
    
    # Use built-in classification template
    messages = builder.render("classification", {
        "text": "The new quantum computer breakthrough could revolutionize computing forever.",
        "categories": ["technology", "science", "business", "politics"],
        "domain": "technology news",
        "category_descriptions": [
            {"name": "technology", "description": "Technology products, innovations, and industry news"},
            {"name": "science", "description": "Scientific research, discoveries, and academic studies"},
            {"name": "business", "description": "Business news, market trends, and corporate activities"},
            {"name": "politics", "description": "Political news, government policies, and elections"}
        ],
        "examples": [
            {
                "text": "Apple releases new iPhone with advanced AI features",
                "category": "technology",
                "reasoning": "Focuses on a technology product release"
            },
            {
                "text": "Scientists discover new exoplanet in habitable zone",
                "category": "science",
                "reasoning": "Reports on scientific discovery and research"
            }
        ],
        "confidence_required": True,
        "reasoning_required": True,
        "output_format": "json"
    })
    
    print(f"Enhanced Classification Prompt:\n{messages[0].content}")
    print()
    
    # Test completion
    complete_with_provider(messages, temperature=0.3, max_tokens=150)
    print()


def showcase_qa_template():
    """Demonstrate question-answering template."""
    print("=== Question Answering Template ===")
    
    builder = BasePromptBuilder()
    
    # Use built-in question answering template
    messages = builder.render("question_answering", {
        "context": "Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to natural intelligence displayed by humans. AI research has been highly successful in developing effective techniques for solving a wide range of problems, from game playing to medical diagnosis.",
        "question": "What is artificial intelligence and what has AI research achieved?",
        "examples": [
            {
                "context": "Machine learning is a subset of AI that enables computers to learn from data.",
                "question": "What is machine learning?",
                "answer": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from data without being explicitly programmed."
            }
        ],
        "answer_length": "comprehensive",
        "output_format": "json",
        "system_prompt": "You are an expert AI researcher. Provide accurate and informative answers based on the given context."
    })
    
    print(f"Enhanced Q&A Prompt:\n{messages[0].content}")
    print()
    
    # Test completion
    complete_with_provider(messages, temperature=0.4, max_tokens=200)
    print()


def showcase_code_generation_template():
    """Demonstrate code generation template."""
    print("=== Code Generation Template ===")
    
    builder = BasePromptBuilder()
    
    # Use built-in code generation template
    messages = builder.render("code_generation", {
        "task": "create a function to calculate fibonacci numbers with memoization",
        "language": "Python",
        "requirements": [
            "Use recursion with memoization for efficiency",
            "Handle edge cases (n <= 0)",
            "Include comprehensive type hints",
            "Add detailed docstring with examples"
        ],
        "examples": [
            {
                "task": "calculate factorial",
                "code": "def factorial(n: int) -> int:\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)"
            }
        ],
        "include_tests": True,
        "include_comments": True,
        "input_format": "integer n (position in fibonacci sequence)",
        "output_format": "integer (nth fibonacci number)"
    })
    
    print(f"Enhanced Code Generation Prompt:\n{messages[0].content}")
    print()
    
    # Test completion with lower temperature for code generation
    complete_with_provider(messages, temperature=0.2, max_tokens=400)
    print()


def showcase_chat_template():
    """Demonstrate chat template with conversation history."""
    print("=== Chat Template ===")
    
    builder = BasePromptBuilder()
    
    # Use built-in chat template
    messages = builder.render("chat", {
        "persona": "an expert data scientist and educator",
        "domain": "machine learning and AI",
        "personality": ["patient", "thorough", "encouraging"],
        "guidelines": [
            "Use simple language when possible",
            "Provide concrete examples",
            "Ask follow-up questions to ensure understanding"
        ],
        "user_message": "I'm still confused about the difference between supervised and unsupervised learning.",
        "conversation_history": [
            {"role": "user", "content": "What is machine learning?"},
            {"role": "assistant", "content": "Machine learning is a subset of AI that enables computers to learn from data."},
            {"role": "user", "content": "Can you give me an example?"}
        ],
        "context": "The user is a beginner learning about ML concepts",
        "output_format": "conversational with examples"
    })
    
    print(f"Enhanced Chat Prompt:\n{messages[0].content}")
    print()
    
    # Test completion
    complete_with_provider(messages, temperature=0.7, max_tokens=300)
    print()


def showcase_agent_templates():
    """Demonstrate new agent-focused templates."""
    print("=== Agent Templates ===")
    
    builder = BasePromptBuilder()
    
    # Memory agent
    print("--- Memory Agent ---")
    messages = builder.render("memory_agent", {
        "user_input": "What did we discuss about neural networks?",
        "memory": [
            {"content": "User asked about backpropagation", "timestamp": "2024-01-15", "type": "episodic"}
        ]
    })
    print(f"Memory Agent: {messages[0].content[:100]}...")
    complete_with_provider(messages, max_tokens=150)
    
    # Tool agent
    print("--- Tool Agent ---")
    messages = builder.render("tool_agent", {
        "user_input": "What's the weather like?",
        "available_tools": [{"name": "get_weather", "description": "Get current weather"}]
    })
    print(f"Tool Agent: {messages[0].content[:100]}...")
    complete_with_provider(messages, temperature=0.3, max_tokens=100)
    
    # Reasoning agent
    print("--- Reasoning Agent ---")
    messages = builder.render("reasoning_agent", {
        "problem": "Why did sales decrease this quarter?",
        "reasoning_type": "analytical"
    })
    print(f"Reasoning Agent: {messages[0].content[:100]}...")
    complete_with_provider(messages, temperature=0.6, max_tokens=200)
    
    # Code agent
    print("--- Code Agent ---")
    messages = builder.render("code_agent", {
        "task": "Create a sorting algorithm",
        "language": "Python"
    })
    print(f"Code Agent: {messages[0].content[:100]}...")
    complete_with_provider(messages, temperature=0.2, max_tokens=250)


def main():
    """Run all template showcase examples."""
    print("Nimbus Prompts Support - Template Showcase")
    print("=" * 50)
    print()
    
    showcase_ner_template()
    showcase_classification_template()
    showcase_qa_template()
    showcase_code_generation_template()
    showcase_chat_template()
    showcase_agent_templates()
    
    print("Template showcase completed!")
    print()
    print("Available templates demonstrate:")
    print("- Enhanced NER with domain-specific labels and examples")
    print("- Classification with category descriptions and reasoning")
    print("- Question answering with context and structured output")
    print("- Code generation with requirements and testing")
    print("- Chat with personality and conversation history")
    print("- Agent templates for memory, tools, reasoning, and code")
    print("- Specialized NLP tasks (relation extraction, SQL generation)")
    print("- Multimodal content support")
    print("- Form-based interactions and procedure execution")


if __name__ == "__main__":
    main()