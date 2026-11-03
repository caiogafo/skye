"""Base content types: ContentChunk and StreamChunk (Live).

This example runs real library code end to end, with no client and no network.

It shows the two provider-agnostic content shapes in ``skye.base``:

- ``ContentChunk`` from ``skye.base.messages``: a piece of text with metadata, an
  optional ``chunk_id`` and ``source``. ``str(chunk)`` returns its text, which makes
  it convenient for document processing and RAG pipelines.
- ``StreamChunk`` from ``skye.base.completion``: one incremental delta of a streaming
  completion. Several chunks accumulate into the final text; the last chunk carries a
  ``finish_reason``.
"""

import skye  # noqa: F401  (imported so the example reads like user code)
from skye.base.completion import StreamChunk
from skye.base.messages import ContentChunk


def inspect_content_chunk() -> None:
    """Build a ContentChunk and read its fields and text form."""
    chunk = ContentChunk(
        text="Skye is built for serverless architectures.",
        metadata={"page": 1, "section": "Introduction"},
        chunk_id="doc-1-0001",
        source="design.md",
    )

    print("ContentChunk")
    print(f"  text    : {str(chunk)}")
    print(f"  source  : {chunk.source}")
    print(f"  chunk_id: {chunk.chunk_id}")
    print(f"  metadata: {chunk.metadata}")


def accumulate_stream_chunks() -> None:
    """Accumulate a few StreamChunk deltas into one final string."""
    stream = [
        StreamChunk(id="stream-1", delta="Hello", index=0),
        StreamChunk(id="stream-1", delta=", ", index=1),
        StreamChunk(id="stream-1", delta="world!", index=2),
        StreamChunk(id="stream-1", delta="", finish_reason="stop", index=3),
    ]

    text = ""
    for part in stream:
        text += part.delta
        if part.finish_reason is not None:
            print(f"  stream finished: {part.finish_reason}")

    print("StreamChunk")
    print(f"  accumulated text: {text}")


def main() -> None:
    inspect_content_chunk()
    print()
    accumulate_stream_chunks()


if __name__ == "__main__":
    main()
