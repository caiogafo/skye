"""The token cache, the bearer authenticator built on it, and the 401 retry helper."""

import pytest

from skye.auth.cache import CachedBearerAuth, TokenCache
from skye.auth.refresh import send_with_refresh
from skye.base.exceptions import ProviderError
from skye.base.interfaces.authentication import AuthenticationInterface


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_cache_returns_the_token_until_the_margin_then_fetches_again():
    clock, calls = Clock(), []

    def fetch():
        calls.append(1)
        return f"t{len(calls)}", 100.0

    cache = TokenCache(margin=10, clock=clock)
    assert cache.get("k", fetch) == "t1" and cache.get("k", fetch) == "t1"
    clock.now = 89.9
    assert cache.get("k", fetch) == "t1"
    clock.now = 90.1  # within the 10 s margin of the deadline (100)
    assert cache.get("k", fetch) == "t2" and len(calls) == 2


def test_cache_keys_are_independent_and_invalidate_forgets():
    cache = TokenCache(clock=Clock())
    assert cache.get("a", lambda: ("A", 1000)) == "A"
    assert cache.get("b", lambda: ("B", 1000)) == "B"
    cache.invalidate("a")
    assert cache.get("a", lambda: ("A2", 1000)) == "A2" and cache.get("b", lambda: ("x", 1)) == "B"
    cache.invalidate()
    assert cache.get("b", lambda: ("B2", 1000)) == "B2"


def test_cache_starts_no_thread():
    import threading

    before = threading.active_count()
    TokenCache().get("k", lambda: ("t", 1))
    assert threading.active_count() == before


def test_bearer_auth_is_a_port_never_mutates_and_hides_the_token():
    auth = CachedBearerAuth("k", lambda: ("secret-token", 100))
    assert isinstance(auth, AuthenticationInterface)
    headers = {"A": "b"}
    assert auth.apply("GET", "https://x", headers) == {
        "A": "b",
        "Authorization": "Bearer secret-token",
    }
    assert headers == {"A": "b"}
    assert "secret-token" not in repr(auth)


def test_bearer_auth_with_another_header_and_no_scheme():
    auth = CachedBearerAuth("k", lambda: ("v", 100), header="api-key", scheme="")
    assert auth.apply("GET", "u", {}) == {"api-key": "v"}


class Tokens:
    def __init__(self):
        self.n = 0

    def fetch(self):
        self.n += 1
        return f"token{self.n}", 1000.0


def _failing(status_codes):
    codes = iter(status_codes)

    def send(headers):
        code = next(codes)
        if code != 200:
            raise ProviderError(f"HTTP {code}", provider="x", status_code=code)
        return headers["Authorization"]

    return send


def test_a_401_refreshes_once_and_retries_once():
    tokens = Tokens()
    auth = CachedBearerAuth("k", tokens.fetch)
    assert send_with_refresh(_failing([401, 200]), auth, "GET", "u") == "Bearer token2"
    assert tokens.n == 2


def test_a_second_401_surfaces_the_error():
    tokens = Tokens()
    with pytest.raises(ProviderError) as caught:
        send_with_refresh(_failing([401, 401]), CachedBearerAuth("k", tokens.fetch), "GET", "u")
    assert caught.value.details["status_code"] == 401 and tokens.n == 2


def test_other_errors_and_authenticators_without_refresh_raise_at_once():
    tokens = Tokens()
    with pytest.raises(ProviderError):
        send_with_refresh(_failing([500, 200]), CachedBearerAuth("k", tokens.fetch), "GET", "u")
    assert tokens.n == 1

    class Plain:
        def apply(self, method, url, headers, body=b""):
            return {**headers}

    sends = []

    def send(headers):
        sends.append(1)
        raise ProviderError("HTTP 401", provider="x", status_code=401)

    with pytest.raises(ProviderError):
        send_with_refresh(send, Plain(), "GET", "u")
    assert len(sends) == 1
