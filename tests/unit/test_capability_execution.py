"""One execution primitive: every path returns an equal message, and a tool's own ``"Error:"`` text is not a failure.

Requirement 16.10 and 16.12 of steering; decisions D42, D43, D45; task 3.11 of the uxui spec.
"""

import asyncio
import json
from datetime import datetime

import pytest

from skye.base.capability_execution import arun_capability_call, find_capability, format_capability_result, run_capability_call
from skye.completion import CapabilityCall, CompleteResponse, TokenUsage
from skye.data import dump
from skye.messages import CapabilityMessage, CapabilityStatus
from skye.tools import CapabilityRegistry, capability
from skye.tools.capability_call_handler import CapabilityCallHandler
from skye.tools.capability_models import CapabilityResult


@capability
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@capability
def say_error() -> str:
    """Answer with text that begins with Error."""
    return "Error: not found"


@capability
def when() -> dict:
    """Return a value JSON cannot hold."""
    return {"at": datetime(2026, 1, 2, 3, 4, 5)}


@capability
def boom() -> str:
    """Raise."""
    raise RuntimeError("kaboom")


def _fields(message: CapabilityMessage) -> tuple[str, str, str, CapabilityStatus]:
    return (message.content, message.capability_id, message.capability_name, message.status)


def _response(*calls: CapabilityCall, capabilities=None) -> CompleteResponse:
    response = CompleteResponse(
        model="m",
        provider="p",
        content="",
        finish_reason="capability_calls",
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        capability_calls=list(calls),
    )
    response._capabilities = capabilities
    return response


def test_status_is_a_str_enum_with_a_derived_is_error():
    assert [s.value for s in CapabilityStatus] == ["ok", "error", "denied", "skipped"]
    assert CapabilityStatus.OK == "ok"
    ok = CapabilityMessage(content="x", capability_id="1", capability_name="n")
    denied = CapabilityMessage(content="x", capability_id="1", capability_name="n", status="denied")
    assert ok.status is CapabilityStatus.OK and not ok.is_error
    assert denied.status is CapabilityStatus.DENIED and denied.is_error
    assert dump(denied)["status"] == "denied"


def test_every_path_returns_an_equal_message():
    call = CapabilityCall(id="c1", name="add", arguments={"a": 1, "b": 2})
    response = _response(call, capabilities=[add])
    registry = CapabilityRegistry([add])
    primitive = _fields(run_capability_call(add, "c1", "add", {"a": 1, "b": 2}))
    assert primitive == ("3", "c1", "add", CapabilityStatus.OK)
    assert _fields(call.execute()) == primitive
    assert _fields(response.execute_capability_calls()[0]) == primitive
    assert _fields(asyncio.run(response.aexecute_capability_calls())[0]) == primitive
    assert _fields(asyncio.run(arun_capability_call(add, "c1", "add", {"a": 1, "b": 2}))) == primitive
    assert _fields(asyncio.run(call.aexecute())) == primitive
    assert _fields(asyncio.run(registry.run(call))) == primitive
    assert _fields(_response(call, capabilities=registry).execute_capability_calls()[0]) == primitive
    assert _fields(response.execute_capability_calls(registry)[0]) == primitive
    assert _fields(CapabilityResult(capability_call_id="c1", name="add", result=3).to_message()) == primitive


def test_a_tools_own_error_text_is_ok_and_a_raise_is_an_error():
    ok = run_capability_call(say_error, "1", "say_error", {})
    assert ok.content == "Error: not found" and ok.status is CapabilityStatus.OK and not ok.is_error
    failed = run_capability_call(boom, "2", "boom", {})
    assert failed.content == "Error: kaboom" and failed.status is CapabilityStatus.ERROR and failed.is_error
    missing = run_capability_call(None, "3", "nope", {})
    assert missing.status is CapabilityStatus.ERROR and "not found" in missing.content


def test_the_primitive_never_raises_for_bad_arguments():
    message = run_capability_call(add, "1", "add", {"a": 1})
    assert message.status is CapabilityStatus.ERROR


def test_a_value_json_cannot_hold_is_rendered_not_raised():
    message = run_capability_call(when, "1", "when", {})
    assert message.status is CapabilityStatus.OK
    assert json.loads(message.content) == {"at": "2026-01-02 03:04:05"}
    assert format_capability_result(25.0) == "25.0"
    assert format_capability_result([1, 2]) == "[1, 2]"


def test_the_response_runs_every_call_and_reports_each_status():
    calls = [CapabilityCall(id="1", name="add", arguments={"a": 1, "b": 2}), CapabilityCall(id="2", name="nope")]
    messages = _response(*calls, capabilities=[add]).execute_capability_calls()
    assert [m.status for m in messages] == [CapabilityStatus.OK, CapabilityStatus.ERROR]


def test_overrides_are_found_by_call_id_or_by_capability_name():
    call = CapabilityCall(id="c1", name="add", arguments={"a": 1, "b": 2})
    response = _response(call, capabilities=[add])
    assert response.execute_capability_calls(argument_overrides={"c1": {"b": 10}})[0].content == "11"
    assert response.execute_capability_calls(argument_overrides={"add": {"b": 20}})[0].content == "21"
    assert response.execute_capability_calls(argument_overrides={"add": {"b": 20}, "c1": {"b": 10}})[0].content == "11"
    assert call.execute(b=5).content == "6"


def test_the_response_without_calls_or_capabilities_raises_a_value_error():
    with pytest.raises(ValueError):
        _response(capabilities=[add]).execute_capability_calls()
    with pytest.raises(ValueError):
        _response(CapabilityCall(id="1", name="add"), capabilities=None).execute_capability_calls()


def test_a_saved_call_keeps_id_name_and_arguments_and_no_live_capability():
    call = CapabilityCall(id="c1", name="add", arguments={"a": 1, "b": 2})
    _response(call, capabilities=[add])
    assert dump(call) == {"id": "c1", "name": "add", "arguments": {"a": 1, "b": 2}}
    assert call.execute().content == "3"


def test_find_capability_looks_in_a_list_or_a_registry():
    assert find_capability([add, boom], "boom") is boom
    assert find_capability(CapabilityRegistry([add]), "add") is add
    assert find_capability(None, "add") is None and find_capability([add], "nope") is None


def test_the_registry_alias_and_execute_paths():
    registry = CapabilityRegistry()
    registry.add(add)
    assert registry.list() == registry.list_all() == ["add"]
    assert registry.execute("add", {"a": 1, "b": 2}).content == "3"
    assert asyncio.run(registry.aexecute("add", {"a": 1, "b": 2})).content == "3"


def test_the_capability_call_handler_still_gives_results_that_convert_to_the_same_message():
    registry = CapabilityRegistry([add])
    results = asyncio.run(CapabilityCallHandler(registry).execute_capability_calls([CapabilityCall(id="c1", name="add", arguments={"a": 1, "b": 2})]))
    assert _fields(results[0].to_message()) == ("3", "c1", "add", CapabilityStatus.OK)
