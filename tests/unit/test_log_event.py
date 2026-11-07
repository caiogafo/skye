"""Tests for the structured log event of a model invocation (Requirement 18.3)."""

import logging

import pytest

from skye.base.completion import CompleteRequest, CompleteResponse, TokenUsage
from skye.base.exceptions import ValidationError
from skye.base.interfaces.observer import EventType
from skye.base.log_event import (
    ModelInvocationEvent,
    model_invocation_end,
    model_invocation_error,
    model_invocation_start,
    new_correlation_id,
)
from skye.base.messages import UserMessage


def _request():
    return CompleteRequest(
        messages=[UserMessage(content="secret text")], model="gpt-4", max_tokens=10
    )


def _response():
    return CompleteResponse(
        model="gpt-4",
        provider="openai",
        content="ok",
        finish_reason="stop",
        usage=TokenUsage(prompt_tokens=3, completion_tokens=2, total_tokens=5),
    )


def test_one_correlation_id_ties_start_end_and_error_together():
    start = model_invocation_start(_request(), provider="openai")
    end = model_invocation_end(_response(), correlation_id=start.correlation_id, latency_ms=12.5)
    failed = model_invocation_error(
        RuntimeError("boom"), model="gpt-4", provider="openai", correlation_id=start.correlation_id
    )
    assert start.correlation_id == end.correlation_id == failed.correlation_id
    assert [e.event_type for e in (start, end, failed)] == [
        EventType.MODEL_INVOKE_START,
        EventType.MODEL_INVOKE_END,
        EventType.MODEL_INVOKE_ERROR,
    ]


def test_events_carry_request_and_response_details_but_not_the_message_text():
    start = model_invocation_start(_request(), provider="openai")
    assert start.request["messages"] == 1 and start.request["max_tokens"] == 10
    assert "secret text" not in str(start.to_dict())
    end = model_invocation_end(_response(), correlation_id="c", latency_ms=1.0)
    assert end.response["total_tokens"] == 5 and end.response["finish_reason"] == "stop"
    failed = model_invocation_error(
        RuntimeError("boom"), model="m", provider="p", correlation_id="c"
    )
    assert failed.error == "RuntimeError: boom"


def test_a_given_correlation_id_is_reused_and_new_ones_are_unique():
    assert (
        model_invocation_start(_request(), provider="p", correlation_id="abc").correlation_id
        == "abc"
    )
    assert new_correlation_id() != new_correlation_id()


def test_log_extra_prefixes_every_key_and_reaches_the_log_record(caplog):
    event = model_invocation_start(_request(), provider="openai")
    with caplog.at_level(logging.INFO, logger="skye.models"):
        logging.getLogger("skye.models").info("model invocation", extra=event.log_extra())
    record = caplog.records[-1]
    assert record.skye_correlation_id == event.correlation_id and record.skye_phase == "start"
    assert all(key.startswith("skye_") for key in event.log_extra())


def test_an_unknown_phase_is_rejected():
    with pytest.raises(ValidationError):
        ModelInvocationEvent(phase="middle", model="m", provider="p")
