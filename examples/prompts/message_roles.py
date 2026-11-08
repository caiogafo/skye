"""Message roles in a .skye prompt: ``message`` blocks, a history placeholder and roles from data.

Each ``message "role"`` block is one message with a real role; no role markers are written by hand.
``placeholder "history"`` is filled at render time with ``history={"history": [...]}``, as message
objects or as plain dicts. ``message turn.role`` inside ``each`` takes the role from data. The
prompt is ``trip`` in message_roles.skye, next to this file. Runs offline, no key.
"""

from pathlib import Path

from skye import AssistantMessage, UserMessage
from skye.prompts import load_prompt, render_prompt

PROMPTS = Path(__file__).with_name("message_roles.skye").read_text(encoding="utf-8")


def show(messages: list) -> None:
    for message in messages:
        print(f"  {message.role:<10} {message.content}")


def main() -> None:
    spec = load_prompt(PROMPTS, "trip")
    notes = [
        {"role": "user", "text": "I travel with a child."},
        {"role": "assistant", "text": "Short visits, then."},
    ]
    variables = {"question": "Plan one day in Rome.", "notes": notes}

    print("History as message objects")
    history = [
        UserMessage(content="I like museums."),
        AssistantMessage(content="Noted: museums first."),
    ]
    show(render_prompt(spec, variables, history={"history": history}))

    print("History as dicts")
    history_dicts = [
        {"role": "user", "content": "Any food tips?"},
        {"role": "assistant", "content": "Try supplì."},
    ]
    messages = render_prompt(
        spec, {**variables, "tone": "friendly"}, history={"history": history_dicts}
    )
    show(messages)

    print("No history")
    show(render_prompt(spec, {"question": "Is May a good month?"}))

    print("As request payload")
    print(f"  {messages[0].to_dict()}")


if __name__ == "__main__":
    main()
