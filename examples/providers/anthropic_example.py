"""Anthropic Provider Example (Boto3-style Nimbus API).

This version demonstrates:
- Basic completion with Claude models
- Streaming responses
- System messages (Anthropic-specific)
- Multi-turn conversations
- Simple client creation: nimbus.provider("anthropic")
"""

import os
import nimbus
from nimbus.messages import UserMessage, SystemMessage


def basic_completion():
    """Basic completion with Anthropic."""
    print("=" * 60)
    print("Anthropic - Basic Completion")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY environment variable not set")
        print("   Set it with: export ANTHROPIC_API_KEY='sk-ant-...'")
        return
    
    try:
        client = nimbus.provider("anthropic", api_key=api_key)
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use Anthropic, install with: pip install nimbus[anthropic]")
        return
    
    messages = [
        SystemMessage("You are a helpful assistant specialized in science."),
        UserMessage("Explain photosynthesis in simple terms"),
    ]
    
    response = client.complete(
        messages=messages,
        model="claude-3-sonnet-20240229",
        temperature=0.7,
        max_tokens=200,
    )
    
    print("\nResponse:")
    print("  Text:", response.content)
    print("  Model:", response.model)
    print("  Tokens:", response.usage.total_tokens)
    print("  Finish reason:", response.finish_reason)


def streaming_example():
    """Streaming completion with Anthropic."""
    print("\n" + "=" * 60)
    print("Anthropic - Streaming")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY environment variable not set")
        return
    
    try:
        client = nimbus.provider("anthropic", api_key=api_key)
    except ImportError:
        print("⚠️  Anthropic provider not available")
        return
    
    messages = [UserMessage("Write a haiku about artificial intelligence")]
    
    print("\nStreaming response:")
    print("-" * 40)
    
    for chunk in client.stream(messages=messages, model="claude-3-sonnet-20240229"):
        print(chunk.delta, end="", flush=True)
    
    print("\n" + "-" * 40)


def claude_models():
    """Example with different Claude models."""
    print("\n" + "=" * 60)
    print("Anthropic - Claude Models")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY environment variable not set")
        return
    
    try:
        client = nimbus.provider("anthropic", api_key=api_key)
    except ImportError:
        print("⚠️  Anthropic provider not available")
        return
    
    models = [
        ("claude-3-opus-20240229", "Claude 3 Opus (most capable)"),
        ("claude-3-sonnet-20240229", "Claude 3 Sonnet (balanced)"),
        ("claude-3-haiku-20240307", "Claude 3 Haiku (fastest)"),
    ]
    
    prompt = "What is the meaning of life?"
    messages = [UserMessage(prompt)]
    
    print(f"\nPrompt: {prompt}")
    print("-" * 40)
    
    for model_id, model_name in models:
        print(f"\n{model_name}:")
        
        response = client.complete(messages=messages, model=model_id, max_tokens=100)
        print("  Response:", response.content[:80], "...")
        print("  Tokens:", response.usage.total_tokens)


def system_message_example():
    """Example showing Anthropic's system message handling."""
    print("\n" + "=" * 60)
    print("Anthropic - System Messages")
    print("=" * 60)
    
    print("""
Anthropic handles system messages differently than other providers.
The system message is sent separately from the conversation messages.

Example:

```python
import nimbus
from nimbus.messages import SystemMessage, UserMessage

client = nimbus.provider("anthropic", api_key="sk-ant-...")

messages = [
    SystemMessage("You are a Python expert."),
    UserMessage("How do I use decorators?")
]

response = client.complete(messages=messages, model="claude-3-sonnet-20240229")
```

Nimbus automatically handles this difference for you!
""")


def multi_turn_conversation():
    """Multi-turn conversation example."""
    print("\n" + "=" * 60)
    print("Anthropic - Multi-Turn Conversation")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY environment variable not set")
        return
    
    try:
        client = nimbus.provider("anthropic", api_key=api_key)
    except ImportError:
        print("⚠️  Anthropic provider not available")
        return
    
    # First turn
    print("\nTurn 1: User asks about Python")
    messages = [UserMessage("What is a Python list?")]
    
    response1 = client.complete(
        messages=messages, model="claude-3-sonnet-20240229", max_tokens=150
    )
    print(f"Assistant: {response1.content[:100]}...")
    
    # Second turn - continue conversation
    print("\nTurn 2: User asks follow-up question")
    messages.append(response1.to_message())
    messages.append(UserMessage("How do I add items to a list?"))
    
    response2 = client.complete(
        messages=messages, model="claude-3-sonnet-20240229", max_tokens=150
    )
    print(f"Assistant: {response2.content[:100]}...")


def main():
    """Run all examples."""
    print("\n" + "🧠 " * 20)
    print("NIMBUS - Anthropic Provider Examples")
    print("🧠 " * 20)
    
    try:
        basic_completion()
        streaming_example()
        claude_models()
        system_message_example()
        multi_turn_conversation()
        
        print("\n" + "=" * 60)
        print("✅ Examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Installed nimbus[anthropic]: pip install nimbus[anthropic]")
        print("  2. Set ANTHROPIC_API_KEY: export ANTHROPIC_API_KEY='sk-ant-...'")


if __name__ == "__main__":
    main()
