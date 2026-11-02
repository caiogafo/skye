"""DecisionModel Port: choose one option from a finite set, with probabilities.

A call supplies a finite, non-empty set of allowed options. The response carries
one choice that belongs to that set and a probability for every allowed option;
each probability is in [0.0, 1.0] and they sum to 1.0. An empty option set must be
rejected with a Skye error (at least one option is required) and no choice returned.
Implemented by the ``models`` Component (decision models); consumed by gateway,
router and guard. Standard library only.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class DecisionResult:
    """Outcome of a decision: the chosen option and one probability per option."""

    choice: str
    probabilities: Mapping[str, float] = field(default_factory=dict)


@runtime_checkable
class DecisionModel(Protocol):
    """Port for a model that selects one option out of a finite set."""

    async def decide(self, prompt: str, options: Sequence[str]) -> DecisionResult:
        """Pick one of ``options`` for ``prompt``.

        Raises a Skye error if ``options`` is empty.
        """
        ...


__all__ = ["DecisionModel", "DecisionResult"]
