"""Your own authenticator behind the AuthenticationInterface Port (Live).

``AuthenticationInterface`` is a runtime-checkable Protocol in
``skye.base.interfaces.authentication``. Any object with a matching
``apply(method, url, headers, body=b"") -> dict[str, str]`` satisfies it, so you can plug a custom
token source in without subclassing anything.
"""

from collections.abc import Mapping

from skye.base.interfaces.authentication import AuthenticationInterface


class StaticTokenAuthenticator:
    """Add a fixed bearer token to every request.

    A real implementation might read the token from a secret store or mint it on demand; the
    contract is the same: return a new headers dict, leave the input mapping untouched.
    """

    def __init__(self, token: str) -> None:
        self._token = token

    def apply(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes = b"",
    ) -> dict[str, str]:
        """Return the headers with an ``Authorization`` bearer token added."""
        return {**headers, "Authorization": f"Bearer {self._token}"}


def main() -> None:
    authenticator = StaticTokenAuthenticator(token="demo-token")

    # The runtime-checkable Port recognises the duck-typed implementation.
    satisfies = isinstance(authenticator, AuthenticationInterface)
    print("Satisfies AuthenticationInterface:", satisfies)

    headers = authenticator.apply(
        "GET", "https://api.example.com/v1/models", {"Accept": "application/json"}
    )
    print("Resulting header names:", sorted(headers))


if __name__ == "__main__":
    main()
