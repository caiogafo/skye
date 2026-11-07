# basic

What you learn: the first calls. Read in this order:

1. `async_and_streaming.py`: Async and streaming usage of a client created with ``skye.provider``
2. `configuration.py`: Configuration: a file, environment variables and code overrides, in that order of precedence (code > environment > file)
3. `quickstart.py`: Quick start: create a client with one call and ask a question
4. `simple_completion.py`: The core types of Skye: messages, a completion, token usage and a multi-turn conversation

Run: `python examples/basic/async_and_streaming.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
