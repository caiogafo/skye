"""Anthropic Provider Example.

This example demonstrates how to use the Anthropic provider with Nimbus.

Features shown:
- Basic completion with Claude
- Streaming responses
- System messages (Anthropic-specific)
- Token usage tracking
"""

import os
from nimbus.completion import CompletionRequest
from nimbus.messages import UserMessage, SystemMessage
from nimbus.providers import ProviderRegistry


def basic_completion():
    """Basic completion with Anthropic."""
    print("=" * 60)
    print("Anthropic Basic Completion")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY environment variable not set")
        print("   Set it with: export ANTHROPIC_API_KEY='sk-ant-...'")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider(
            "anthropic",
            api_key=api_key
        )
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use Anthropic, install with: pip install nimbus[anthropic]")
        return
    
    request = CompletionRequest(
        messages=[
            SystemMessage(content="You are a helpful assistant specialized in science."),
            UserMessage(content="Explain photosynthesis in simple terms")
        ],
        model="claude-3-sonnet-20240229",
        temperature=0.7,
        max_tokens=200
    )
    
    print("\nRequest:")
    print(f"  Model: {request.model}")
    print(f"  Temperature: {request.temperature}")
    print(f"  Messages: {len(request.messages)}")
    
    try:
        response = provider.complete(request)
        
        print("\nResponse:")
        print(f"  Content: {response.content}")
        print(f"  Provider: {response.provider}")
        print(f"  Tokens used: {response.usage.total_tokens}")
        print(f"  Finish reason: {response.finish_reason}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def streaming_example():
    """Streaming completion with Anthropic."""
    print("\n" + "=" * 60)
    print("Anthropic Streaming")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider(
            "anthropic",
            api_key=api_key
        )
    except ImportError:
        print("⚠️  Anthropic provider not available")
        return
    
    request = CompletionRequest(
        messages=[
            UserMessage(content="Write a haiku about artificial intelligence")
        ],
        model="claude-3-sonnet-20240229",
        stream=True
    )
    
    print("\nStreaming response:")
    print("-" * 40)
    
    try:
        for chunk in provider.stream(request):
            print(chunk.delta, end="", flush=True)
        print("\n" + "-" * 40)
    except Exception as e:
        print(f"\n❌ Error: {e}")


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
        provider = ProviderRegistry.get_model_provider(
            "anthropic",
            api_key=api_key
        )
    except ImportError:
        print("⚠️  Anthropic provider not available")
        return
    
    models = [
        ("claude-3-opus-20240229", "Claude 3 Opus (most capable)"),
        ("claude-3-sonnet-20240229", "Claude 3 Sonnet (balanced)"),
        ("claude-3-haiku-20240307", "Claude 3 Haiku (fastest)"),
    ]
    
    prompt = "What is the meaning of life?"
    
    print(f"\nPrompt: {prompt}")
    print("-" * 40)
    
    for model_id, model_name in models:
        print(f"\n{model_name}:")
        
        request = CompletionRequest(
            messages=[UserMessage(content=prompt)],
            model=model_id,
            max_tokens=100
        )
        
        try:
            response = provider.complete(request)
            print(f"  Response: {response.content[:80]}...")
            print(f"  Tokens: {response.usage.total_tokens}")
        except Exception as e:
            print(f"  ⚠️  Error: {str(e)[:60]}...")


def system_message_example():
    """Example showing Anthropic's system message handling."""
    print("\n" + "=" * 60)
    print("Anthropic - System Messages")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider(
            "anthropic",
            api_key=api_key
        )
    except ImportError:
        print("⚠️  Anthropic provider not available")
        return
    
    print("""
Anthropic handles system messages differently than other providers.
The system message is sent separately from the conversation messages.

Example:

```python
request = CompletionRequest(
    messages=[
        SystemMessage(content="You are a Python expert."),
        UserMessage(content="How do I use decorators?")
    ],
    model="claude-3-sonnet-20240229"
)

response = provider.complete(request)
```

Nimbus automatically handles this difference for you!
""")


def multi_turn_conversation():
    """Multi-turn conversation example."""
    print("\n" + "=" * 60)
    print("Anthropic Multi-Turn Conversation")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider(
            "anthropic",
            api_key=api_key
        )
    except ImportError:
        print("⚠️  Anthropic provider not available")
        return
    
    # First turn
    print("\nTurn 1: User asks about Python")
    request = CompletionRequest(
        messages=[
            UserMessage(content="What is a Python list?")
        ],
        model="claude-3-sonnet-20240229",
        max_tokens=150
    )
    
    try:
        response1 = provider.complete(request)
        print(f"Assistant: {response1.content[:100]}...")
        
        # Second turn - continue conversation
        print("\nTurn 2: User asks follow-up question")
        request = CompletionRequest(
            messages=[
                UserMessage(content="What is a Python list?"),
                response1.to_message(),
                UserMessage(content="How do I add items to a list?")
            ],
            model="claude-3-sonnet-20240229",
            max_tokens=150
        )
        
        response2 = provider.complete(request)
        print(f"Assistant: {response2.content[:100]}...")
    except Exception as e:
        print(f"\n❌ Error: {e}")


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
