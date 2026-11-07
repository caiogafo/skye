# advanced

What you learn: the advanced calls. Read in this order:

1. `custom_providers.py`: A custom provider: extend the base model provider, register it, and use it like any other
2. `function_calling.py`: Function calling: several capabilities, parallel execution and errors inside a capability
3. `multimodal.py`: Multimodal inputs: turn an image (URL, data URL, file or bytes) into the shape each provider expects
4. `prompt_engineering.py`: Prompt engineering with the prompt builder: few-shot examples, composition and dynamic prompts
5. `streaming.py`: Streaming: tokens as the model writes them, with ``stream`` (sync) and ``astream`` (async)
6. `structured_output.py`: Structured output: ask for a declared shape and get a typed object back
7. `value_proposition.py`: The value of Skye in one example: one prompt, several providers, and a fallback when one fails

Run: `python examples/advanced/custom_providers.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
