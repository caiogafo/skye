"""Basic rendering: register a .skye prompt file, fill its variables, defaults and a partial.

``register_template(name, path, from_string=False)`` reads the prompt ``greeting`` from
basic_rendering.skye, next to this file. ``render`` returns messages ready for ``client.complete``;
``format`` returns their text as one string. A missing required variable is an error that names
it. Runs offline, no key.
"""

from pathlib import Path

from skye.prompts import BasePromptBuilder

PROMPT_FILE = Path(__file__).with_name("basic_rendering.skye")


def main() -> None:
    builder = BasePromptBuilder()
    builder.register_template("greeting", str(PROMPT_FILE), from_string=False)

    print("Render")
    for message in builder.render("greeting", {"name": "Alice", "product": "Skye"}):
        print(f"  {message.role:<10} {message.content}")

    print("Defaults")
    builder.set_default_values({"product": "Skye"})
    print(f"  text:     {builder.render('greeting', {'name': 'Bob'})[-1].content}")

    print("Partial")
    support = builder.partial(product="Skye Support")
    print(f"  partial:  {support.render('greeting', {'name': 'Carol'})[-1].content}")
    print(f"  base:     {builder.render('greeting', {'name': 'Carol'})[-1].content}")

    print("Optional variable")
    with_note = builder.render("greeting", {"name": "Dan", "note": "Your trial lasts 30 days."})
    print(f"  with:     {with_note[-1].content!r}")

    print("Missing required variable")
    try:
        builder.render("greeting", {})
    except ValueError as error:
        print(f"  error:    {str(error).split(' | ')[0]}")

    print("Registry")
    metadata = builder.get_template_metadata("greeting")
    print(f"  required: {', '.join(metadata['variables'])}")
    print(f"  optional: {', '.join(metadata['optional_variables'])}")
    print(f"  format:   {metadata['format']}")
    print(f"  valid:    {builder.validate_template('greeting')['valid']}")


if __name__ == "__main__":
    main()
