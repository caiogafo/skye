"""Counting tokens with TokenCounter (Live).

This example runs real library code end to end, with no network.

``TokenCounter`` counts tokens in plain text and in a list of messages, adding the
per-message overhead each model uses for formatting. Exact counts for GPT models come
from ``tiktoken``, which ships with the ``tokens`` extra (``pip install "skyeai[tokens]"``).
Without it ``TokenCounter`` falls back to its standard-library approximation (about four
characters per token); with the extra installed the same calls return exact counts for GPT
models.
"""

import skye  # noqa: F401  (imported so the example reads like user code)
from skye import SystemMessage, UserMessage
from skye.models import TokenCounter


def main() -> None:
    model = "gpt-4"

    text = "Skye keeps the core to the Python standard library."
    text_tokens = TokenCounter.count_tokens(text, model)
    print("count_tokens (exact with the tokens extra, otherwise the stdlib approximation):")
    print(f"  model : {model}")
    print(f"  text  : {text}")
    print(f"  tokens: {text_tokens}")

    messages = [
        SystemMessage(content="You are a concise assistant."),
        UserMessage(content="Summarize the serverless-first rule in one sentence."),
    ]
    message_tokens = TokenCounter.count_message_tokens(messages, model)
    print("\ncount_message_tokens (includes per-message overhead):")
    print(f"  messages: {len(messages)}")
    print(f"  tokens  : {message_tokens}")

    print('\nInstall "skyeai[tokens]" (tiktoken) for exact GPT token counts.')


if __name__ == "__main__":
    main()
