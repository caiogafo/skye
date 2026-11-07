"""Example: Using YAML Configuration for ModelRouter

This example demonstrates how to configure a ModelRouter using a YAML file
with environment variable substitution for API keys and other sensitive data.
"""

import os
import re
from pathlib import Path

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

    # No request is made here: the keys are placeholders. With real keys, `router.complete(messages=..., model="gpt-3.5-turbo")`
    # picks a target by strategy and falls back on failure.
    print("\nRouter health metrics:")
    for alias in router.list_aliases():
        for model_id in [mid for mid in router.models if mid.startswith(f"{alias}:")]:
            health = router.get_model_health(model_id)
            print(f"  {model_id}: success rate {health.success_rate:.1%}, total requests {health.total_requests}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
