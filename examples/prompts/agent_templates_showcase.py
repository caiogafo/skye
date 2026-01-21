"""Agent Templates Showcase for Nimbus Prompts Support.

This script demonstrates the comprehensive agent-focused templates
inspired by Cheshire Cat and Promptify patterns.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from nimbus.prompts import BasePromptBuilder
import nimbus


def complete_with_provider(messages, model="gpt-4", temperature=0.7, max_tokens=200, provider_name="openai"):
    """Helper function to complete messages using a provider.
    
    Args:
        messages: List of NimbusMessage objects from template rendering
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
        provider = nimbus.provider(provider_name, api_key=api_key)
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


def showcase_memory_agent():
    """Demonstrate memory agent template with episodic and declarative memory."""
    print("=== Memory Agent Template ===")
    
    builder = BasePromptBuilder()
    
    # Render memory agent template
    messages = builder.render("memory_agent", {
        "input": "What did we discuss about machine learning yesterday?",
        "episodic_memory": [
            {
                "content": "User asked about neural networks and deep learning fundamentals",
                "timestamp": "2024-01-15 14:30:00"
            }
        ],
        "declarative_memory": [
            {
                "content": "Machine learning is a subset of AI that learns from data",
                "source": "AI textbook"
            }
        ],
        "personality": "helpful and patient teacher"
    })
    
    print(f"Memory Agent Prompt:\n{messages[0].content}")
    print()
    
    # Test completion
    complete_with_provider(messages, temperature=0.7, max_tokens=250)
    print()


def showcase_tool_agent():
    """Demonstrate tool agent template for capability selection."""
    print("=== Tool Agent Template ===")
    
    builder = BasePromptBuilder()
    
    # Render tool agent template
    messages = builder.render("tool_agent", {
        "input": "What's the weather like in San Francisco and can you send an email about it?",
        "tools": [
            {
                "name": "get_weather",
                "description": "Get current weather information for a specified location"
            },
            {
                "name": "send_email", 
                "description": "Send an email to specified recipients"
            },
            {
                "name": "search_web",
                "description": "Search the web for information"
            }
        ]
    })
    
    print(f"Tool Agent Prompt:\n{messages[0].content}")
    print()
    
    # Test completion with lower temperature for tool selection
    complete_with_provider(messages, temperature=0.3, max_tokens=150)
    print()


def showcase_procedure_agent():
    """Demonstrate procedure agent template for step-by-step execution."""
    print("=== Procedure Agent Template ===")
    
    builder = BasePromptBuilder()
    
    # Render procedure agent template
    messages = builder.render("procedure_agent", {
        "input": "Set up a new Python project with testing framework",
        "procedures": [
            {
                "name": "create_directory",
                "description": "Create a new directory structure"
            },
            {
                "name": "setup_virtual_env",
                "description": "Set up Python virtual environment"
            },
            {
                "name": "install_dependencies",
                "description": "Install required packages"
            }
        ]
    })
    
    print(f"Procedure Agent Prompt:\n{messages[0].content}")
    print()
    
    # Test completion
    complete_with_provider(messages, temperature=0.4, max_tokens=300)
    print()


def showcase_form_agent():
    """Demonstrate form agent template for interactive data collection."""
    print("=== Form Agent Template ===")
    
    builder = BasePromptBuilder()
    
    # Render form agent template
    messages = builder.render("form_agent", {
        "input": "I want to register for an account",
        "form_description": "User Registration",
        "form_fields": [
            {
                "name": "full_name",
                "required": True,
                "description": "Your full name"
            },
            {
                "name": "email",
                "required": True,
                "description": "Your email address",
                "validation": "valid email format"
            },
            {
                "name": "age",
                "required": False,
                "description": "Your age (optional)"
            }
        ],
        "collected_data": {
            "full_name": "John Doe"
        },
        "validation_errors": ["Email is required"]
    })
    
    print(f"Form Agent Prompt:\n{messages[0].content}")
    print()
    
    # Test completion
    complete_with_provider(messages, temperature=0.5, max_tokens=200)
    print()


def showcase_reasoning_agent():
    """Demonstrate reasoning agent template for step-by-step analysis."""
    print("=== Reasoning Agent Template ===")
    
    builder = BasePromptBuilder()
    
    # Render reasoning agent template
    messages = builder.render("reasoning_agent", {
        "input": "A company's revenue decreased by 15% this quarter. What could be the possible causes and solutions?",
        "reasoning_type": "analytical",
        "context": "Q3 financial review meeting",
        "constraints": [
            "Focus on actionable insights",
            "Consider both internal and external factors",
            "Provide evidence-based recommendations"
        ],
        "output_format": "structured"
    })
    
    print(f"Reasoning Agent Prompt:\n{messages[0].content}")
    print()
    
    # Test completion
    complete_with_provider(messages, temperature=0.6, max_tokens=400)
    print()


def showcase_multimodal_agent():
    """Demonstrate multimodal agent template for mixed content analysis."""
    print("=== Multimodal Agent Template ===")
    
    builder = BasePromptBuilder()
    
    # Render multimodal agent template
    messages = builder.render("multimodal_agent", {
        "input": "Analyze this product presentation and provide feedback",
        "task_type": "multimodal_reasoning",
        "content_types": ["text", "image", "audio"],
        "images": [
            {
                "description": "Product photo showing the smartphone",
                "url": "https://example.com/product-image.jpg"
            }
        ],
        "documents": [
            {
                "title": "Product Description",
                "content": "Our new AI-powered smartphone features advanced camera capabilities and 5G connectivity."
            }
        ],
        "audio": [
            {
                "description": "Audio demo of voice features",
                "transcript": "Voice assistant activated. How can I help you today?"
            }
        ],
        "context": "Product launch preparation",
        "output_format": "detailed"
    })
    
    print(f"Multimodal Agent Prompt:\n{messages[0].content}")
    print()
    
    # Test completion
    complete_with_provider(messages, temperature=0.7, max_tokens=350)
    print()


def showcase_code_agent():
    """Demonstrate code agent template for programming assistance."""
    print("=== Code Agent Template ===")
    
    builder = BasePromptBuilder()
    
    # Render code agent template
    messages = builder.render("code_agent", {
        "input": "Create a Python function to validate email addresses",
        "task_type": "code_generation",
        "programming_language": "python",
        "requirements": [
            "Use regular expressions for validation",
            "Handle edge cases (empty strings, None)",
            "Return boolean result",
            "Include comprehensive docstring"
        ],
        "constraints": [
            "PEP 8 compliant",
            "Include type hints",
            "Add error handling"
        ],
        "output_format": "detailed",
        "code_style": [
            "Follow PEP 8 guidelines",
            "Use descriptive variable names",
            "Include comprehensive docstrings"
        ]
    })
    
    print(f"Code Agent Prompt:\n{messages[0].content}")
    print()
    
    # Test completion with lower temperature for code generation
    complete_with_provider(messages, temperature=0.2, max_tokens=500)
    print()


def showcase_main_agent():
    """Demonstrate main agent template with all capabilities."""
    print("=== Main Agent Template (All Capabilities) ===")
    
    builder = BasePromptBuilder()
    
    # Render main agent template
    messages = builder.render("main_agent", {
        "input": "I need help planning a data science project. Can you help me set up the environment and create a basic analysis workflow?",
        "capabilities": [
            {
                "name": "memory_recall",
                "description": "Access to conversation history and learned information"
            },
            {
                "name": "tool_usage", 
                "description": "Ability to use external tools and APIs"
            },
            {
                "name": "procedure_execution",
                "description": "Execute step-by-step procedures"
            },
            {
                "name": "code_generation",
                "description": "Generate and analyze code"
            }
        ],
        "declarative_memory": [
            {
                "content": "User is experienced with Python but new to data science",
                "source": "previous conversation"
            }
        ],
        "personality": "expert data scientist and mentor",
        "response_guidelines": [
            "Provide structured and educational responses",
            "Include practical examples",
            "Break down complex concepts"
        ],
        "thinking_required": True
    })
    
    print(f"Main Agent Prompt:\n{messages[0].content}")
    print()
    
    # Test completion
    complete_with_provider(messages, temperature=0.7, max_tokens=400)
    print()


def showcase_specialized_nlp_templates():
    """Demonstrate specialized NLP templates."""
    print("=== Specialized NLP Templates ===")
    
    builder = BasePromptBuilder()
    
    # Relation extraction
    print("--- Relation Extraction ---")
    messages = builder.render("relation_extraction", {
        "text": "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
        "relation_types": [
            {"name": "FOUNDED_BY", "description": "Organization founded by person"},
            {"name": "LOCATED_IN", "description": "Entity located in place"}
        ],
        "output_format": "json"
    })
    print(f"Relation Extraction Prompt:\n{messages[0].content[:150]}...\n")
    complete_with_provider(messages, temperature=0.3, max_tokens=150)
    
    # SQL generation
    print("--- SQL Generation ---")
    messages = builder.render("sql_generation", {
        "question": "Find all customers who made purchases over $1000 last month",
        "database_schema": [
            {
                "name": "customers",
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name", "type": "VARCHAR(100)"}
                ]
            },
            {
                "name": "orders",
                "columns": [
                    {"name": "customer_id", "type": "INTEGER"},
                    {"name": "amount", "type": "DECIMAL"},
                    {"name": "order_date", "type": "DATE"}
                ]
            }
        ],
        "database_type": "PostgreSQL"
    })
    print(f"SQL Generation Prompt:\n{messages[0].content[:150]}...\n")
    complete_with_provider(messages, temperature=0.2, max_tokens=200)
    
    # Tabular extraction
    print("--- Tabular Extraction ---")
    messages = builder.render("tabular_extraction", {
        "text": "Product A costs $29.99, Product B costs $45.50, Product C costs $12.75",
        "table_schema": [
            {"name": "product_name", "description": "Name of the product", "type": "string"},
            {"name": "price", "description": "Price in USD", "type": "decimal"}
        ],
        "output_format": "csv"
    })
    print(f"Tabular Extraction Prompt:\n{messages[0].content[:150]}...\n")
    complete_with_provider(messages, temperature=0.1, max_tokens=100)


def main():
    """Run all agent template showcase examples."""
    print("Nimbus Prompts Support - Agent Templates Showcase")
    print("=" * 55)
    print()
    
    showcase_memory_agent()
    showcase_tool_agent()
    showcase_procedure_agent()
    showcase_form_agent()
    showcase_reasoning_agent()
    showcase_multimodal_agent()
    showcase_code_agent()
    showcase_main_agent()
    showcase_specialized_nlp_templates()
    
    print("Agent templates showcase completed!")
    print()
    print("Available agent templates:")
    print("- memory_agent: AI with episodic/declarative memory context")
    print("- tool_agent: Tool selection with JSON response format")
    print("- procedure_agent: Procedure execution system")
    print("- form_agent: Interactive form completion")
    print("- reasoning_agent: Step-by-step reasoning with multiple strategies")
    print("- multimodal_agent: Text, image, audio content analysis")
    print("- code_agent: Programming assistance and code generation")
    print("- main_agent: Comprehensive agent with all capabilities")
    print("- relation_extraction: Extract relationships between entities")
    print("- sql_generation: Natural language to SQL conversion")
    print("- tabular_extraction: Extract structured data from text")
    print("- explanation: Generate explanations for complex topics")


if __name__ == "__main__":
    main()