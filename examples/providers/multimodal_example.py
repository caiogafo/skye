"""Images in a message: from a URL, from a data URL and from a file.

``UserMessage(content=..., images=[...])`` takes image URLs (HTTP or data URLs). The client turns them into the shape each provider
expects, so the same message works for OpenAI, Anthropic, Bedrock and Google vision models; ``examples/advanced/multimodal.py`` shows the
conversions. Several images in one message are just a longer list. With OPENAI_API_KEY set the call is real; without a key a scripted
client answers and the example says so.
"""

import base64
import sys
import tempfile
from pathlib import Path

from skye import UserMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402

# A 1x1 PNG, so the example needs no image file of its own
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def data_url(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode()


def main() -> None:
    client = get_client("openai")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "pixel.png"
        path.write_bytes(PNG)
        sources = {
            "url": "https://example.com/image.jpg",
            "data url": data_url(PNG),
            "file": data_url(path.read_bytes()),  # read the file and send it as a data URL
        }
        for label, image in sources.items():
            message = UserMessage(content="What's in this image?", images=[image])
            response = client.complete(messages=[message], model="gpt-4o", max_tokens=50)
            print(f"{label}: {response.content[:60]}")

    both = UserMessage(content="Compare these two images", images=[sources["url"], sources["data url"]])
    print("two images:", client.complete(messages=[both], model="gpt-4o", max_tokens=50).content[:60])


if __name__ == "__main__":
    main()
