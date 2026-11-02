"""Prompt engineering with the prompt builder: few-shot examples, chain of thought, composition and dynamic prompts.

The builder renders templates into ``SkyeMessage`` objects. A template uses ``{{ variable }}``, ``{% if %}``, ``{% for %}`` and filters; it
is rendered by the standard-library engine, so nothing is installed for it. ``[SYSTEM]`` and ``[USER]`` markers split a template into
messages with those roles.

No provider is needed; if OPENAI_API_KEY is set, the last prompt is also sent to a model.
"""

import os
from datetime import date

import skye
from skye.prompts import BasePromptBuilder


def few_shot(builder: BasePromptBuilder) -> None:
    """Examples are formatted with their own template and injected where the template says ``{{ examples }}``."""
    builder.register_template(
        "sentiment",
        "Classify the sentiment of the text as positive, negative or neutral.\n\n{{ examples }}\n\nText: {{ text }}\nSentiment:",
    )
    builder.add_examples(
        "sentiment",
        [
            {"text": "I love this phone", "label": "positive"},
            {"text": "The battery died in an hour", "label": "negative"},
            {"text": "It arrived on Tuesday", "label": "neutral"},
        ],
        example_template="Text: {text}\nSentiment: {label}",
    )
    print("--- few-shot ---")
    print(builder.render("sentiment", {"text": "Great screen, terrible speakers"})[0].content)


def chain_of_thought(builder: BasePromptBuilder) -> None:
    """A system message that asks for steps, and a user message with the question."""
    builder.register_template(
        "cot",
        "[SYSTEM]\nYou solve problems. Think step by step, then give the final answer after 'Answer:'.\n\n"
        "[USER]\n{{ question }}",
    )
    messages = builder.render("cot", {"question": "A train goes 60 km in 45 minutes. What is its speed in km/h?"})
    print("\n--- chain of thought ---")
    for message in messages:
        print(f"[{message.role}] {message.content}")


def composition(builder: BasePromptBuilder) -> None:
    """Small templates joined into a bigger one."""
    builder.register_template("persona", "You are a {{ role }} who writes in a {{ tone }} tone.")
    builder.register_template("task", "Summarize the text below in {{ sentences }} sentences.\n\n{{ text }}")
    builder.compose_templates("summarizer", ["persona", "task"])
    builder.set_default_values({"tone": "neutral", "sentences": 2})
    print("\n--- composition ---")
    print(builder.render("summarizer", {"role": "technical editor", "text": "Skye is a light library for serverless applications."})[0].content)


def dynamic(builder: BasePromptBuilder) -> list:
    """Defaults can be functions, evaluated at each rendering; a custom filter reshapes a value inside the template."""
    builder.register_jinja_filter("shout", lambda value: str(value).upper())
    builder.register_template("greeting", "Today is {{ today }}. Greet {{ name | shout }} in one sentence.")
    builder.set_default_values({"today": lambda: date.today().isoformat()})
    messages = builder.render("greeting", {"name": "ana"})
    print("\n--- dynamic ---")
    print(messages[0].content)
    return messages


def main() -> None:
    builder = BasePromptBuilder()
    few_shot(builder)
    chain_of_thought(builder)
    composition(builder)
    messages = dynamic(builder)

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = skye.provider("openai", api_key=api_key)
        print("\nmodel:", client.complete(messages=messages, model="gpt-4", max_tokens=40).content)


if __name__ == "__main__":
    main()
