"""Fallbacks, retry policies, health, usage and cooldown of a router.

A router balances several targets, falls back to other models when one fails, and tracks the health and the rate-limit usage of each
model. State can live in memory, or in an external store (Redis, DynamoDB) when the process does not survive between invocations.

Set OPENAI_API_KEY.
"""

import os

from skye.router import RoutingStrategy
from skye import UserMessage
from skye.router import FallbackConfig, ModelRouter, ModelTarget, RetryPolicyConfig, RouteConfig


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set, skipping")
        return

    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="gpt-4",
                targets=[ModelTarget(model="gpt-4", provider="openai", api_key=api_key, tpm=90000, rpm=60)],
                strategy=RoutingStrategy.ROUND_ROBIN,
            ),
            RouteConfig(
                alias="gpt-3.5-turbo",
                targets=[ModelTarget(model="gpt-3.5-turbo", provider="openai", api_key=api_key)],
            ),
        ],
        fallbacks=[FallbackConfig(primary="gpt-4", fallbacks=["gpt-3.5-turbo"])],
        retry_policies=[
            RetryPolicyConfig(error_type="RateLimitError", max_retries=3),
            RetryPolicyConfig(error_type="TimeoutError", max_retries=2),
        ],
    )

    response = router.complete(messages=[UserMessage(content="Hello!")], model="gpt-4")
    print(response.content)

    for alias in router.list_aliases():
        route = router.get_route(alias)
        for target in route.targets:
            model_id = f"{alias}:{target.provider}:{target.model}"
            health = router.get_model_health(model_id)
            stats = router.get_usage_stats(model_id)
            print(f"{model_id}: success {health.success_rate:.0%}, rpm {stats.rpm_used}/{stats.rpm_limit}")

    print("in cooldown:", [info.model_id for info in router.get_cooldown_models()])


if __name__ == "__main__":
    main()
