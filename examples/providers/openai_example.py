"""OpenAI Provider Example (Boto3-style Nimbus API).

This version demonstrates:
- Basic completion with messages
- Streaming responses
- Async operations
- Multi-turn conversations
- Simple client creation: nimbus.provider("openai")
"""

import asyncio
import os
import nimbus
from nimbus.messages import UserMessage, SystemMessage


def basic_completion():
    """Basic completion with OpenAI."""
    print("=" * 60)
    print("OpenAI - Basic Completion")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='sk-...'")
        return
    
    client = nimbus.provider("openai", api_key=api_key)
    
    messages = [
        SystemMessage("You are a helpful assistant."),
        UserMessage("What is the capital of France?"),
    ]
    
    response = client.complete(
        messages=messages, model="gpt-4", temperature=0.7, max_tokens=100
    )
    
    print("\nResponse:")
    print("  Text:", response.content)
    print("  Model:", response.model)
    print("  Tokens:", response.usage.total_tokens)
    print("  Finish reason:", response.finish_reason)


def streaming_example():
    """Streaming completion with OpenAI."""
    print("\n" + "=" * 60)
    print("OpenAI - Streaming")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    client = nimbus.provider("openai", api_key=api_key)
    
    messages = [UserMessage("Write a short poem about Python programming")]
    
    print("\nStreaming response:")
    print("-" * 40)
    
    for chunk in client.stream(messages=messages, model="gpt-4"):
        print(chunk.delta, end="", flush=True)
    
    print("\n" + "-" * 40)


async def async_completion():
    """Async completion with OpenAI."""
    print("\n" + "=" * 60)
    print("OpenAI - Async Completion")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    client = nimbus.provider("openai", api_key=api_key)
    
    messages = [UserMessage("Explain async/await in Python")]
    
    print("\nMaking async request...")
    response = await client.acomplete(messages=messages, model="gpt-4", max_tokens=200)
    
    print("  Response:", response.content[:100], "...")
    print("  Tokens:", response.usage.total_tokens)


def multi_turn_conversation():
    """Multi-turn conversation example."""
    print("\n" + "=" * 60)
    print("OpenAI - Multi-Turn Conversation")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    client = nimbus.provider("openai", api_key=api_key)
    
    # First turn
    print("\nTurn 1: User asks a question")
    messages = [UserMessage("What is machine learning?")]
    
    response1 = client.complete(messages=messages, model="gpt-4", max_tokens=150)
    print(f"Assistant: {response1.content[:100]}...")
    
    # Second turn - continue conversation
    print("\nTurn 2: User asks follow-up question")
    messages.append(response1.to_message())
    messages.append(UserMessage("Can you give me a practical example?"))
    
    response2 = client.complete(messages=messages, model="gpt-4", max_tokens=150)
    print(f"Assistant: {response2.content[:100]}...")


def router_example():
    """Example using router for load balancing."""
    print("\n" + "=" * 60)
    print("OpenAI - Router for Load Balancing")
    print("=" * 60)
    
    print("""
Use RouterRegistry for load balancing across deployments:

```python
import nimbus
from nimbus import routes as rt
from nimbus.messages import UserMessage

# Define load balancing setup
registry = rt.RouterRegistry([
    rt.RouteConfig(
        alias="gpt-4",
        targets=[
            rt.ModelTarget(
                model="gpt-4",
                provider="openai",
                api_key=os.getenv("OPENAI_API_KEY_1")
            ),
            rt.ModelTarget(
                model="gpt-4",
                provider="openai",
                api_key=os.getenv("OPENAI_API_KEY_2")
            ),
        ],
        strategy="least-busy"
    ),
    rt.RouteConfig(
        alias="fast",
        targets=[
            rt.ModelTarget(model="gpt-3.5-turbo", provider="openai", api_key="..."),
            rt.ModelTarget(model="gpt-3.5-turbo-16k", provider="openai", api_key="..."),
        ],
        strategy="round-robin"
    )
])

# Create client with router
client = nimbus.provider("openai", router=registry)

# Use alias - router handles selection
response = client.complete(
    messages=[UserMessage("Hello")],
    model="fast"  # Routes to gpt-3.5-turbo or gpt-3.5-turbo-16k
)
```

Benefits:
- Load balance across multiple API keys
- Automatic failover on rate limits
- Custom aliases for model groups
""")


def main():
    """Run all examples."""
    print("\n" + "🤖 " * 20)
    print("NIMBUS - OpenAI Provider Examples")
    print("🤖 " * 20)
    
    try:
        basic_completion()
        streaming_example()
        multi_turn_conversation()
        router_example()
        
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
