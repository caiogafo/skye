"""Fallbacks, retry policies, health, usage and cooldown of a router.

A router balances targets, falls back when one fails, retries per error class of ``skye.exceptions`` (waiting 1 s, 2 s, 4 s here) and
tracks health and usage. State lives in memory, or in a store passed as ``storage=`` when the process does not survive between calls.

With OPENAI_API_KEY set the targets are OpenAI models; without a key they are a scripted provider, and the example says which.
"""

import os
import sys
from pathlib import Path

from skye import UserMessage
from skye.router import FallbackConfig, ModelRouter, ModelTarget, RetryPolicyConfig, RouteConfig, RoutingStrategy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import router_provider  # noqa: E402


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    provider = router_provider("openai")
    print("mode:", "openai (real)" if api_key else "scripted (set OPENAI_API_KEY to call openai)")

    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="gpt-4",
                targets=[ModelTarget(model="gpt-4", provider=provider, api_key=api_key, tpm=90000, rpm=60)],
                strategy=RoutingStrategy.ROUND_ROBIN,
            ),
            RouteConfig(
                alias="gpt-3.5-turbo",
                targets=[ModelTarget(model="gpt-3.5-turbo", provider=provider, api_key=api_key)],
            ),
        ],
        fallbacks=[FallbackConfig(primary="gpt-4", fallbacks=["gpt-3.5-turbo"])],
        retry_policies=[
            RetryPolicyConfig(error_type="RateLimitError", max_retries=3, retry_after_seconds=1.0, exponential_backoff=True),
            RetryPolicyConfig(error_type="ProviderTimeoutError", max_retries=2),
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
