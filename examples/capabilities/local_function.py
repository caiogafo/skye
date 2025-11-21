"""Local Function Capability Example.

This example demonstrates how to use local Python functions as capabilities
that can be invoked by language models.

Features shown:
- Wrapping Python functions as capabilities using the @capability decorator
- Automatic schema generation from function signatures
- Executing capabilities locally
- Returning results to the model
- Both synchronous and asynchronous functions
- Multi-turn conversations with capability results

Note: Set environment variables for API keys:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
"""

import os
import json
import asyncio
import nimbus
from nimbus.messages import UserMessage, CapabilityMessage
from nimbus.capabilities import capability


# Define capabilities using the @capability decorator
@capability
def get_weather(location: str, unit: str = "fahrenheit") -> dict:
    """Get the current weather for a location.
    
    Args:
        location: City name or location
        unit: Temperature unit (fahrenheit or celsius)
    
    Returns:
        Dictionary with weather information
    """
    # Mock weather data
    weather_data = {
        "San Francisco": {"temp": 72, "condition": "Sunny", "humidity": 65},
        "New York": {"temp": 65, "condition": "Cloudy", "humidity": 75},
        "London": {"temp": 55, "condition": "Rainy", "humidity": 85},
        "Tokyo": {"temp": 68, "condition": "Clear", "humidity": 60},
    }
    
    data = weather_data.get(location, {"temp": 70, "condition": "Unknown", "humidity": 50})
    
    # Convert temperature if needed
    if unit.lower() == "celsius":
        data["temp"] = round((data["temp"] - 32) * 5 / 9, 1)
    
    return data


@capability
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2 * 3")
    
    Returns:
        The result of the calculation
    """
    try:
        # Use eval for simple math (in production, use a safer parser)
        result = eval(expression)
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


def basic_local_function_example():
    """Basic example of using local functions as capabilities."""
    print("=" * 60)
    print("Local Function Capabilities - Basic Example")
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
    
    # Pass capabilities directly - no need to convert to dict!
    capabilities = [get_weather, calculate]
    
    print("\nCapabilities defined:")
    for cap in capabilities:
        schema = cap.get_schema()
        print(f"  - {schema.name}: {schema.description}")
    
    print("\nRequest:")
    print(f"  Model: gpt-4")
    print(f"  Message: What's the weather in San Francisco and what is 25 * 4?")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="What's the weather in San Francisco and what is 25 * 4?")
            ],
            model="gpt-4",
            capabilities=capabilities
        )
        
        print("\nResponse:")
        print(f"  Content: {response.content}")
        
        if response.capability_calls:
            print(f"\n  Capability calls: {len(response.capability_calls)}")
            for call in response.capability_calls:
                func_name = call['function']['name']
                args = call['function']['arguments']
                print(f"    - {func_name}({args})")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def execute_and_continue_example():
    """Example of executing capabilities and continuing the conversation."""
    print("\n" + "=" * 60)
    print("Local Function Capabilities - Execute and Continue")
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
    
    # Pass capabilities directly
    capabilities = [get_weather, calculate]
    
    print("\nStep 1: Initial request")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="What's the weather in New York?")
            ],
            model="gpt-4",
            capabilities=capabilities
        )
        
        print(f"  Assistant: {response.content[:80]}...")
        
        if response.has_capability_calls():
            print(f"\nStep 2: Execute capabilities automatically")
            print(f"  Found {len(response.capability_calls)} capability call(s)")
            
            # Execute capabilities using the built-in method
            capability_messages = await response.execute_capability_calls()
            
            for msg in capability_messages:
                print(f"  {msg.capability_name}: {msg.content[:60]}...")
            
            print(f"\nStep 3: Continue conversation with results")
            
            # Continue conversation with capability results
            final_response = provider.complete(
                messages=[
                    UserMessage(content="What's the weather in New York?"),
                    response.to_message(),
                    *capability_messages
                ],
                model="gpt-4",
                capabilities=capabilities
            )
            print(f"  Assistant: {final_response.content}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def async_capability_example():
    """Example of using async capabilities."""
    print("\n" + "=" * 60)
    print("Local Function Capabilities - Async Example")
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
    
    # Define async capability
    @capability
    async def fetch_user_info(user_id: str) -> dict:
        """Fetch user information asynchronously."""
        await asyncio.sleep(0.1)
        users = {
            "user_123": {"name": "Alice", "email": "alice@example.com", "role": "admin"},
            "user_456": {"name": "Bob", "email": "bob@example.com", "role": "user"},
        }
        return users.get(user_id, {"error": f"User {user_id} not found"})
    
    # Pass capability directly
    capabilities = [fetch_user_info]
    
    print("\nCapabilities defined:")
    print(f"  - fetch_user_info: Fetch user information asynchronously")
    
    print("\nRequest:")
    print(f"  Model: gpt-4")
    print(f"  Message: Tell me about user_123")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="Tell me about user_123")
            ],
            model="gpt-4",
            capabilities=capabilities
        )
        
        print("\nResponse:")
        print(f"  Content: {response.content}")
        
        if response.capability_calls:
            print(f"\n  Capability calls: {len(response.capability_calls)}")
            
            # Execute async capabilities
            for call in response.capability_calls:
                func_name = call['function']['name']
                args = json.loads(call['function']['arguments'])
                
                if func_name == "fetch_user_info":
                    result = await fetch_user_info.aexecute(**args)
                    print(f"    - {func_name}({args}) = {result}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def capability_schema_example():
    """Example showing how capability schemas are automatically generated."""
    print("\n" + "=" * 60)
    print("Local Function Capabilities - Schema Generation")
    print("=" * 60)
    
    print("\nCapability schemas are automatically generated from function signatures:")
    
    # Show schema for get_weather
    schema = get_weather.get_schema()
    print(f"\n1. get_weather capability:")
    print(f"   Name: {schema.name}")
    print(f"   Description: {schema.description}")
    print(f"   Parameters:")
    for param_name, param_schema in schema.parameters.get("properties", {}).items():
        required = param_name in schema.parameters.get("required", [])
        print(f"     - {param_name}: {param_schema.get('type')} {'(required)' if required else '(optional)'}")
    
    # Show schema for calculate
    schema = calculate.get_schema()
    print(f"\n2. calculate capability:")
    print(f"   Name: {schema.name}")
    print(f"   Description: {schema.description}")
    print(f"   Parameters:")
    for param_name, param_schema in schema.parameters.get("properties", {}).items():
        required = param_name in schema.parameters.get("required", [])
        print(f"     - {param_name}: {param_schema.get('type')} {'(required)' if required else '(optional)'}")


async def main():
    """Run all examples."""
    print("\n" + "🔧 " * 20)
    print("NIMBUS - Local Function Capability Examples")
    print("🔧 " * 20)
    
    try:
        basic_local_function_example()
        await execute_and_continue_example()
        await async_capability_example()
        capability_schema_example()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        print("\nKey points:")
        print("  • Use @capability decorator to wrap Python functions")
        print("  • Schemas are automatically generated from function signatures")
        print("  • Supports both sync and async functions")
        print("  • Execute capabilities and send results back to the model")
        print("  • Works with any provider (OpenAI, Anthropic, Bedrock, etc.)")
        print("  • No need for CapabilityRegistry - use schemas directly")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
