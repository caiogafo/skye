"""Router Example - Load Balancing with Structured Configuration.

This example demonstrates how to use Nimbus RouterRegistry with structured Pydantic models
for load balancing across multiple model deployments.

Features shown:
- Structured configuration with Pydantic models
- Multiple targets with same alias
- Load balancing strategies
- Routing metrics
"""

import os
import nimbus
from nimbus import routes as rt
from nimbus.messages import UserMessage


def basic_router_example():
    """Basic router with multiple targets - actually calls LLM."""
    print("=" * 60)
    print("RouterRegistry - Basic Load Balancing")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, skipping actual LLM calls")
        print("   This example would load balance between multiple deployments")
        return
    
    # Define registry with multiple targets for same alias
    # In real scenario, you'd have different API keys or endpoints
    registry = rt.RouterRegistry([
        rt.RouteConfig(
            alias="gpt-3.5-turbo",
            targets=[
                rt.ModelTarget(
                    model="gpt-3.5-turbo",
                    provider="openai",
                    api_key=api_key,
                    metadata={"deployment": "primary"}
                ),
                rt.ModelTarget(
                    model="gpt-3.5-turbo",
                    provider="openai",
                    api_key=api_key,
                    metadata={"deployment": "secondary"}
                ),
            ],
            strategy="round-robin"
        )
    ])
    
    print(f"\nRegistered aliases: {registry.list_aliases()}")
    
    route = registry.get_route("gpt-3.5-turbo")
    if route:
        print(f"Targets for 'gpt-3.5-turbo': {len(route.targets)}")
    
    # Create client with registry
    try:
        client = nimbus.provider("openai", router=registry)
        
        # Use the alias - registry will load balance
        messages = [UserMessage("What is 2+2?")]
        
        print("\nMaking 3 requests with round-robin load balancing:")
        for i in range(3):
            selected_model = registry.resolve_model("gpt-3.5-turbo")
            print(f"\n  Request {i+1}: Routed to {selected_model}")
            
            try:
                response = client.complete(
                    messages=messages,
                    model="gpt-3.5-turbo",  # Alias - router resolves it
                    max_tokens=50
                )
                print(f"  Response: {response.content[:60]}...")
                print(f"  Tokens: {response.usage.total_tokens}")
            except Exception as e:
                print(f"  Error: {str(e)[:80]}")
    
    except Exception as e:
        print(f"\n❌ Error setting up client: {e}")


def multi_model_router():
    """Registry with multiple model aliases - demonstrates custom aliases."""
    print("\n" + "=" * 60)
    print("RouterRegistry - Multiple Model Aliases")
    print("=" * 60)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        print("⚠️  OPENAI_API_KEY not set, showing configuration only")
        print("   This example demonstrates custom aliases like 'fast' and 'smart'")
        return
    
    registry = rt.RouterRegistry([
        # Fast models route - for quick responses
        rt.RouteConfig(
            alias="fast",
            targets=[
                rt.ModelTarget(
                    model="gpt-3.5-turbo",
                    provider="openai",
                    api_key=openai_key
                ),
            ],
            strategy="round-robin"
        ),
        # Smart models route - for complex tasks
        rt.RouteConfig(
            alias="smart",
            targets=[
                rt.ModelTarget(
                    model="gpt-4",
                    provider="openai",
                    api_key=openai_key
                ),
            ],
            strategy="round-robin"
        ),
    ])
    
    print(f"\nAvailable aliases: {registry.list_aliases()}")
    
    try:
        client = nimbus.provider("openai", router=registry)
        
        # Use 'fast' alias for simple question
        print("\n--- Using 'fast' alias for simple math ---")
        selected = registry.resolve_model("fast")
        print(f"Routes to: {selected}")
        
        try:
            response = client.complete(
                messages=[UserMessage("What is 5 + 7?")],
                model="fast",
                max_tokens=30
            )
            print(f"Response: {response.content}")
        except Exception as e:
            print(f"Error: {str(e)[:80]}")
        
        # Use 'smart' alias for complex question
        print("\n--- Using 'smart' alias for complex reasoning ---")
        selected = registry.resolve_model("smart")
        print(f"Routes to: {selected}")
        
        try:
            response = client.complete(
                messages=[UserMessage("Explain quantum entanglement in simple terms")],
                model="smart",
                max_tokens=100
            )
            print(f"Response: {response.content[:150]}...")
        except Exception as e:
            print(f"Error: {str(e)[:80]}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")


def routing_strategies():
    """Demonstrate different routing strategies with actual calls."""
    print("\n" + "=" * 60)
    print("RouterRegistry - Routing Strategies")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, showing strategies only")
        strategies = ["round-robin", "random", "least-busy", "least-latency", "weighted"]
        for strategy in strategies:
            print(f"\n{strategy}:")
            print(f"  Description: {_get_strategy_description(strategy)}")
        return
    
    # Demonstrate round-robin strategy
    print("\n--- Round-Robin Strategy ---")
    print("Distributes requests evenly across targets in order")
    
    registry = rt.RouterRegistry([
        rt.RouteConfig(
            alias="balanced",
            targets=[
                rt.ModelTarget(model="gpt-3.5-turbo", provider="openai", api_key=api_key, weight=1.0),
                rt.ModelTarget(model="gpt-3.5-turbo", provider="openai", api_key=api_key, weight=1.0),
            ],
            strategy="round-robin"
        )
    ])
    
    try:
        client = nimbus.provider("openai", router=registry)
        
        print("\nMaking 4 requests to see round-robin in action:")
        for i in range(4):
            selected = registry.resolve_model("balanced")
            print(f"  Request {i+1}: {selected}")
    
    except Exception as e:
        print(f"Error: {e}")


def _get_strategy_description(strategy: str) -> str:
    """Get description for a routing strategy."""
    descriptions = {
        "round-robin": "Distributes requests evenly in order",
        "random": "Randomly selects a target",
        "least-busy": "Routes to target with fewest active calls",
        "least-latency": "Routes to target with lowest average latency",
        "weighted": "Random selection based on target weights"
    }
    return descriptions.get(strategy, "Unknown strategy")


def azure_multi_region():
    """Registry for Azure multi-region deployments with failover."""
    print("\n" + "=" * 60)
    print("RouterRegistry - Azure Multi-Region with Failover")
    print("=" * 60)
    
    print("""
This example shows how to configure multi-region Azure deployments
for automatic failover and load balancing.

Configuration:
""")
    
    registry = rt.RouterRegistry([
        rt.RouteConfig(
            alias="gpt-4",
            targets=[
                rt.ModelTarget(
                    model="azure/gpt-4",
                    provider="azure",
                    api_key=os.getenv("AZURE_OPENAI_API_KEY_EAST"),
                    api_base="https://my-resource-east.openai.azure.com",
                    api_version="2024-02-15-preview",
                    region="us-east-1",
                    metadata={"priority": "primary"}
                ),
                rt.ModelTarget(
                    model="azure/gpt-4",
                    provider="azure",
                    api_key=os.getenv("AZURE_OPENAI_API_KEY_WEST"),
                    api_base="https://my-resource-west.openai.azure.com",
                    api_version="2024-02-15-preview",
                    region="us-west-2",
                    metadata={"priority": "secondary"}
                ),
            ],
            strategy="least-latency",
            fallback_on_error=True
        )
    ])
    
    print("\nAzure multi-region setup:")
    route = registry.get_route("gpt-4")
    if route:
        for i, target in enumerate(route.targets, 1):
            priority = target.metadata.get("priority", "unknown")
            print(f"  {i}. {target.model} in {target.region} ({priority})")
        print(f"\nStrategy: {route.strategy}")
        print(f"Fallback on error: {route.fallback_on_error}")
    
    print("\nBenefits:")
    print("  - Automatic failover if primary region is down")
    print("  - Load balancing based on latency")
    print("  - Geographic redundancy")


def bedrock_multi_region():
    """Registry for Bedrock multi-region deployments with actual call."""
    print("\n" + "=" * 60)
    print("RouterRegistry - Bedrock Multi-Region")
    print("=" * 60)
    
    # Check if AWS credentials are available
    has_aws = os.getenv("AWS_PROFILE") or os.getenv("AWS_ACCESS_KEY_ID")
    
    registry = rt.RouterRegistry([
        rt.RouteConfig(
            alias="claude",
            targets=[
                rt.ModelTarget(
                    model="anthropic.claude-3-sonnet-20240229-v1:0",
                    provider="bedrock",
                    region="us-east-1",
                    metadata={"location": "Virginia"}
                ),
                rt.ModelTarget(
                    model="anthropic.claude-3-sonnet-20240229-v1:0",
                    provider="bedrock",
                    region="us-west-2",
                    metadata={"location": "Oregon"}
                ),
            ],
            strategy="round-robin"
        )
    ])
    
    print("\nBedrock multi-region setup:")
    route = registry.get_route("claude")
    if route:
        for i, target in enumerate(route.targets, 1):
            location = target.metadata.get("location", "unknown")
            print(f"  {i}. {target.model}")
            print(f"     Region: {target.region} ({location})")
    
    if not has_aws:
        print("\n⚠️  AWS credentials not configured, skipping actual call")
        print("   Set AWS_PROFILE or AWS credentials to test")
        return
    
    try:
        print("\n--- Making request with router ---")
        client = nimbus.provider("bedrock", router=registry)
        
        selected = registry.resolve_model("claude")
        print(f"Routed to: {selected}")
        
        response = client.complete(
            messages=[UserMessage("What is AWS Bedrock?")],
            model="claude",  # Alias - router resolves to actual model
            max_tokens=100
        )
        
        print(f"\nResponse: {response.content[:150]}...")
        print(f"Tokens: {response.usage.total_tokens}")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)[:100]}")


def main():
    """Run all examples."""
    print("\n" + "🔀 " * 20)
    print("NIMBUS - RouterRegistry Examples")
    print("🔀 " * 20)
    
    try:
        basic_router_example()
        multi_model_router()
        routing_strategies()
        azure_multi_region()
        bedrock_multi_region()
        
        print("\n" + "=" * 60)
        print("✅ Examples completed!")
        print("=" * 60)
        print("\nNote: These examples show configuration structure.")
        print("To actually run them, set the appropriate API keys.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
