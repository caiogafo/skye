"""Validation: check a .skye prompt, fix it, lay it out, then render it.

``skye.dsl.check_text`` lists every mistake with its line, column and fix (the checks of ``skye
check``); ``format_text`` lays a text out (``skye fmt``). ``load_prompt`` refuses a text with
mistakes, so a prompt is never half loaded. The texts are inline on purpose: they are badly written.
Runs offline, no key.
"""

from skye.dsl import check_text, format_text
from skye.prompts import load_prompt, render_prompt

WRONG = """prompt "greeting" {
  variables = { name = string }
  message "system" { text = "Hello {{ nme }}." }
  mesage "user" { text = "Hi" }
}
"""

FIXED = """prompt "greeting" {
variables = { name = string }
    message "system" { text = "Hello {{ name }}." }
  message "user" { text = "Hi" }
}
"""


def main() -> None:
    print("Diagnostics")
    for d in check_text(WRONG, "greeting.skye"):
        print(f"  {d.file}:{d.line}:{d.column}  {d.reason}  {d.fix}")
    print()

    print("Fixed and laid out")
    print("  mistakes:  ", len(check_text(FIXED)))
    formatted = format_text(FIXED)
    for line in formatted.splitlines():
        print(f"  | {line}")
    print()

    print("Rendered")
    for message in render_prompt(load_prompt(formatted, "greeting"), {"name": "Alice"}):
        print(f"  {message.role:<10} {message.content}")

    print("Missing variable at render time")
    try:
        render_prompt(load_prompt(FIXED, "greeting"), {})
    except ValueError as error:
        print(f"  error:     {str(error).split(' | ')[0]}")


if __name__ == "__main__":
    main()
