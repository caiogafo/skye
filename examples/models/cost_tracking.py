"""Estimating request cost with CostCalculator (Live).

It makes one completion, then turns the response's ``TokenUsage`` into a dollar
estimate with ``CostCalculator``.

``CostCalculator`` ships pricing for the common models (per one million tokens),
supports custom pricing for fine-tuned or private models, and returns ``0.0`` for a
model it does not know.

With OPENAI_API_KEY set the completion is real; without a key a scripted client answers (its usage is a fixed number).
"""

from skye import UserMessage
from skye.models import CostCalculator

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402


def main() -> None:
    client = get_client("openai")

    model = "gpt-4"
    response = client.complete(
        messages=[UserMessage(content="What is the capital of France?")],
        model=model,
    )

    usage = response.usage
    print("Token usage for the request:")
    print(f"  prompt    : {usage.prompt_tokens}")
    print(f"  completion: {usage.completion_tokens}")
    print(f"  total     : {usage.total_tokens}")

    pricing = CostCalculator.get_pricing(model)
    print(f"\nPricing for {model} (USD per 1M tokens): {pricing}")

    cost = CostCalculator.calculate_cost(model, usage)
    print(f"Estimated cost for this request: ${cost:.6f}")

    # Register pricing for a private or fine-tuned model, then price the same usage.
    CostCalculator.add_custom_pricing("my-finetuned-model", prompt_price=5.0, completion_price=10.0)
    custom_cost = CostCalculator.calculate_cost("my-finetuned-model", usage)
    print(f"Estimated cost on my-finetuned-model: ${custom_cost:.6f}")


if __name__ == "__main__":
    main()
