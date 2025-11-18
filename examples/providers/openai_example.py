"""OpenAI Provider Example.

This example demonstrates how to use the OpenAI provider with Nimbus.

Features shown:
- Basic completion
- Streaming responses
- Async operations
- Token usage tracking
"""

import asyncio
import os
from nimbus.completion import CompletionRequest
from nimbus.messages import UserMessage, SystemMessage
from nimbus.providers import ProviderRegistry


def basic_completion():
    """Basic completion example."""
    print("=" * 60)
    print("OpenAI Basic Completion")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='sk-...'")
        return
    
    provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    
    request = CompletionRequest(
        messages=[
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="What is the capital of France?")
        ],
        model="gpt-4",
        temperature=0.7,
        max_tokens=100
    )
    
    print("\nRequest:")
    print(f"  Model: {request.model}")
    print(f"  Temperature: {request.temperature}")
    print(f"  Messages: {len(request.messages)}")
    
    response = provider.complete(request)
    
    print("\nResponse:")
    print(f"  Content: {response.content}")
    print(f"  Provider: {response.provider}")
    print(f"  Tokens used: {response.usage.total_tokens}")
    print(f"  Finish reason: {response.finish_reason}")


def streaming_example():
    """Streaming completion example."""
    print("\n" + "=" * 60)
    print("OpenAI Streaming")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    
    request = CompletionRequest(
        messages=[
            UserMessage(content="Write a short poem about Python programming")
        ],
        model="gpt-4",
        stream=True
    )
    
    print("\nStreaming response:")
    print("-" * 40)
    
    for chunk in provider.stream(request):
        print(chunk.delta, end="", flush=True)
    
    print("\n" + "-" * 40)


async def async_completion():
    """Async completion example."""
    print("\n" + "=" * 60)
    print("OpenAI Async Completion")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    
    request = CompletionRequest(
        messages=[
            UserMessage(content="Explain async/await in Python")
        ],
        model="gpt-4",
        max_tokens=200
    )
    
    print("\nMaking async request...")
    response = await provider.acomplete(request)
    
    print(f"Response: {response.content[:100]}...")
    print(f"Tokens: {response.usage.total_tokens}")


def multi_turn_conversation():
    """Multi-turn conversation example."""
    print("\n" + "=" * 60)
    print("OpenAI Multi-Turn Conversation")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    
    # First turn
    print("\nTurn 1: User asks a question")
    request = CompletionRequest(
        messages=[
            UserMessage(content="What is machine learning?")
        ],
        model="gpt-4",
        max_tokens=150
    )
    
    response1 = provider.complete(request)
    print(f"Assistant: {response1.content[:100]}...")
    
    # Second turn - continue conversation
    print("\nTurn 2: User asks follow-up question")
    request = CompletionRequest(
        messages=[
            UserMessage(content="What is machine learning?"),
            response1.to_message(),
            UserMessage(content="Can you give me a practical example?")
        ],
        model="gpt-4",
        max_tokens=150
    )
    
    response2 = provider.complete(request)
    print(f"Assistant: {response2.content[:100]}...")


def main():
    """Run all examples."""
    print("\n" + "🤖 " * 20)
    print("NIMBUS - OpenAI Provider Examples")
    print("🤖 " * 20)
    
    try:
        basic_completion()
        streaming_example()
        multi_turn_conversation()
        
        # Run async example
        print("\n" + "=" * 60)
        print("Running async example...")
        print("=" * 60)
        asyncio.run(async_completion())
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Installed nimbus[openai]: pip install nimbus[openai]")
        print("  2. Set OPENAI_API_KEY: export OPENAI_API_KEY='sk-...'")


if __name__ == "__main__":
    main()
