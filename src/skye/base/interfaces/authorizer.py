"""Authorizer Port: may this principal perform this action on this resource?

A call carries three identifiers (principal, action, resource) and returns a decision
that is exactly one of ``permit`` or ``forbid``. Implemented by the ``policy`` Component;
consumed by the runtime (for example the gateway) through injection or hooks, never by
importing ``policy``. Standard library only, no I/O.

Raises: never raises for a denial: a denial is the value ``forbid``; raises only on a malformed identifier.
Missing: an unknown principal, action or resource is ``forbid`` (default deny), never an exception.
Concurrency: ``authorize`` is a pure read; safe to call from many threads and tasks.
"""

from enum import Enum
from typing import Protocol, runtime_checkable


class Decision(str, Enum):
    """Outcome of an authorization check: exactly one of permit or forbid."""

    PERMIT = "permit"
    FORBID = "forbid"


@runtime_checkable
class AuthorizerInterface(Protocol):
    """Port for deciding whether a principal may act on a resource."""

    def authorize(self, principal: str, action: str, resource: str) -> Decision:
        """Return ``Decision.PERMIT`` or ``Decision.FORBID`` for the given identifiers."""
        ...


__all__ = ["AuthorizerInterface", "Decision"]
