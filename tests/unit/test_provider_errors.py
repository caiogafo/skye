"""Provider errors chosen by the response (D104); errors never log themselves (D105)."""

from __future__ import annotations

import email.message
import io
import logging
import socket
import urllib.error
from unittest.mock import patch

import pytest

import skye
import skye.exceptions
from skye.base import http
from skye.base.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConfigurationError,
    ContentPolicyError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
    ServerError,
    SkyeError,
    ValidationError,
)

NEW = [
    RateLimitError,
    ServerError,
    ProviderTimeoutError,
    AuthenticationError,
    BadRequestError,
    ContentPolicyError,
]


def _http_error(
    code: int, body: str = "", headers: dict[str, str] | None = None
) -> urllib.error.HTTPError:
    msg = email.message.Message()
    for key, value in (headers or {}).items():
        msg[key] = value
    return urllib.error.HTTPError(
        "https://api.example", code, "reason", msg, io.BytesIO(body.encode())
    )


def _raised(exc: BaseException) -> ProviderError:
    with patch("urllib.request.urlopen", side_effect=exc):
        with pytest.raises(ProviderError) as info:
            http.request_json("https://api.example", {"a": 1}, provider="openai")
    return info.value


@pytest.mark.parametrize("cls", NEW)
def test_every_new_error_is_a_provider_error_and_keeps_its_context(
    cls: type[ProviderError],
) -> None:
    err = cls("boom", provider="openai", status_code=400, retry_after=1.5)
    assert isinstance(err, ProviderError)
    assert err.provider == "openai"
    assert err.status_code == 400
    assert err.retry_after == 1.5
    assert err.details["provider"] == "openai"


def test_content_policy_is_a_bad_request() -> None:
    assert issubclass(ContentPolicyError, BadRequestError)


def test_provider_error_defaults() -> None:
    err = ProviderError("boom", provider="x")
    assert err.status_code is None and err.retry_after is None and err.provider == "x"
    assert str(err) == "boom | Details: {'provider': 'x', 'status_code': None}"


@pytest.mark.parametrize(
    ("code", "cls"),
    [
        (429, RateLimitError),
        (500, ServerError),
        (503, ServerError),
        (401, AuthenticationError),
        (403, AuthenticationError),
        (400, BadRequestError),
        (404, BadRequestError),
        (422, BadRequestError),
    ],
)
def test_http_status_picks_the_subclass(code: int, cls: type[ProviderError]) -> None:
    err = _raised(_http_error(code, '{"error": "x"}'))
    assert type(err) is cls
    assert err.status_code == code
    assert err.provider == "openai"
    assert isinstance(err.__cause__, urllib.error.HTTPError)


@pytest.mark.parametrize(
    "body",
    [
        '{"error": {"code": "content_policy_violation", "message": "no"}}',
        '{"error": {"code": "content_filter"}}',
        "The response was filtered due to the prompt triggering the content management policy.",
    ],
)
def test_a_content_policy_refusal_is_a_content_policy_error(body: str) -> None:
    err = _raised(_http_error(400, body))
    assert type(err) is ContentPolicyError
    assert err.status_code == 400


def test_a_plain_bad_request_is_not_a_content_policy_error() -> None:
    assert type(_raised(_http_error(400, '{"error": "max_tokens too large"}'))) is BadRequestError


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"Retry-After": "7"}, 7.0),
        ({"Retry-After": "2.5"}, 2.5),
        ({"retry-after-ms": "1500"}, 1.5),
        ({"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}, 0.0),  # a date in the past: retry now
        ({"Retry-After": "soon"}, None),
        ({}, None),
    ],
)
def test_retry_after_is_parsed_into_seconds(
    headers: dict[str, str], expected: float | None
) -> None:
    err = _raised(_http_error(429, "", headers))
    assert type(err) is RateLimitError
    assert err.retry_after == expected


def test_retry_after_as_a_future_date() -> None:
    import datetime as dt
    from email.utils import format_datetime

    later = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=120)
    err = _raised(_http_error(503, "", {"Retry-After": format_datetime(later, usegmt=True)}))
    assert type(err) is ServerError
    assert err.retry_after is not None and 100 < err.retry_after <= 120


@pytest.mark.parametrize(
    "exc",
    [
        TimeoutError("timed out"),
        TimeoutError("timed out"),
        urllib.error.URLError(TimeoutError("timed out")),
        urllib.error.URLError(TimeoutError()),
        ConnectionResetError("reset by peer"),
        urllib.error.URLError(ConnectionResetError("reset")),
        ConnectionAbortedError(),
        BrokenPipeError(),
    ],
)
def test_timeouts_and_dropped_connections_are_provider_timeout_errors(exc: BaseException) -> None:
    err = _raised(exc)
    assert type(err) is ProviderTimeoutError
    assert err.status_code is None
    assert err.provider == "openai"


def test_other_transport_failures_stay_plain_provider_errors() -> None:
    err = _raised(urllib.error.URLError(socket.gaierror("name not known")))
    assert type(err) is ProviderError


@pytest.mark.parametrize("helper", ["send_bytes", "open_stream", "stream_lines", "request"])
def test_every_helper_raises_the_subclass(helper: str) -> None:
    with patch("urllib.request.urlopen", side_effect=_http_error(429, "", {"Retry-After": "3"})):
        with pytest.raises(RateLimitError) as info:
            result = getattr(http, helper)("https://api.example", provider="p")
            if helper == "stream_lines":
                list(result)
    assert info.value.retry_after == 3.0


def test_existing_except_provider_error_still_catches() -> None:
    try:
        raise RateLimitError("slow down", provider="x", status_code=429)
    except ProviderError as e:
        assert e.status_code == 429


@pytest.mark.parametrize("cls", NEW)
def test_new_errors_are_public(cls: type[ProviderError]) -> None:
    name = cls.__name__
    assert getattr(skye.exceptions, name) is cls
    assert name in skye.exceptions.__all__
    assert getattr(skye, name) is cls
    assert name in skye.__all__


@pytest.mark.parametrize(
    "make",
    [
        lambda: SkyeError("x"),
        lambda: ProviderError("x", provider="p", status_code=500),
        lambda: RateLimitError("x", provider="p", status_code=429),
        lambda: ConfigurationError("x", details={"a": 1}),
        lambda: ValidationError("x", field="f", value=1),
    ],
)
def test_creating_an_error_logs_nothing(make, caplog: pytest.LogCaptureFixture) -> None:  # type: ignore[no-untyped-def]
    """D105: an error never logs itself; the code that handles it logs it once."""
    with caplog.at_level(logging.DEBUG):
        make()
    assert caplog.records == []
