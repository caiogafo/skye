"""Control flow in a .skye prompt: ``when``, ``each``, ``loop.*``, map entries and filters.

Conditions and loops are blocks, not template tags: ``when x { ... }``, ``when not x { ... }`` and
``each item in items { ... }``. Inside ``each``, ``loop.index`` counts from 1 and ``loop.last``
marks the last item; an ``each`` over a map gives entries with ``.key`` and ``.value``. The prompt
is ``review`` in control_flow.skye, next to this file. Runs offline, no key.
"""

from pathlib import Path

from skye.prompts import load_prompt, render_prompt

PROMPTS = Path(__file__).with_name("control_flow.skye").read_text(encoding="utf-8")


def main() -> None:
    spec = load_prompt(PROMPTS, "review")
    base = {
        "language": "python",
        "rules": ["Errors keep their cause", "Names say what they hold"],
        "owners": {"api": "Alice", "docs": "Bob"},
    }
    tools = [
        {"name": "run_tests", "description": "Run the test suite"},
        {"name": "lint", "description": "Check the style"},
    ]
    variable_sets = [
        ("Lenient, no tools", base),
        ("Strict, two tools", {**base, "strict": True, "tools": tools}),
    ]

    for title, variables in variable_sets:
        print(title)
        for message in render_prompt(spec, variables):
            print(f"[{message.role}]")
            print(message.content)
        print()


if __name__ == "__main__":
    main()
