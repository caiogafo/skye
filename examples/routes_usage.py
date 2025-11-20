"""Complete example of using routes package with 'from nimbus import routes as rt'.

This example demonstrates all the ways to use the ModelRouter with constructor-based
configuration (no setters). All configuration is done upfront in the constructor.

Note: Set environment variables for API keys:
- OPENAI_API_KEY
- AZURE_API_KEY
- AZURE_API_BASE
- ANTHROPIC_API_KEY
"""

import os
import nimbus
from nimbus import routes as rt
from nimbus.completion import CompletionRequest
from nimbus.messages import UserMessage


def example_1_basic_routes():
    """Example 1: Basic route configuration with single targets."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Route Configuration")
    print("=" * 60)

    # Create routes using rt namespace
    router = rt.ModelRouter(
        routes=[
            rt.RouteConfig(
                alias="gpt-3.5-turbo",
                targets=[
                    rt.ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key=os.getenv("OPENAI_API_KEY"),
                        tpm=200000,
                        rpm=2000,
                        tags=["fast", "cheap"],
                    ),
                ],
            ),
            rt.RouteConfig(
                alias="gpt-4",
                targets=[
                    rt.ModelTarget(
                        model="gpt-4",
                        provider="openai",
                        api_key=os.getenv("OPENAI_API_KEY"),
                        tpm=100000,
                        rpm=500,
                        tags=["premium", "high-quality"],
                    ),
                ],
            ),
        ]
    )

    print(f"✓ Created router with {len(router.list_aliases())} aliases")
    print(f"  Aliases: {router.list_aliases()}")


def example_2_multi_target_routes():
    """Example 2: Routes with multiple targets for load balancing."""
    print("\n" + "=" * 60)
    print("Example 2: Multi-Target Routes (Load Balancing)")
    print("=" * 60)

    # Create routes with multiple targets per alias
    router = rt.ModelRouter(
        routes=[
            rt.RouteConfig(
                alias="gpt-3.5-turbo",
                targets=[
                    rt.ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key=os.getenv("OPENAI_API_KEY"),
                        tpm=200000,
                        rpm=2000,
                        tags=["openai"],
                        weight=1.0,
                    ),
                    rt.ModelTarget(
                        model="gpt-35-turbo",
                        provider="azure",
                        api_key=os.getenv("AZURE_API_KEY"),
                        api_base=os.getenv("AZURE_API_BASE"),
                        api_version="2024-02-15-preview",
                        tpm=100000,
                        rpm=1000,
                        tags=["azure"],
                        weight=0.8,
                    ),
                ],
                strategy=rt.RoutingStrategy.RATE_LIMIT_AWARE,
            )
        ]
    )

    route = router.get_route("gpt-3.5-turbo")
    if route:
        print(f"✓ Route 'gpt-3.5-turbo' has {len(route.targets)} targets")
        for i, target in enumerate(route.targets, 1):
            print(f"  {i}. {target.provider}: {target.model} (weight: {target.weight})")


def example_3_complete_setup():
    """Example 3: Complete router setup with all features."""
    print("\n" + "=" * 60)
    print("Example 3: Complete Router Setup (All Features)")
    print("=" * 60)

    # Create a complete router with all features configured in constructor
    router = rt.ModelRouter(
        routes=[
            rt.RouteConfig(
                alias="gpt-3.5-turbo",
                targets=[
                    rt.ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key=os.getenv("OPENAI_API_KEY"),
                        tpm=200000,
                        rpm=2000,
                        tags=["fast", "cheap"],
                        weight=1.0,
                    ),
                    rt.ModelTarget(
                        model="gpt-35-turbo",
                        provider="azure",
                        api_key=os.getenv("AZURE_API_KEY"),
                        api_base=os.getenv("AZURE_API_BASE"),
                        api_version="2024-02-15-preview",
                        tpm=100000,
                        rpm=1000,
                        tags=["fast", "cheap", "azure"],
                        weight=0.8,
                    ),
                ],
                strategy=rt.RoutingStrategy.RATE_LIMIT_AWARE,
                fallback_on_error=True,
            ),
            rt.RouteConfig(
                alias="gpt-4",
                targets=[
                    rt.ModelTarget(
                        model="gpt-4",
                        provider="openai",
                        api_key=os.getenv("OPENAI_API_KEY"),
                        tpm=100000,
                        rpm=500,
                        tags=["premium", "high-quality"],
                    ),
                ],
            ),
            rt.RouteConfig(
                alias="claude-3-sonnet",
                targets=[
                    rt.ModelTarget(
                        model="claude-3-sonnet-20240229",
                        provider="anthropic",
                        api_key=os.getenv("ANTHROPIC_API_KEY"),
                        tpm=150000,
                        rpm=1000,
                        tags=["premium", "high-quality"],
                    ),
                ],
            ),
        ],
        # Global routing strategy
        strategy=rt.RoutingStrategy.LEAST_BUSY,
        # Cooldown configuration
        cooldown_seconds=60.0,
        # Enable pre-call rate limit checks
        enable_pre_call_checks=True,
        # Fallback chains
        fallbacks=[
            rt.FallbackConfig(
                primary="gpt-4",
                fallbacks=["gpt-3.5-turbo", "claude-3-sonnet"],
            ),
            rt.FallbackConfig(
                primary="claude-3-sonnet",
                fallbacks=["gpt-3.5-turbo"],
            ),
        ],
        # Retry policies
        retry_policies=[
            rt.RetryPolicyConfig(error_type="RateLimitError", max_retries=3),
            rt.RetryPolicyConfig(error_type="TimeoutError", max_retries=2),
            rt.RetryPolicyConfig(error_type="ServerError", max_retries=2),
            rt.RetryPolicyConfig(error_type="AuthenticationError", max_retries=0),
        ],
        # Allowed fails before cooldown
        allowed_fails_policies=[
            rt.AllowedFailsPolicyConfig(
                error_type="RateLimitError",
                allowed_fails_per_minute=100,
            ),
            rt.AllowedFailsPolicyConfig(
                error_type="ServerError",
                allowed_fails_per_minute=5,
            ),
        ],
    )

    print("✓ Complete router setup:")
    print(f"  Aliases: {router.list_aliases()}")
    print(f"  Strategy: {router.strategy.value}")
    print(f"  Cooldown: {router.cooldown_seconds}s")
    print(f"  Pre-call checks: {router.pre_call_checks_enabled}")
    print(f"  Fallback chains: {len(router.fallbacks)}")
    print(f"  Retry policies: {len(router.retry_policy)}")
    print(f"  Allowed fails policies: {len(router.allowed_fails_policy)}")


def example_4_metrics_and_monitoring():
    """Example 4: Accessing router metrics and monitoring."""
    print("\n" + "=" * 60)
    print("Example 4: Metrics and Monitoring")
    print("=" * 60)

    # Create router
    router = rt.ModelRouter(
        routes=[
            rt.RouteConfig(
                alias="gpt-4",
                targets=[
                    rt.ModelTarget(
                        model="gpt-4",
                        provider="openai",
                        api_key=os.getenv("OPENAI_API_KEY"),
                        tpm=100000,
                        rpm=500,
                    ),
                ],
            ),
        ]
    )

    print("✓ Available metrics (returned as Pydantic models):")
    print("  - rt.ModelHealthMetrics: Health tracking")
    print("    - success_rate, average_latency_ms, failure_count, etc.")
    print("  - rt.UsageStats: Rate limit usage")
    print("    - tpm_used, rpm_used, active_requests, etc.")
    print("  - rt.CooldownInfo: Cooldown status")
    print("    - model_id, cooldown_until, reason")

    print("\nExample usage:")
    print("  health = router.get_model_health('gpt-4')")
    print("  print(f'Success rate: {health.success_rate:.1%}')")
    print("  print(f'Avg latency: {health.average_latency_ms:.0f}ms')")
    print("")
    print("  stats = router.get_usage_stats('gpt-4')")
    print("  print(f'TPM used: {stats.tpm_used}/{stats.tpm_limit}')")
    print("")
    print("  cooled_down = router.get_cooldown_models()")
    print("  for info in cooled_down:")
    print("      print(f'{info.model_id} cooled down until {info.cooldown_until}')")


def example_5_routing_strategies():
    """Example 5: Different routing strategies."""
    print("\n" + "=" * 60)
    print("Example 5: Routing Strategies")
    print("=" * 60)

    print("✓ Available strategies via rt.RoutingStrategy:")
    print("  - ROUND_ROBIN: Rotate through targets")
    print("  - SIMPLE_SHUFFLE: Random selection")
    print("  - LEAST_BUSY: Fewest active requests")
    print("  - RATE_LIMIT_AWARE: Most available capacity")
    print("  - LATENCY_BASED: Lowest average latency")
    print("  - COST_BASED: Lowest cost")
    print("  - WEIGHTED: Weighted random selection (by target weight)")
    print("  - PRIORITY_BASED: Highest success rate")

    print("\nExample - Create router with specific strategy:")
    print("  router = rt.ModelRouter(")
    print("      routes=[...],")
    print("      strategy=rt.RoutingStrategy.RATE_LIMIT_AWARE")
    print("  )")


def example_6_alias_management():
    """Example 6: Alias management and inspection."""
    print("\n" + "=" * 60)
    print("Example 6: Alias Management")
    print("=" * 60)

    router = rt.ModelRouter(
        routes=[
            rt.RouteConfig(
                alias="gpt-3.5-turbo",
                targets=[
                    rt.ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key=os.getenv("OPENAI_API_KEY"),
                    ),
                ],
            ),
            rt.RouteConfig(
                alias="gpt-4",
                targets=[
                    rt.ModelTarget(
                        model="gpt-4",
                        provider="openai",
                        api_key=os.getenv("OPENAI_API_KEY"),
                    ),
                ],
            ),
        ]
    )

    print("✓ Alias management methods:")
    print(f"  - is_alias('gpt-4'): {router.is_alias('gpt-4')}")
    print(f"  - list_aliases(): {router.list_aliases()}")

    route = router.get_route("gpt-3.5-turbo")
    if route:
        print(f"  - get_route('gpt-3.5-turbo'):")
        print(f"      - Targets: {len(route.targets)}")
        print(f"      - Strategy: {route.strategy.value}")
        print(f"      - Fallback on error: {route.fallback_on_error}")


def example_7_tag_based_routing():
    """Example 7: Tag-based routing."""
    print("\n" + "=" * 60)
    print("Example 7: Tag-Based Routing")
    print("=" * 60)

    router = rt.ModelRouter(
        routes=[
            rt.RouteConfig(
                alias="gpt-4",
                targets=[
                    rt.ModelTarget(
                        model="gpt-4",
                        provider="openai",
                        api_key=os.getenv("OPENAI_API_KEY"),
                        tags=["premium", "high-quality"],
                    ),
                ],
            ),
            rt.RouteConfig(
                alias="gpt-3.5-turbo",
                targets=[
                    rt.ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key=os.getenv("OPENAI_API_KEY"),
                        tags=["fast", "cheap"],
                    ),
                ],
            ),
        ]
    )

    print("✓ Tag-based routing:")
    print("  Tags are assigned to targets during configuration")
    print("  Example:")
    print("    rt.ModelTarget(")
    print("        model='gpt-4',")
    print("        provider='openai',")
    print("        tags=['premium', 'high-quality']")
    print("    )")
    print("")
    print("  Route to models with specific tags:")
    print("    response = router.route_with_tags(")
    print("        request,")
    print("        required_tags=['premium', 'high-quality']")
    print("    )")


def main():
    """Run all examples."""
    print("\n" + "🚀 " * 20)
    print("NIMBUS ROUTES PACKAGE - Complete Usage Guide")
    print("🚀 " * 20)

    print("\nUsage: from nimbus import routes as rt")
    print("\nKey Classes and Enums:")
    print("  - rt.ModelRouter: Main router class")
    print("  - rt.ModelTarget: Target configuration")
    print("  - rt.RouteConfig: Route configuration")
    print("  - rt.FallbackConfig: Fallback configuration")
    print("  - rt.RetryPolicyConfig: Retry policy configuration")
    print("  - rt.AllowedFailsPolicyConfig: Allowed fails configuration")
    print("  - rt.ModelHealthMetrics: Health metrics (Pydantic model)")
    print("  - rt.UsageStats: Usage statistics (Pydantic model)")
    print("  - rt.CooldownInfo: Cooldown information (Pydantic model)")
    print("  - rt.RoutingStrategy: Routing strategy enum")

    try:
        example_1_basic_routes()
        example_2_multi_target_routes()
        example_3_complete_setup()
        example_4_metrics_and_monitoring()
        example_5_routing_strategies()
        example_6_alias_management()
        example_7_tag_based_routing()

        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("  ✓ All configuration is done in the constructor")
        print("  ✓ No setters needed - everything is declarative")
        print("  ✓ Use 'from nimbus import routes as rt' for clean imports")
        print("  ✓ All metrics return Pydantic models for type safety")
        print("  ✓ Support for multiple providers (OpenAI, Azure, Anthropic)")
        print("  ✓ Comprehensive health tracking and rate limiting")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
