"""Validation: a .skye prompt with mistakes is rejected with every diagnostic, line and column.

``load_prompt`` raises a ``ValidationError`` (a ``ValueError``) whose ``details["diagnostics"]``
lists each mistake with a fix, the same checks as ``skye check``; the text is never half loaded.
Use ``skye fmt`` on the command line to lay a file out. The texts below are inline on purpose:
they are badly written. Runs offline, no key.
"""

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
    try:
        load_prompt(WRONG, "greeting")
    except ValueError as error:
        for diagnostic in error.details["diagnostics"]:
            print(f"  {diagnostic}")
    print()

    print("Fixed")
    for message in render_prompt(load_prompt(FIXED, "greeting"), {"name": "Alice"}):
        print(f"  {message.role:<10} {message.content}")

    print("Missing variable at render time")
    try:
        render_prompt(load_prompt(FIXED, "greeting"), {})
    except ValueError as error:
        print(f"  error:     {str(error).split(' | ')[0]}")


if __name__ == "__main__":
    main()
