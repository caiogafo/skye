"""Example: Using YAML Configuration for ModelRouter

This example demonstrates how to configure a ModelRouter using a YAML file
with environment variable substitution for API keys and other sensitive data.
"""

import os
import re
from pathlib import Path

from skye.base.messages import UserMessage
from skye.router import ModelRouter

# In production the variables referenced as ${VAR} in the YAML are set externally. Here every one that is not set gets a placeholder,
# so the example can load the file and show the routing without real keys.
for _name in re.findall(r"\$\{(\w+)\}", (Path(__file__).parent / "router_config.yaml").read_text(encoding="utf-8")):
    os.environ.setdefault(_name, "your-api-key-here")


async def main():
    """Demonstrate YAML-based router configuration (the router is also used asynchronously)."""

    # Method 1: Load router from YAML file
    print("Loading router from YAML configuration...")
    config_path = Path(__file__).parent / "router_config.yaml"
    router = ModelRouter.from_yaml(config_path)

    print(f"Router loaded with {len(router.list_aliases())} aliases:")
    for alias in router.list_aliases():
        print(f"  - {alias}")

    # Method 2: Load with overrides
    print("\nLoading router with custom overrides...")
    router_custom = ModelRouter.from_yaml(
        config_path,
        cooldown_seconds=120.0,  # Override cooldown duration
        strategy="least_busy",  # Override default strategy
    )

    print(f"Custom router strategy: {router_custom.strategy.value}")
    print(f"Custom cooldown: {router_custom.cooldown_seconds}s")

    # Use the router to make a request
    print("\nMaking a completion request...")

    try:
        # The router will automatically select the best target based on strategy
        response = router.complete(
            messages=[UserMessage(content="Hello, how are you?")],
            model="gpt-3.5-turbo",  # Use the alias defined in YAML
            max_tokens=50
        )
        print(f"Response: {response.content}")

        # Example with async
        print("\nMaking async request...")
        response = await router.acomplete(
            messages=[UserMessage(content="What is Python?")],
            model="gpt-3.5-turbo",
            max_tokens=30
        )
        print(f"Async response: {response.content}")

        # Check router health metrics
        print("\nRouter health metrics:")
        for alias in router.list_aliases():
            # Get model IDs for this alias
            model_ids = [
                mid for mid in router.models.keys() if mid.startswith(f"{alias}:")
            ]
            for model_id in model_ids:
                health = router.get_model_health(model_id)
                print(f"  {model_id}:")
                print(f"    Success rate: {health.success_rate:.1%}")
                print(f"    Total requests: {health.total_requests}")
                print(f"    Active requests: {health.active_requests}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
