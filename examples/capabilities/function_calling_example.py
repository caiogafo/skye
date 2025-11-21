"""Function Calling Example.

This example demonstrates how to use function calling (capability use) with Nimbus.

Features shown:
- Defining capabilities/functions
- Handling capability calls from models
- Multi-turn conversations with capability results
- Different provider implementations

Note: Set environment variables for API keys:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- AWS credentials for Bedrock
"""

import os
import json
import asyncio
import nimbus
from nimbus.messages import UserMessage, CapabilityMessage
from nimbus.capabilities.registry import CapabilityRegistry


def basic_function_calling():
    """Basic function calling example."""
    print("=" * 60)
    print("Function Calling - Basic Example")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = nimbus.provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Define capabilities
    capabilities = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    print("\nCapabilities defined:")
    print(f"  - get_weather(location: str, unit?: str)")
    
    print("\nRequest:")
    print(f"  Model: gpt-4")
    print(f"  Capabilities: {len(capabilities)}")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="What's the weather in San Francisco?")
            ],
            model="gpt-4",
            capabilities=capabilities
        )
        
        print("\nResponse:")
        print(f"  Content: {response.content}")
        
        if response.capability_calls:
            print(f"  Capability calls: {len(response.capability_calls)}")
            for call in response.capability_calls:
                print(f"    - {call['function']['name']}")
                print(f"      Args: {call['function']['arguments']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def function_execution_workflow():
    """Example of executing functions and continuing conversation."""
    print("\n" + "=" * 60)
    print("Function Calling - Execution Workflow")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = nimbus.provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Define capabilities
    capabilities = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    # Mock weather function
    def get_weather(location: str) -> str:
        weather_data = {
            "San Francisco": "Sunny, 72°F",
            "New York": "Cloudy, 65°F",
            "London": "Rainy, 55°F"
        }
        return weather_data.get(location, "Unknown location")
    
    print("\nStep 1: Initial request")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="What's the weather in San Francisco and New York?")
            ],
            model="gpt-4",
            capabilities=capabilities
        )
        print(f"  Assistant: {response.content[:80]}...")
        
        if response.has_capability_calls():
            print(f"\nStep 2: Execute capabilities")
            print(f"  Found {len(response.capability_calls)} capability call(s)")
            
            # Execute all capability calls and get messages
            registry = CapabilityRegistry.get_instance()
            capability_messages = await response.execute_capability_calls(registry)
            
            for msg in capability_messages:
                print(f"  {msg.capability_name}: {msg.content[:60]}...")
            
            print(f"\nStep 3: Continue conversation with results")
            
            # Continue conversation with capability results
            final_response = provider.complete(
                messages=[
                    UserMessage(content="What's the weather in San Francisco and New York?"),
                    response.to_message(),
                    *capability_messages  # Spread capability messages
                ],
                model="gpt-4",
                capabilities=capabilities
            )
            print(f"  Assistant: {final_response.content}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def multiple_functions():
    """Example with multiple functions."""
    print("\n" + "=" * 60)
    print("Function Calling - Multiple Functions")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = nimbus.provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Define multiple capabilities
    capabilities = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_time",
                "description": "Get current time for a timezone",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {"type": "string"}
                    },
                    "required": ["timezone"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search",
                "description": "Search for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    print("\nCapabilities defined:")
    for cap in capabilities:
        func = cap['function']
        print(f"  - {func['name']}: {func['description']}")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="What's the weather in Paris and what time is it there?")
            ],
            model="gpt-4",
            capabilities=capabilities
        )
        
        print("\nResponse:")
        print(f"  Content: {response.content[:80]}...")
        
        if response.capability_calls:
            print(f"  Capability calls: {len(response.capability_calls)}")
            for call in response.capability_calls:
                print(f"    - {call['function']['name']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def anthropic_tool_use():
    """Example with Anthropic tool use."""
    print("\n" + "=" * 60)
    print("Function Calling - Anthropic Tool Use")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY environment variable not set")
        return
    
    try:
        provider = nimbus.provider("anthropic", api_key=api_key)
    except ImportError:
        print("⚠️  Anthropic provider not available")
        return
    
    print("""
Anthropic uses "tool use" instead of "function calling".
Nimbus handles the differences transparently.

Example:

```python
capabilities = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    }
]

request = CompletionRequest(
    messages=[
        UserMessage(content="What is 25 * 4?")
    ],
    model="claude-3-sonnet-20240229",
    capabilities=capabilities
)

response = provider.complete(request)

if response.capability_calls:
    for call in response.capability_calls:
        print(f"Tool: {call['function']['name']}")
        print(f"Args: {call['function']['arguments']}")
```

Nimbus automatically converts between provider formats!
""")


def bedrock_tool_use():
    """Example with Bedrock tool use."""
    print("\n" + "=" * 60)
    print("Function Calling - Bedrock Tool Use")
    print("=" * 60)
    
    print("""
AWS Bedrock also supports tool use through the Converse API.
Nimbus provides a unified interface across all providers.

Example:

```python
import nimbus

provider = nimbus.provider(
    "bedrock",
    region="us-east-1"
)

capabilities = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get current stock price",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"}
                },
                "required": ["symbol"]
            }
        }
    }
]

request = CompletionRequest(
    messages=[
        UserMessage(content="What's the price of AAPL stock?")
    ],
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    capabilities=capabilities
)

response = provider.complete(request)
```

Same code works across OpenAI, Anthropic, and Bedrock!
""")


async def main():
    """Run all examples."""
    print("\n" + "🔧 " * 20)
    print("NIMBUS - Function Calling Examples")
    print("🔧 " * 20)
    
    try:
        basic_function_calling()
        await function_execution_workflow()
        multiple_functions()
        anthropic_tool_use()
        bedrock_tool_use()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        print("\nKey points:")
        print("  • Define capabilities using JSON schema")
        print("  • Models can request capability calls")
        print("  • Execute capabilities and send results back")
        print("  • Nimbus handles provider differences transparently")
        print("  • Works with OpenAI, Anthropic, and Bedrock")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
