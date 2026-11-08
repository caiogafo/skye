"""Few-shot examples in a .skye prompt: each example becomes a user turn and an assistant turn.

``each example in examples { message "user" {...} message "assistant" {...} }`` turns a list of
dicts into chat turns, so the model sees worked examples as a real conversation and no example
shape is written by hand. The prompt is ``sentiment`` in few_shot.skye, next to this file.
Runs offline, no key.
"""

from pathlib import Path

from skye.prompts import load_prompt, render_prompt

PROMPTS = Path(__file__).with_name("few_shot.skye").read_text(encoding="utf-8")

EXAMPLES = [
    {"review": "Arrived early and works perfectly.", "sentiment": "positive"},
    {"review": "The box was crushed and the cable missing.", "sentiment": "negative"},
    {"review": "It is a phone charger.", "sentiment": "neutral"},
    {"review": "Best purchase this year.", "sentiment": "positive"},
]


def show(messages: list) -> None:
    for message in messages:
        print(f"  {message.role:<10} {message.content}")


def main() -> None:
    spec = load_prompt(PROMPTS, "sentiment")
    review = "Stopped working after a week."

    print("Two examples")
    show(render_prompt(spec, {"examples": EXAMPLES[:2], "review": review}))

    print("No examples")
    show(render_prompt(spec, {"review": review}))

    messages = render_prompt(spec, {"examples": EXAMPLES, "review": review})
    print("All examples")
    print(f"  messages:  {len(messages)}")
    print(f"  turns:     {', '.join(m.role for m in messages)}")


if __name__ == "__main__":
    main()
