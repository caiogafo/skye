---
title: "Images"
status: current
---

# Images

This guide shows you how to send images to a vision model with the text of a message, from a URL, a file or bytes, and what each
provider accepts.

## What you need

- A client from `skye.provider(...)` for a model that reads images, for example `gpt-4o-mini` on OpenAI, a Claude 3 model on
  Anthropic or Bedrock, or a Gemini model on Google. See [Call a provider](call-a-provider.md).

## Put images in a message

`UserMessage` takes `images`, a list next to `content`. Each image is one of:

| Source | Example |
|---|---|
| an `http(s)` URL | `"https://example.com/photo.jpg"` |
| a data URL | `"data:image/png;base64,iVBORw0..."` |
| a file path, as `str` or `Path` | `Path("photo.png")` |
| raw bytes | `path.read_bytes()` |

```python
from pathlib import Path

from skye import UserMessage

message = UserMessage(content="What is in this image?", images=[Path("photo.png")])
response = client.complete(messages=[message], model="gpt-4o-mini", max_tokens=100)
```

The client converts each image to its provider's shape when it sends the request; the same message works for every vision model.
Several images in one message are a longer list. A file that does not exist raises `ValidationError`.

This example sends one image from a URL, one from a data URL and one read from a file, then two images in one message:

```python
--8<-- "examples/providers/multimodal_example.py:9:47"
```

Without `OPENAI_API_KEY` a scripted client answers, so the example runs offline.

## What each provider accepts

| Provider | URL | Data URL, file, bytes |
|---|---|---|
| OpenAI, Azure OpenAI | sent as is; the provider fetches it | sent as a base64 data URL |
| Anthropic | sent as a `url` image source; the provider fetches it | sent as a base64 image source |
| Bedrock | not accepted: raises `ValidationError` ("Bedrock does not fetch image URLs") | sent as bytes in a Converse image block |
| Google | sent as `fileData` with the URL as `fileUri` | sent as `inlineData` |

For Bedrock, download the image first, or pass a file, bytes or a data URL. For Google, a URL is best a `gs://` object that the
project can read.

The media type of a file comes from its extension (`.png`, `.jpg`, `.gif`, `.webp`, ...); the media type of bytes comes from their
first bytes.

## See the conversion without a call

`ImageHandler` (from `skye.models`) is the converter the clients use. It needs no key and no network, so you can check what a source
becomes before you send it:

```python
--8<-- "examples/advanced/multimodal.py:10:41"
```

`ImageHandler` has `to_openai_format`, `to_anthropic_format`, `to_bedrock_format` and `to_google_format`, and `process_image`, which
reads any source into a data URL or keeps a URL.

## Images in embeddings

To compare images by meaning, use the Google multimodal embedding provider, which encodes texts and images in the same vector
space. See [Embeddings](embeddings.md).

## See also

- [Call a provider](call-a-provider.md) and [Tokens and cost](tokens-and-cost.md): an image counts as input tokens for the provider.
- [`skye.models` API reference](../../reference/api/models.md) (`ImageHandler`) and [`skye` API reference](../../reference/api/skye.md)
  (`UserMessage`).
- Examples: [`providers/multimodal_example.py`](https://github.com/ggiallo28/skye/blob/main/examples/providers/multimodal_example.py),
  [`advanced/multimodal.py`](https://github.com/ggiallo28/skye/blob/main/examples/advanced/multimodal.py).
