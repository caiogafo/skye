"""Cohere embeddings through ``skye.provider("cohere")`` (Live).

Cohere is an embedding provider in Skye (there is no Cohere language-model adapter). A name that
has only an embedding provider gives it without ``provider_type``, so these two lines are the same::

    embedder = skye.provider("cohere", model="embed-english-v3.0")
    embedder = skye.provider("cohere", model="embed-english-v3.0", provider_type="embedding")

The key comes from ``COHERE_API_KEY`` when ``api_key`` is not given; a missing key raises
``ConfigurationError`` naming the variable. Without the key a scripted embedder answers and the
example says so.
"""

import math
import sys
from pathlib import Path

import skye
from skye.exceptions import ConfigurationError

# The shared offline helper lives in examples/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _offline import get_embedder  # noqa: E402

MODEL = "embed-english-v3.0"


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1.0)


def main() -> None:
    embedder = get_embedder("cohere", model=MODEL)
    texts = ["serverless functions start fast", "cold starts on Lambda", "a recipe for bread"]
    vectors = embedder.encode_batch(texts)
    print(f"{len(vectors)} vectors of {len(vectors[0])} numbers")
    for text, vector in zip(texts[1:], vectors[1:]):
        print(f"  similarity to {texts[0]!r}: {cosine(vectors[0], vector):.2f} ({text!r})")

    # Without the key, the error names the variable to set
    try:
        skye.provider("cohere", model=MODEL)
    except ConfigurationError as error:
        print("Expected without a key:", error.message)


if __name__ == "__main__":
    main()
