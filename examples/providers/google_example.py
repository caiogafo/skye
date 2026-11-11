"""Google (Gemini on Vertex AI) through ``skye.provider("google")``: completion, streaming and embeddings.

Google needs a GCP project and a location. Set GCP_PROJECT_ID (and GCP_LOCATION if it is not ``us-central1``); without a project a scripted
client answers and the example says so. ``location`` is the Google parameter and is kept as it is (``region`` is accepted as an alias);
the same ``project_id`` and ``location`` build the embedding client with ``provider_type="embedding"``.
"""

import os
import sys
from pathlib import Path

import skye
from skye import SystemMessage, UserMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import provider_or_scripted  # noqa: E402

MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "text-embedding-005"


def main() -> None:
    project = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")
    client = provider_or_scripted("google", bool(project), "set GCP_PROJECT_ID", project_id=project, location=location)

    messages = [SystemMessage(content="You are a helpful assistant."), UserMessage(content="What is the capital of France?")]
    response = client.complete(messages=messages, model=MODEL, temperature=0.7, max_tokens=100)
    print("answer:", response.content)
    print(f"model={response.model} tokens={response.usage.total_tokens} finish={response.finish_reason}")

    print("stream: ", end="")
    for chunk in client.stream(messages=[UserMessage(content="Write a two-line poem about Python")], model=MODEL):
        print(chunk.delta, end="", flush=True)
    print()

    if project:
        embedder = skye.provider("google", project_id=project, location=location, model=EMBEDDING_MODEL, provider_type="embedding")
        print(f"embedding client in {embedder.location}:", len(embedder.encode("Rome")), "numbers")


if __name__ == "__main__":
    main()
