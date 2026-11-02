"""Structured Output Example.

This example demonstrates how to use structured outputs with Skye.

Features shown:
- Basic structured output
- Nested schemas
- Field validation
- Type-safe responses
"""

import os
from pydantic import BaseModel, Field
from skye.base.completion import CompletionRequest
from skye.base.messages import UserMessage
from skye.models import ProviderRegistry


def basic_structured_output():
    """Basic structured output example."""
    print("=" * 60)
    print("Structured Output - Basic Example")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Define output schema
    class Person(BaseModel):
        name: str
        age: int
        occupation: str
    
    print("\nSchema:")
    print(f"  Fields: {list(Person.model_fields.keys())}")
    print(f"  Types: name (str), age (int), occupation (str)")
    
    request = CompletionRequest(
        messages=[
            UserMessage(content="Extract: John is 30 and works as a software engineer")
        ],
        model="gpt-4",
        response_schema=Person
    )
    
    print("\nRequest:")
    print(f"  Model: {request.model}")
    print(f"  Schema: {Person.__name__}")
    
    try:
        response = provider.complete(request)
        person = response.structured_output
        
        print("\nResponse:")
        print(f"  Name: {person.name}")
        print(f"  Age: {person.age}")
        print(f"  Occupation: {person.occupation}")
        print(f"  Type: {type(person).__name__}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def nested_schema():
    """Example with nested schemas."""
    print("\n" + "=" * 60)
    print("Structured Output - Nested Schema")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Define nested schema
    class Address(BaseModel):
        street: str
        city: str
        country: str
    
    class Person(BaseModel):
        name: str
        age: int
        address: Address
    
    print("\nSchema:")
    print(f"  Person:")
    print(f"    - name: str")
    print(f"    - age: int")
    print(f"    - address: Address")
    print(f"      - street: str")
    print(f"      - city: str")
    print(f"      - country: str")
    
    request = CompletionRequest(
        messages=[
            UserMessage(
                content="Extract: Alice lives at 123 Main St in New York, USA. She is 28 years old."
            )
        ],
        model="gpt-4",
        response_schema=Person
    )
    
    try:
        response = provider.complete(request)
        person = response.structured_output
        
        print("\nResponse:")
        print(f"  Name: {person.name}")
        print(f"  Age: {person.age}")
        print(f"  Address:")
        print(f"    Street: {person.address.street}")
        print(f"    City: {person.address.city}")
        print(f"    Country: {person.address.country}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def list_extraction():
    """Example extracting a list of items."""
    print("\n" + "=" * 60)
    print("Structured Output - List Extraction")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Define schema with list
    class Task(BaseModel):
        title: str
        priority: str
        completed: bool
    
    class TodoList(BaseModel):
        tasks: list[Task]
    
    print("\nSchema:")
    print(f"  TodoList:")
    print(f"    - tasks: list[Task]")
    print(f"      - title: str")
    print(f"      - priority: str")
    print(f"      - completed: bool")
    
    request = CompletionRequest(
        messages=[
            UserMessage(
                content="""Extract tasks from: 
                1. Buy groceries (high priority, not done)
                2. Write report (high priority, done)
                3. Call mom (low priority, not done)"""
            )
        ],
        model="gpt-4",
        response_schema=TodoList
    )
    
    try:
        response = provider.complete(request)
        todo_list = response.structured_output
        
        print("\nResponse:")
        print(f"  Tasks: {len(todo_list.tasks)}")
        for i, task in enumerate(todo_list.tasks, 1):
            status = "✓" if task.completed else "✗"
            print(f"    {i}. [{status}] {task.title} ({task.priority})")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def field_validation():
    """Example with field validation."""
    print("\n" + "=" * 60)
    print("Structured Output - Field Validation")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Define schema with validation
    class Product(BaseModel):
        name: str = Field(min_length=1, max_length=100)
        price: float = Field(gt=0, le=10000)
        rating: float = Field(ge=0, le=5)
        in_stock: bool
    
    print("\nSchema with validation:")
    print(f"  name: str (1-100 chars)")
    print(f"  price: float (0 < price <= 10000)")
    print(f"  rating: float (0 <= rating <= 5)")
    print(f"  in_stock: bool")
    
    request = CompletionRequest(
        messages=[
            UserMessage(
                content="Extract: Laptop priced at $999, rated 4.5 stars, currently in stock"
            )
        ],
        model="gpt-4",
        response_schema=Product
    )
    
    try:
        response = provider.complete(request)
        product = response.structured_output
        
        print("\nResponse:")
        print(f"  Name: {product.name}")
        print(f"  Price: ${product.price}")
        print(f"  Rating: {product.rating}/5")
        print(f"  In Stock: {product.in_stock}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def enum_fields():
    """Example with enum fields."""
    print("\n" + "=" * 60)
    print("Structured Output - Enum Fields")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    from enum import Enum
    
    # Define enum
    class Sentiment(str, Enum):
        POSITIVE = "positive"
        NEGATIVE = "negative"
        NEUTRAL = "neutral"
    
    class Review(BaseModel):
        text: str
        sentiment: Sentiment
        rating: int = Field(ge=1, le=5)
    
    print("\nSchema:")
    print(f"  text: str")
    print(f"  sentiment: Sentiment (positive, negative, neutral)")
    print(f"  rating: int (1-5)")
    
    request = CompletionRequest(
        messages=[
            UserMessage(
                content="Analyze: This product is amazing! I love it. Rating: 5 stars"
            )
        ],
        model="gpt-4",
        response_schema=Review
    )
    
    try:
        response = provider.complete(request)
        review = response.structured_output
        
        print("\nResponse:")
        print(f"  Text: {review.text}")
        print(f"  Sentiment: {review.sentiment.value}")
        print(f"  Rating: {review.rating}/5")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def optional_fields():
    """Example with optional fields."""
    print("\n" + "=" * 60)
    print("Structured Output - Optional Fields")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    from typing import Optional
    
    class Contact(BaseModel):
        name: str
        email: str
        phone: Optional[str] = None
        company: Optional[str] = None
    
    print("\nSchema:")
    print(f"  name: str (required)")
    print(f"  email: str (required)")
    print(f"  phone: str (optional)")
    print(f"  company: str (optional)")
    
    request = CompletionRequest(
        messages=[
            UserMessage(
                content="Extract: John Doe, john@example.com, works at Acme Corp"
            )
        ],
        model="gpt-4",
        response_schema=Contact
    )
    
    try:
        response = provider.complete(request)
        contact = response.structured_output
        
        print("\nResponse:")
        print(f"  Name: {contact.name}")
        print(f"  Email: {contact.email}")
        print(f"  Phone: {contact.phone or 'Not provided'}")
        print(f"  Company: {contact.company or 'Not provided'}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "📋 " * 20)
    print("SKYE - Structured Output Examples")
    print("📋 " * 20)
    
    try:
        basic_structured_output()
        nested_schema()
        list_extraction()
        field_validation()
        enum_fields()
        optional_fields()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        print("\nKey points:")
        print("  • Define schemas using Pydantic BaseModel")
        print("  • Skye handles schema validation automatically")
        print("  • Responses are type-safe Python objects")
        print("  • Supports nested schemas, lists, enums, and validation")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Installed skyeai[openai]: pip install skyeai[openai]")
        print("  2. Set OPENAI_API_KEY: export OPENAI_API_KEY='sk-...'")


if __name__ == "__main__":
    main()
