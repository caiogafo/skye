"""The value of Skye in one example: one prompt, several providers, and a fallback when one fails.

The same ``messages`` go to a router that knows the models by one alias. The first entry is the primary, the others are its fallbacks.
With both OPENAI_API_KEY and ANTHROPIC_API_KEY set the entries are real models. Without them a scripted run shows the same thing: the
primary is down, so the answer comes from the fallback.
"""

import os
import sys
from pathlib import Path

from skye import UserMessage
from skye.router import ModelRouter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import KEYS, register_demo_providers  # noqa: E402

MODELS = {"openai": "gpt-4o-mini", "anthropic": "claude-3-5-haiku-latest"}


def main() -> None:
    entries = [f"{name}/{model}" for name, model in MODELS.items() if os.getenv(KEYS[name])]
    if len(entries) < 2:
        print("mode: scripted (set OPENAI_API_KEY and ANTHROPIC_API_KEY to call real models)")
        register_demo_providers()
        entries = ["flaky/primary", "scripted/backup"]  # the primary is down on purpose
    else:
        print("mode: real,", ", ".join(entries))

    router = ModelRouter({"answer": entries})  # first entry is the primary, the rest are fallbacks
    response = router.complete(messages=[UserMessage(content="What is the capital of France?")], model="answer")
    print(f"answered by {response.provider}: {response.content}")
    print("fallback chain:", router.fallbacks["answer"])


if __name__ == "__main__":
    main()
