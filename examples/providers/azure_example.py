"""Azure OpenAI through ``skye.provider("azure")``: completion and streaming.

Azure needs an endpoint, an API version and the name of your deployment, which is also the ``model`` of a call. Set AZURE_OPENAI_API_KEY and
AZURE_OPENAI_ENDPOINT (and AZURE_OPENAI_DEPLOYMENT if it is not ``gpt-4``); without them a scripted client answers and the example says so.
"""

import os
import sys
from pathlib import Path

from skye import SystemMessage, UserMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import provider_or_scripted  # noqa: E402

MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")  # the name of your Azure deployment


def main() -> None:
    key, endpoint = os.getenv("AZURE_OPENAI_API_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT")
    client = provider_or_scripted(
        "azure", bool(key and endpoint), "set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT",
        api_key=key, azure_endpoint=endpoint, api_version="2024-02-15-preview", deployment_name=MODEL,
    )

    messages = [SystemMessage(content="You are a helpful assistant."), UserMessage(content="What is the capital of France?")]
    response = client.complete(messages=messages, model=MODEL, temperature=0.7, max_tokens=100)
    print("answer:", response.content)
    print(f"model={response.model} tokens={response.usage.total_tokens} finish={response.finish_reason}")

    print("stream: ", end="")
    for chunk in client.stream(messages=[UserMessage(content="Write a two-line poem about Python")], model=MODEL):
        print(chunk.delta, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
