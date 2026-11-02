---
title: "Function calling (capabilities)"
status: current
last_updated: 2026-11-02
---

## Function Calling (Capabilities)

Skye supports two ways to provide capabilities to the LLM:

1. **Direct list** - Pass capabilities as an array (simple, no registry needed)
2. **CapabilityRegistry** - Pass a registry for search/discovery (advanced)

### Option 1: Direct Capabilities (Recommended)

```python
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage
from skye.tools import capability

# Define capability using decorator
@capability
def get_weather(location: str) -> str:
    """Get weather for a location.
    
    Args:
        location: The city or location to get weather for
    """
    return f"Weather in {location}: Sunny, 72°F"

client = create_provider("openai", api_key="sk-...")

# Pass capabilities directly - no registry needed!
response = client.complete(
    messages=[UserMessage(content="What's the weather in San Francisco?")],
    model="gpt-4",
    capabilities=[get_weather]  # Direct list
)

# Check if model requested capability calls
if response.has_capability_calls():
    # Option 1: Execute automatically (no registry needed!)
    capability_messages = await response.execute_capability_calls()
    
    # Option 2: Execute individually with control
    capability_messages = []
    for capability in response.get_capability_calls():
        # Execute with LLM-provided arguments
        msg = capability.execute()
        
        # Or override specific arguments
        msg = capability.execute(location="New York")  # Override location
        
        capability_messages.append(msg)
    
    # Option 3: Execute with argument overrides
    overrides = {
        "call_123": {"units": "celsius"}  # Override specific call arguments
    }
    capability_messages = await response.execute_capability_calls(
        argument_overrides=overrides
    )
    
    # Continue conversation with results
    final_response = client.complete(
        messages=[
            UserMessage(content="What's the weather in San Francisco?"),
            response.to_message(),  # Assistant's response with capability calls
            *capability_messages    # Spread capability results as messages
        ],
        model="gpt-4"
    )
    
    print(final_response.content)
```

### Option 2: CapabilityRegistry with Manual Search

Search for relevant tools and pass the results:

```python
from skye.tools import capability, CapabilityRegistry

# Define multiple capabilities
@capability
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    return f"Weather in {location}: Sunny, 72°F"

@capability
def get_forecast(location: str, days: int = 3) -> str:
    """Get weather forecast for multiple days."""
    return f"{days}-day forecast for {location}"

# Create registry with tools
registry = CapabilityRegistry(capabilities=[get_weather, get_forecast])

# Search for relevant tools
search_results = registry.search("weather forecast")
selected_tools = [cap for name, cap, score in search_results]

# Pass search results
response = client.complete(
    messages=[UserMessage(content="What's the weather like?")],
    model="gpt-4",
    capabilities=selected_tools  # Pass search results
)
```

### Option 3: CapabilityRegistry with Automatic Search

Pass the registry directly - search happens automatically:

```python
# Create registry with tools
registry = CapabilityRegistry(capabilities=[get_weather, get_forecast])

# Pass registry - search happens automatically
response = client.complete(
    messages=[UserMessage(content="What's the weather like?")],
    model="gpt-4",
    capabilities=registry  # Registry enables automatic search
)
```

**When to use each approach:**
- **Direct list**: Simple use cases, fixed set of tools
- **Manual search**: You control which tools based on context
- **Automatic search**: Let the system find relevant tools dynamically

**Important**: In all cases, you can execute capabilities without the registry:
```python
if response.has_capability_calls():
    messages = await response.execute_capability_calls()  # No registry needed!
```
