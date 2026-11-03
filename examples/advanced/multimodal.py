"""Multimodal inputs: turn an image (URL, data URL, file or bytes) into the shape each provider expects.

`ImageHandler` reads the four kinds of source and returns the part a provider adds to a message: for OpenAI an `image_url` part,
for Anthropic and Bedrock a base64 block. It needs no key and no network.

Not yet available: carrying the images inside a `UserMessage` through `client.complete`. Until the adapters do it (task 5.2 of
the `models` spec) a message holds text only.
"""

import base64
import tempfile
from pathlib import Path

from skye.models.transport.multimodal import ImageHandler

# A 1x1 PNG, so the example needs no image file
PIXEL = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pixel.png"
        path.write_bytes(PIXEL)

        sources = {
            "url": "https://example.com/image.jpg",
            "data URL": "data:image/png;base64," + base64.b64encode(PIXEL).decode(),
            "file": path,
            "bytes": PIXEL,
        }
        for kind, source in sources.items():
            part = ImageHandler.to_openai_format(source)
            print(f"{kind}: OpenAI part of type {part['type']!r}, url starts with {part['image_url']['url'][:22]!r}")

        block = ImageHandler.to_anthropic_format(PIXEL)
        print("Anthropic block:", block["type"], block["source"]["media_type"])


if __name__ == "__main__":
    main()
