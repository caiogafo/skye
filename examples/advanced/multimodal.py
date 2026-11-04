"""Multimodal inputs: turn an image (URL, data URL, file or bytes) into the shape each provider expects.

`ImageHandler` reads the four kinds of source and returns the part a provider adds to a message: for OpenAI an `image_url` part,
for Anthropic and Bedrock a base64 block. It needs no key and no network.

To send images, put them in `UserMessage(images=[...])`: each adapter converts them itself (OpenAI, Anthropic, Bedrock and
Google). Bedrock does not fetch URLs, so give it a file, bytes or a data URL.
"""

import base64
import tempfile
from pathlib import Path

from skye import UserMessage
from skye.models import ImageHandler

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

        # The same sources, inside a message (needs OPENAI_API_KEY and a network)
        message = UserMessage(content="What is in this image?", images=[path])
        print("message carries", len(message.images), "image(s):", message.to_dict()["images"][0][:22])
        # client = skye.provider("openai"); client.complete(messages=[message], model="gpt-4o")


if __name__ == "__main__":
    main()
