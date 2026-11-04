"""Authorizer: implement the policy Port and decide permit or forbid (Live, Port-level).

The ``policy`` component is minimal, but the
``AuthorizerInterface`` Port and its ``Decision`` outcome are real
(``skye.base.interfaces.authorizer``). A user implements the Port; this example
defines a tiny rule set and shows one permit and one forbid, no client needed.
"""

from skye.interfaces import AuthorizerInterface, Decision


class RuleSetAuthorizer(AuthorizerInterface):
    """Authorize against an explicit allow set of (principal, action, resource)."""

    def __init__(self, allowed: set[tuple[str, str, str]]) -> None:
        self._allowed = allowed

    def authorize(self, principal: str, action: str, resource: str) -> Decision:
        """Return ``Decision.PERMIT`` if the triple is allowed, else ``Decision.FORBID``."""
        if (principal, action, resource) in self._allowed:
            return Decision.PERMIT
        return Decision.FORBID


def main() -> None:
    authorizer = RuleSetAuthorizer(
        allowed={
            ("alice", "read", "report"),
            ("alice", "write", "report"),
        }
    )

    permit = authorizer.authorize("alice", "read", "report")
    print(f"alice read report  -> {permit.value}")

    forbid = authorizer.authorize("bob", "write", "report")
    print(f"bob write report   -> {forbid.value}")


if __name__ == "__main__":
    main()
