"""Skye as an MCP server: the intended gateway shape (proposed-interface, guarded).

Built from real parts. This example targets the planned ``gateway`` API
(R44-48) that would expose Skye capabilities over MCP with an authorizer checked
on every list and every call. That server entry point does not exist in ``src``
yet, so this example shows the intended shape from real parts only — a
``CapabilityRegistry`` of ``@capability`` functions plus a user
``AuthorizerInterface`` consulted before each operation — and then guard-returns
before any not-yet-existing gateway call. No fake server API is invented.
"""

from skye.base.interfaces.authorizer import AuthorizerInterface, Decision
from skye.tools import CapabilityRegistry, capability


@capability
def get_time(timezone: str = "UTC") -> str:
    """Return the current time label for a timezone."""
    return f"12:00 {timezone}"


@capability
def echo(text: str) -> str:
    """Echo the given text back."""
    return text


class ClientAuthorizer(AuthorizerInterface):
    """Authorize an MCP client against an explicit allow set."""

    def __init__(self, allowed: set[tuple[str, str, str]]) -> None:
        self._allowed = allowed

    def authorize(self, principal: str, action: str, resource: str) -> Decision:
        """Permit a known (principal, action, resource) triple, forbid otherwise."""
        if (principal, action, resource) in self._allowed:
            return Decision.PERMIT
        return Decision.FORBID


def main() -> None:
    registry = CapabilityRegistry(capabilities=[get_time, echo], auto_search=False)
    authorizer = ClientAuthorizer(
        allowed={
            ("client-a", "list", "*"),
            ("client-a", "call", "get_time"),
        }
    )
    principal = "client-a"

    # Intended "list" operation: authorize, then expose the capability names.
    if authorizer.authorize(principal, "list", "*") is Decision.PERMIT:
        print(f"list permitted for {principal}: {registry.list_all()}")
    else:
        print(f"list forbidden for {principal}")

    # Intended "call" operation, authorized per capability.
    call_arguments: dict[str, dict[str, str]] = {
        "get_time": {"timezone": "UTC"},
        "echo": {"text": "hello"},
    }
    for name in registry.list_all():
        decision = authorizer.authorize(principal, "call", name)
        if decision is Decision.PERMIT:
            message = registry.execute(name, call_arguments.get(name, {}))
            print(f"call permitted {name}: {message.content}")
        else:
            print(f"call forbidden {name}")

    # The gateway server entry point (serve Skye over MCP) is not in src yet.
    print("gateway server API not available yet, skipping serve step")
    return


if __name__ == "__main__":
    main()
