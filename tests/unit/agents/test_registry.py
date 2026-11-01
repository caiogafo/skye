"""Unit tests for the agents registry (extension point for agent types)."""

import asyncio

import pytest

from nimbus.agents import registry
from nimbus.agents.registry import (
    REACT,
    ReActAgent,
    create_agent,
    get_agent_type,
    list_agent_types,
    register_agent_type,
)
from nimbus.base.exceptions import ConfigurationError, NimbusError
from nimbus.base.interfaces.runnable import Runnable


@pytest.fixture(autouse=True)
def _isolated_registry():
    saved = dict(registry._REGISTRY)
    yield
    registry._REGISTRY.clear()
    registry._REGISTRY.update(saved)


class _Echo:
    async def invoke(self, input):
        return input


def test_react_is_registered_by_default():
    assert REACT in list_agent_types()
    assert get_agent_type(REACT) is ReActAgent


def test_register_and_lookup_custom_type():
    register_agent_type("echo", _Echo)
    assert get_agent_type("echo") is _Echo
    assert "echo" in list_agent_types()
    agent = create_agent("echo")
    assert asyncio.run(agent.invoke("x")) == "x"


def test_list_is_sorted():
    register_agent_type("aaa", _Echo)
    names = list_agent_types()
    assert names == sorted(names)


def test_duplicate_name_raises_nimbus_error():
    register_agent_type("dup", _Echo)
    with pytest.raises(ConfigurationError) as exc:
        register_agent_type("dup", _Echo)
    assert isinstance(exc.value, NimbusError)


def test_duplicate_allowed_with_replace():
    register_agent_type("dup", _Echo)
    register_agent_type("dup", ReActAgent, replace=True)
    assert get_agent_type("dup") is ReActAgent


def test_unknown_name_raises_nimbus_error():
    with pytest.raises(ConfigurationError) as exc:
        get_agent_type("nope")
    assert isinstance(exc.value, NimbusError)
    assert REACT in exc.value.details["available"]


def test_empty_name_rejected():
    with pytest.raises(ConfigurationError):
        register_agent_type("", _Echo)


def test_placeholder_conforms_to_runnable():
    agent = create_agent(REACT, foo=1)
    assert isinstance(agent, Runnable)
    assert agent.options == {"foo": 1}


def test_placeholder_invoke_is_not_implemented():
    with pytest.raises(NotImplementedError):
        asyncio.run(ReActAgent().invoke("hi"))
