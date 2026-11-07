"""Google (Gemini on Vertex AI) through ``skye.provider("google")``: completion and streaming.

Google needs a GCP project and a location. Set GCP_PROJECT_ID (and GCP_LOCATION if it is not ``us-central1``); without a project a scripted
client answers and the example says so.
"""

import os
import sys
from pathlib import Path

from skye import SystemMessage, UserMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import provider_or_scripted  # noqa: E402

MODEL = "gemini-1.5-pro"


def main() -> None:
    project = os.getenv("GCP_PROJECT_ID")
    client = provider_or_scripted("google", bool(project), "set GCP_PROJECT_ID", project_id=project, location=os.getenv("GCP_LOCATION", "us-central1"))

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
