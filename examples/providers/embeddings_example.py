"""Embeddings through ``skye.provider(..., provider_type="embedding")``.

The embedding client has ``encode`` (one text), ``encode_batch`` (several), their async forms ``aencode`` and ``aencode_batch``, and
``get_vector_dimension``. The same call works for OpenAI, Bedrock (Titan) and Google; only the name and the configuration change:
``skye.provider("bedrock", region="us-east-1", model="amazon.titan-embed-text-v1", provider_type="embedding")``. With OPENAI_API_KEY set the
vectors are real; without a key a scripted embedder answers and the example says so.
"""

import asyncio
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_embedder  # noqa: E402


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def main() -> None:
    embedder = get_embedder("openai", "text-embedding-3-small")
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Python is a popular programming language",
    ]

    vectors = embedder.encode_batch(texts)
    print(f"{len(vectors)} vectors of dimension {embedder.get_vector_dimension()}; first values: {vectors[0][:3]}")
    print(f"similarity of text 1 and 2: {cosine_similarity(vectors[0], vectors[1]):.4f}")
    print(f"similarity of text 2 and 3: {cosine_similarity(vectors[1], vectors[2]):.4f}")

    print("one text:", embedder.encode("This is a single text")[:3])
    print("async:", asyncio.run(embedder.aencode("This is an async call"))[:3])


if __name__ == "__main__":
    main()
