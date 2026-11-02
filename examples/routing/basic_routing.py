"""Basic Routing Example.

This example demonstrates how to use Skye routers for load balancing
across multiple model deployments.

Features shown:
- Creating routers with multiple targets
- Round-robin load balancing
- Accessing routing metrics
- Different routing strategies
"""

import os
from skye.base.messages import UserMessage
from skye.base.interfaces.router import RoutingStrategy
from skye.router import ModelRouter, ModelTarget, RouteConfig


def basic_router_example():
    """Basic router with multiple targets."""
    print("=" * 60)
    print("Basic Router - Multiple Targets")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, showing configuration only")
        print("   This example would load balance between multiple deployments")
        return
    
    # Define router with multiple targets for same alias
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="gpt-3.5-turbo",
                targets=[
                    ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key=api_key,
                        tpm=200000,
                        rpm=2000,
                        metadata={"deployment": "primary"}
                    ),
                    ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key=api_key,
                        tpm=200000,
                        rpm=2000,
                        metadata={"deployment": "secondary"}
                    ),
                ],
                strategy=RoutingStrategy.ROUND_ROBIN
            )
        ]
    )
    
    print(f"\nRegistered aliases: {router.list_aliases()}")
    
    route = router.get_route("gpt-3.5-turbo")
    if route:
        print(f"Targets for 'gpt-3.5-turbo': {len(route.targets)}")
        for i, target in enumerate(route.targets, 1):
            print(f"  {i}. {target.provider}: {target.model}")
    
    # Make requests with round-robin load balancing
    try:
        print("\nMaking 3 requests with round-robin load balancing:")
        for i in range(3):
            response = router.complete(
                messages=[UserMessage(content="What is 2+2?")],
                model="gpt-3.5-turbo",
                max_tokens=50
            )
            print(f"\n  Request {i+1}:")
            print(f"    Response: {response.content[:60]}...")
            print(f"    Tokens: {response.usage.total_tokens}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")


def tag_based_routing():
    """Demonstrate tag-based routing."""
    print("\n" + "=" * 60)
    print("Tag-Based Routing")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, showing configuration only")
        return
    
    # Create router with tagged models
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="fast-model",
                targets=[
                    ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key=api_key,
                        tpm=200000,
                        rpm=2000,
                        tags=["fast", "cheap", "general"]
                    ),
                ],
                strategy=RoutingStrategy.ROUND_ROBIN
            ),
            RouteConfig(
                alias="smart-model",
                targets=[
                    ModelTarget(
                        model="gpt-4",
                        provider="openai",
                        api_key=api_key,
                        tpm=100000,
                        rpm=500,
                        tags=["smart", "expensive", "reasoning"]
                    ),
                ],
                strategy=RoutingStrategy.ROUND_ROBIN
            ),
        ]
    )
    
    try:
        # Use tag-based selection only
        print("\n--- Using tag-based selection (fast models) ---")
        response = router.complete(
            messages=[UserMessage(content="What is 5 + 7?")],
            tags=["fast", "cheap"],
            max_tokens=30
        )
        print(f"Response: {response.content}")
        
        # Use specific model with tag validation
        print("\n--- Using model with tag validation ---")
        response = router.complete(
            messages=[UserMessage(content="Explain quantum physics")],
            model="smart-model",
            tags=["reasoning"],  # Ensures model has reasoning capability
            max_tokens=100
        )
        print(f"Response: {response.content[:150]}...")
        
        # This would fail - model doesn't have required tags
        print("\n--- This would fail (model lacks required tags) ---")
        try:
            response = router.complete(
                messages=[UserMessage(content="Hello")],
                model="fast-model",
                tags=["expensive"]  # fast-model doesn't have "expensive" tag
            )
        except ValueError as e:
            print(f"Expected error: {e}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")


def multi_model_router():
    """Router with multiple model aliases."""
    print("\n" + "=" * 60)
    print("Multi-Model Router - Different Aliases")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, showing configuration only")
        return
    
    router = ModelRouter(
        routes=[
            # Fast models route
            RouteConfig(
                alias="fast",
                targets=[
                    ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key=api_key,
                        tpm=200000,
                        rpm=2000
                    ),
                ],
                strategy=RoutingStrategy.ROUND_ROBIN
            ),
            # Smart models route
            RouteConfig(
                alias="smart",
                targets=[
                    ModelTarget(
                        model="gpt-4",
                        provider="openai",
                        api_key=api_key,
                        tpm=100000,
                        rpm=500
                    ),
                ],
                strategy=RoutingStrategy.ROUND_ROBIN
            ),
        ]
    )
    
    print(f"\nAvailable aliases: {router.list_aliases()}")
    
    try:
        # Use 'fast' alias for simple question
        print("\n--- Using 'fast' alias for simple math ---")
        response = router.complete(
            messages=[UserMessage(content="What is 5 + 7?")],
            model="fast",
            max_tokens=30
        )
        print(f"Response: {response.content}")
        
        # Use 'smart' alias for complex question
        print("\n--- Using 'smart' alias for complex reasoning ---")
        response = router.complete(
            messages=[UserMessage(content="Explain quantum entanglement in simple terms")],
            model="smart",
            max_tokens=100
        )
        print(f"Response: {response.content[:150]}...")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")


def routing_strategies():
    """Demonstrate different routing strategies."""
    print("\n" + "=" * 60)
    print("Routing Strategies")
    print("=" * 60)
    
    strategies = [
        (RoutingStrategy.ROUND_ROBIN, "Rotate through targets in order"),
        (RoutingStrategy.SIMPLE_SHUFFLE, "Random selection"),
        (RoutingStrategy.LEAST_BUSY, "Fewest active requests"),
        (RoutingStrategy.RATE_LIMIT_AWARE, "Most available capacity"),
        (RoutingStrategy.LATENCY_BASED, "Lowest average latency"),
        (RoutingStrategy.COST_BASED, "Lowest cost"),
        (RoutingStrategy.WEIGHTED, "Weighted random selection"),
        (RoutingStrategy.PRIORITY_BASED, "Highest success rate"),
    ]
    
    print("\nAvailable strategies:")
    for strategy, description in strategies:
        print(f"  • {strategy.value}: {description}")


def azure_multi_region():
    """Router for Azure multi-region deployments."""
    print("\n" + "=" * 60)
    print("Azure Multi-Region with Failover")
    print("=" * 60)
    
    if not (os.getenv("AZURE_OPENAI_API_KEY_EAST") and os.getenv("AZURE_OPENAI_API_KEY_WEST")):
        print("AZURE_OPENAI_API_KEY_EAST and AZURE_OPENAI_API_KEY_WEST not set, showing the configuration only")
        return

    print("""
This example shows how to configure multi-region Azure deployments
for automatic failover and load balancing.

Configuration:
""")
    
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="gpt-4",
                targets=[
                    ModelTarget(
                        model="gpt-4",
                        provider="azure",
                        api_key=os.getenv("AZURE_OPENAI_API_KEY_EAST"),
                        api_base="https://my-resource-east.openai.azure.com",
                        api_version="2024-02-15-preview",
                        region="us-east-1",
                        metadata={"priority": "primary"}
                    ),
                    ModelTarget(
                        model="gpt-4",
                        provider="azure",
                        api_key=os.getenv("AZURE_OPENAI_API_KEY_WEST"),
                        api_base="https://my-resource-west.openai.azure.com",
                        api_version="2024-02-15-preview",
                        region="us-west-2",
                        metadata={"priority": "secondary"}
                    ),
                ],
                strategy=RoutingStrategy.LEAST_BUSY
            )
        ]
    )
    
    print("\nAzure multi-region setup:")
    route = router.get_route("gpt-4")
    if route:
        for i, target in enumerate(route.targets, 1):
            priority = target.metadata.get("priority", "unknown")
            print(f"  {i}. {target.model} in {target.region} ({priority})")
        print(f"\nStrategy: {route.strategy.value}")
    
    print("\nBenefits:")
    print("  - Automatic failover if primary region is down")
    print("  - Load balancing based on latency")
    print("  - Geographic redundancy")


def bedrock_multi_region():
    """Router for Bedrock multi-region deployments."""
    print("\n" + "=" * 60)
    print("Bedrock Multi-Region")
    print("=" * 60)
    
    has_aws = os.getenv("AWS_PROFILE") or os.getenv("AWS_ACCESS_KEY_ID")
    
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="claude",
                targets=[
                    ModelTarget(
                        model="anthropic.claude-3-sonnet-20240229-v1:0",
                        provider="bedrock",
                        region="us-east-1",
                        metadata={"location": "Virginia"}
                    ),
                    ModelTarget(
                        model="anthropic.claude-3-sonnet-20240229-v1:0",
                        provider="bedrock",
                        region="us-west-2",
                        metadata={"location": "Oregon"}
                    ),
                ],
                strategy=RoutingStrategy.ROUND_ROBIN
            )
        ]
    )
    
    print("\nBedrock multi-region setup:")
    route = router.get_route("claude")
    if route:
        for i, target in enumerate(route.targets, 1):
            location = target.metadata.get("location", "unknown")
            print(f"  {i}. {target.model}")
            print(f"     Region: {target.region} ({location})")
    
    if not has_aws:
        print("\n⚠️  AWS credentials not configured, skipping actual call")
        return
    
    try:
        print("\n--- Making request with router ---")
        response = router.complete(
            messages=[UserMessage(content="What is AWS Bedrock?")],
            model="claude",
            max_tokens=100
        )
        print(f"\nResponse: {response.content[:150]}...")
        print(f"Tokens: {response.usage.total_tokens}")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)[:100]}")


def main():
    """Run all examples."""
    print("\n" + "🔀 " * 20)
    print("SKYE - Basic Routing Examples")
    print("🔀 " * 20)
    
    try:
        basic_router_example()
        multi_model_router()
        tag_based_routing()
        routing_strategies()
        azure_multi_region()
        bedrock_multi_region()
        
        print("\n" + "=" * 60)
        print("✅ Examples completed!")
        print("=" * 60)
        print("\nKey takeaways:")
        print("  • Routers distribute requests across multiple targets")
        print("  • Different strategies optimize for different goals")
        print("  • Aliases provide semantic names for model groups")
        print("  • Tag-based routing enables flexible model selection")
        print("  • Multi-region setup enables geographic redundancy")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
