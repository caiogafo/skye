"""Multimodal inputs: images in a message, from a URL, a base64 data URL or a file.

A ``UserMessage`` carries text and, next to it, ``images``: a list of URLs, data URLs or file paths. The library converts them to the
shape of each provider (for OpenAI an ``image_url`` part), so the same message works wherever the model accepts images.

Set OPENAI_API_KEY.
"""

import base64
import os
import tempfile
from pathlib import Path

import skye
from skye.base.messages import UserMessage

# A 1x1 PNG, so the example needs no image file
PIXEL = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set, skipping")
        return

    client = skye.provider("openai", api_key=api_key)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pixel.png"
        path.write_bytes(PIXEL)

        sources = {
            "url": "https://example.com/image.jpg",
            "data URL": "data:image/png;base64," + base64.b64encode(PIXEL).decode(),
            "file": str(path),
        }
        for kind, image in sources.items():
            message = UserMessage(content=f"What is in this image ({kind})?", images=[image])
            response = client.complete(messages=[message], model="gpt-4o", max_tokens=50)
            print(f"{kind}: {response.content}")

        # Several images in one message
        message = UserMessage(content="Compare these two images.", images=[sources["data URL"], str(path)])
        print("two images:", client.complete(messages=[message], model="gpt-4o", max_tokens=50).content)


if __name__ == "__main__":
    main()
