"""Prompt engineering with the prompt builder: few-shot examples, composition and a .skye prompt.

A text template does interpolation only: ``{{ variable }}`` and filters, rendered by the
standard-library engine, so nothing is installed for it. Conditions and loops are written in a
``.skye`` prompt (``when``, ``each``), registered on the same builder.

No provider is needed; if OPENAI_API_KEY is set, the last prompt is also sent to a model.
"""

import os
from datetime import date

import skye
from skye.prompts import BasePromptBuilder

GREETING = """prompt "greeting" {
  variables = {
    name   = string            "Who to greet"
    today  = string            "The date"
    topics = list(string, [])  "Topics to mention"
  }
  message "system" { text = "Today is {{ today }}. Greet {{ name | shout }} in one sentence." }
  message "user" {
    when topics { text = "Mention: {{ topics | join(', ') }}." }
    when not topics { text = "Keep it short." }
  }
}
"""


def few_shot(builder: BasePromptBuilder) -> None:
    """Examples become user/assistant message pairs, before the last user message."""
    template = "[SYSTEM]\nAnswer positive, negative or neutral.\n[USER]\n{{ text }}"
    builder.register_template("sentiment", template)
    examples = [
        {"text": "I love this phone", "label": "positive"},
        {"text": "The battery died in an hour", "label": "negative"},
    ]
    builder.add_examples("sentiment", examples, as_messages=True)
    print("--- few-shot ---")
    for message in builder.render("sentiment", {"text": "Great screen, terrible speakers"}):
        print(f"[{message.role}] {message.content}")


def composition(builder: BasePromptBuilder) -> None:
    """Small templates joined into a bigger one."""
    builder.register_template("persona", "You are a {{ role }} who writes in a {{ tone }} tone.")
    builder.register_template("task", "Summarize in {{ sentences }} sentences:\n\n{{ text }}")
    builder.compose_templates("summarizer", ["persona", "task"])
    builder.set_default_values({"tone": "neutral", "sentences": 2})
    variables = {"role": "technical editor", "text": "Skye is a light library for serverless apps."}
    print("\n--- composition ---")
    print(builder.render("summarizer", variables)[0].content)


def dynamic(builder: BasePromptBuilder) -> list:
    """A .skye prompt with a condition, a default that is a function, and a custom filter."""
    builder.register_filter("shout", lambda value: str(value).upper())
    builder.register_template("greeting", GREETING)
    builder.set_default_values({"today": lambda: date.today().isoformat()})
    messages = builder.render("greeting", {"name": "ana", "topics": ["the weather"]})
    print("\n--- dynamic ---")
    for message in messages:
        print(f"[{message.role}] {message.content}")
    return messages


def main() -> None:
    builder = BasePromptBuilder()
    few_shot(builder)
    composition(builder)
    messages = dynamic(builder)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = skye.provider("openai", api_key=api_key)
        print("\nmodel:", client.complete(messages=messages, model="gpt-4", max_tokens=40).content)


if __name__ == "__main__":
    main()
