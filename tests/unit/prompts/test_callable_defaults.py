"""A default value that is a function is called at each rendering; a provided variable wins over it."""

from skye.prompts import BasePromptBuilder


def test_a_callable_default_is_called_at_each_rendering():
    builder = BasePromptBuilder()
    calls = []
    builder.register_template("t", "Now: {{ now }}")
    builder.set_default_values({"now": lambda: calls.append(1) or f"tick-{len(calls)}"})
    assert builder.render("t", {})[0].content == "Now: tick-1"
    assert builder.render("t", {})[0].content == "Now: tick-2"


def test_a_provided_variable_wins_and_its_default_is_not_called():
    builder = BasePromptBuilder()
    builder.register_template("t", "Now: {{ now }}")
    builder.set_default_values({"now": lambda: (_ for _ in ()).throw(AssertionError("must not be called"))})
    assert builder.render("t", {"now": "fixed"})[0].content == "Now: fixed"
