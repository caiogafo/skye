"""The DecisionModel Port (proposed-interface, guarded).

This example shows the call shape of the ``DecisionModel`` Port. No concrete decision
model ships in ``src`` yet, so the script defines a tiny local implementation of the
Port to demonstrate the intended usage rather than invoking a real model.

A ``DecisionModel`` picks one option out of a finite, non-empty set and returns a
``DecisionResult`` with the chosen option plus a probability for every option; the
probabilities are each in ``[0.0, 1.0]`` and sum to ``1.0``. An empty option set is
rejected with a Skye error.
"""

import asyncio
from collections.abc import Sequence

from skye import ValidationError
from skye.interfaces import DecisionModel, DecisionResult


class FirstOptionDecider:
    """A minimal DecisionModel that favours the first option.

    This stands in for a real decision model to illustrate the Port's call shape.
    """

    async def decide(self, prompt: str, options: Sequence[str]) -> DecisionResult:
        """Pick the first option and spread the remaining mass evenly.

        Args:
            prompt: The question the decision is made against.
            options: The finite, non-empty set of allowed options.

        Returns:
            A DecisionResult whose probabilities sum to 1.0.

        Raises:
            ValidationError: If ``options`` is empty.
        """
        if not options:
            raise ValidationError(
                "at least one option is required", field="options", value=list(options)
            )

        lead = 0.7 if len(options) > 1 else 1.0
        rest = (1.0 - lead) / (len(options) - 1) if len(options) > 1 else 0.0
        probabilities = {option: (lead if i == 0 else rest) for i, option in enumerate(options)}
        return DecisionResult(choice=options[0], probabilities=probabilities)


async def main() -> None:
    decider = FirstOptionDecider()

    # The local implementation satisfies the runtime-checkable Port.
    print(f"FirstOptionDecider is a DecisionModel: {isinstance(decider, DecisionModel)}")

    options = ["route-to-cheap", "route-to-strong", "refuse"]
    result = await decider.decide("Which route fits this request?", options)
    print("\nDecision:")
    print(f"  choice       : {result.choice}")
    print(f"  probabilities: {result.probabilities}")
    print(f"  sum          : {round(sum(result.probabilities.values()), 6)}")

    # An empty option set is rejected; this error is provoked on purpose.
    try:
        await decider.decide("no options", [])
    except ValidationError as error:
        print(f"\nExpected rejection of empty options -> {error.message}")


if __name__ == "__main__":
    asyncio.run(main())
