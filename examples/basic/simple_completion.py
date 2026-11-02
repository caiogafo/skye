"""Basic Skye Usage Example.

This example demonstrates the core concepts of Skye:
- Creating completion requests with messages
- Using different message types
- Working with token usage
- Handling structured outputs

Note: Set environment variables for API keys:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- AWS credentials for Bedrock
"""

import os
from skye.models.registry import provider as create_provider
from pydantic import BaseModel

from skye.base.messages import UserMessage, AssistantMessage, SystemMessage


def basic_completion_example():
    """Example of creating a basic completion request."""
    print("=" * 60)
    print("Basic Completion Request Example")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, skipping example")
        return
    
    try:
        provider = create_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    messages = [
        SystemMessage(content="You are a helpful AI assistant."),
        UserMessage(content="What is the capital of France?")
    ]
    
    print(f"\nModel: gpt-4")
    print(f"Temperature: 0.7")
    print(f"Messages: {len(messages)}")
    
    for i, msg in enumerate(messages):
        print(f"  {i+1}. [{msg.role}] {msg.content[:50]}...")
    
    try:
        response = provider.complete(
            messages=messages,
            model="gpt-4",
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"\nResponse:")
        print(f"  Provider: {response.provider}")
        print(f"  Content: {response.content}")
        print(f"  Tokens used: {response.usage.total_tokens}")
        print(f"  Finish reason: {response.finish_reason}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def conversation_example():
    """Example of a multi-turn conversation."""
    print("\n" + "=" * 60)
    print("Multi-Turn Conversation Example")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, skipping example")
        return
    
    try:
        provider = create_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Build a conversation history
    messages = [
        SystemMessage(content="You are a helpful coding assistant."),
        UserMessage(content="How do I create a list in Python?"),
        AssistantMessage(content="You can create a list using square brackets: my_list = [1, 2, 3]"),
        UserMessage(content="How do I add an item to it?")
    ]
    
    print(f"\nConversation with {len(messages)} messages:")
    for msg in messages:
        role_emoji = {"system": "⚙️", "user": "👤", "assistant": "🤖"}.get(msg.role, "❓")
        print(f"  {role_emoji} [{msg.role}] {msg.content[:60]}...")
    
    try:
        response = provider.complete(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=100
        )
        print(f"\nAssistant response:")
        print(f"  {response.content}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def structured_output_example():
    """Example of requesting structured output."""
    print("\n" + "=" * 60)
    print("Structured Output Example")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, skipping example")
        return
    
    try:
        provider = create_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Define output schema
    class Person(BaseModel):
        name: str
        age: int
        occupation: str
    
    print(f"\nRequesting structured output with schema: {Person.__name__}")
    print(f"  Fields: {list(Person.model_fields.keys())}")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="Extract person info: John is a 30-year-old software engineer.")
            ],
            model="gpt-4",
            response_schema=Person
        )
        person = response.structured_output
        
        print(f"\nStructured output received:")
        print(f"  Name: {person.name}")
        print(f"  Age: {person.age}")
        print(f"  Occupation: {person.occupation}")
        print(f"  Tokens used: {response.usage.total_tokens}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def message_metadata_example():
    """Example of using message metadata."""
    print("\n" + "=" * 60)
    print("Message Metadata Example")
    print("=" * 60)
    
    from datetime import datetime
    
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
    
    from skye.base.messages import CapabilityMessage
    
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


def anthropic_example():
    """Example using Anthropic provider."""
    print("\n" + "=" * 60)
    print("Anthropic Provider Example")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set, skipping example")
        return
    
    try:
        provider = create_provider("anthropic", api_key=api_key)
    except ImportError:
        print("⚠️  Anthropic provider not available")
        return
    
    print(f"\nUsing Anthropic Claude model")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="Explain quantum computing in simple terms.")
            ],
            model="claude-3-sonnet-20240229",
            max_tokens=200
        )
        print(f"\nResponse:")
        print(f"  {response.content[:200]}...")
        print(f"  Tokens used: {response.usage.total_tokens}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def bedrock_example():
    """Example using AWS Bedrock provider."""
    print("\n" + "=" * 60)
    print("AWS Bedrock Provider Example")
    print("=" * 60)
    
    has_aws = os.getenv("AWS_PROFILE") or os.getenv("AWS_ACCESS_KEY_ID")
    if not has_aws:
        print("⚠️  AWS credentials not configured, skipping example")
        return
    
    try:
        provider = create_provider("bedrock", region="us-east-1")
    except ImportError:
        print("⚠️  Bedrock provider not available")
        return
    
    print(f"\nUsing AWS Bedrock Claude model")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="What is machine learning?")
            ],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            max_tokens=200
        )
        print(f"\nResponse:")
        print(f"  {response.content[:200]}...")
        print(f"  Tokens used: {response.usage.total_tokens}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "🌥️  " * 20)
    print("SKYE - Basic Examples")
    print("🌥️  " * 20)
    
    basic_completion_example()
    conversation_example()
    structured_output_example()
    message_metadata_example()
    capability_message_example()
    anthropic_example()
    bedrock_example()
    
    print("\n" + "=" * 60)
    print("✅ Examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Explore capabilities: examples/capabilities/")
    print("  2. Learn about providers: examples/providers/")
    print("  3. Set up routing: examples/routing/")
    print("  4. Advanced patterns: examples/advanced/")
    print("\nFor more information, see the README files in each directory.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
