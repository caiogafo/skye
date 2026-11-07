"""Routing: one alias, one or several models, round-robin balancing.

Start with the shorthand: ``ModelRouter({"alias": ["provider/model", ...]})``. The first entry is the primary and the others are its
fallbacks; the API key is read from the provider's standard variable. The full form (``RouteConfig``, ``ModelTarget``, a strategy, tags,
limits) builds the same objects and gives control of each target. With OPENAI_API_KEY set the targets are OpenAI models; without a key
they are a scripted provider, and the example says which.
"""

import os
import sys
from pathlib import Path

from skye import UserMessage
from skye.router import ModelRouter, ModelTarget, RouteConfig, RoutingStrategy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import router_provider  # noqa: E402


def ask(router: ModelRouter, alias: str) -> None:
    response = router.complete(messages=[UserMessage(content="What is 2+2?")], model=alias, max_tokens=50)
    print(f"  {alias}: {response.content[:50]} ({response.usage.total_tokens} tokens)")


def main() -> None:
    provider = router_provider("openai")
    print("mode:", "openai (real)" if os.getenv("OPENAI_API_KEY") else "scripted (set OPENAI_API_KEY to call openai)")

    # The shorthand
    router = ModelRouter({"fast": [f"{provider}/gpt-4o-mini"]})
    print("aliases:", router.list_aliases())
    ask(router, "fast")

    # The full form: two targets for one alias, balanced round-robin, with limits and tags
    api_key = os.getenv("OPENAI_API_KEY")
    targets = [
        ModelTarget(model="gpt-4o-mini", provider=provider, api_key=api_key, tpm=200000, rpm=2000, tags=[name])
        for name in ("primary", "secondary")
    ]
    router = ModelRouter(routes=[RouteConfig(alias="balanced", targets=targets, strategy=RoutingStrategy.ROUND_ROBIN)])
    for number in range(3):
        print(f"request {number + 1}")
        ask(router, "balanced")
    print("targets:", [(t.provider, t.model, t.tags) for t in router.get_route("balanced").targets])


if __name__ == "__main__":
    main()
