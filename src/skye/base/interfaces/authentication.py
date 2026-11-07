"""Authentication Port: apply authentication to an outgoing request.

An authenticator adds headers to a request or signs it (API key, bearer token, SigV4,
OAuth2 and so on). The contract lives in ``base``; the implementations, which perform I/O
and may need third-party libraries, live in the ``auth`` Component. Standard library only,
no I/O here.

Raises: ProviderError or ConfigurationError when a credential cannot be obtained or refreshed; never returns a request without the credential it promises.
Missing: not applicable (the method returns the headers to add); an unsupported method name is an error, not an empty dict.
Concurrency: an authenticator may be shared by threads and tasks; one that caches a token must guard the refresh with a lock.
"""

from collections.abc import Mapping
from typing import Protocol, runtime_checkable


@runtime_checkable
class AuthenticationInterface(Protocol):
    """Port for an object that authenticates one request."""

    def apply(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes = b"",
    ) -> dict[str, str]:
        """Return the request headers with authentication added (or the request signed).

        The input ``headers`` mapping is not modified; a new dict is returned.
        """
        ...


__all__ = ["AuthenticationInterface"]
