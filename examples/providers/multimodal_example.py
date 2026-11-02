"""Multimodal Input Example.

This example demonstrates how to use multimodal inputs (images) with Skye.

Features shown:
- Image from URL
- Image from file path
- Image from base64
- Vision models (GPT-4 Vision, Claude 3 Vision, Gemini)
"""

import os
import base64
from pathlib import Path
from skye.base.completion import CompletionRequest
from skye.base.messages import UserMessage
from skye.models import ProviderRegistry


def image_from_url():
    """Example using image from URL."""
    print("=" * 60)
    print("Multimodal - Image from URL")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    print("""
Using an image from a URL:

```python
request = CompletionRequest(
    messages=[
        UserMessage(
            content="What's in this image?",
            images=["https://example.com/image.jpg"]
        )
    ],
    model="gpt-4-vision"
)

response = provider.complete(request)
print(response.content)
```

The image URL can be:
- Public HTTP/HTTPS URL
- Data URL (base64 encoded)
- Any accessible image URL
""")


def image_from_file():
    """Example using image from file path."""
    print("\n" + "=" * 60)
    print("Multimodal - Image from File Path")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    print("""
Using an image from a file path:

```python
from pathlib import Path

image_path = Path("path/to/image.png")

request = CompletionRequest(
    messages=[
        UserMessage(
            content="Describe this image",
            images=[str(image_path)]
        )
    ],
    model="gpt-4-vision"
)

response = provider.complete(request)
print(response.content)
```

Supported formats:
- .jpg, .jpeg
- .png
- .gif
- .webp

The image is automatically converted to base64 and sent to the provider.
""")


def image_from_base64():
    """Example using base64 encoded image."""
    print("\n" + "=" * 60)
    print("Multimodal - Image from Base64")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    print("""
Using a base64 encoded image:

```python
import base64

# Read image file
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Create data URL
data_url = f"data:image/jpeg;base64,{image_data}"

request = CompletionRequest(
    messages=[
        UserMessage(
            content="What's in this image?",
            images=[data_url]
        )
    ],
    model="gpt-4-vision"
)

response = provider.complete(request)
print(response.content)
```

This is useful when:
- You have image bytes in memory
- You want to avoid file I/O
- You're processing images from a stream
""")


def multiple_images():
    """Example with multiple images."""
    print("\n" + "=" * 60)
    print("Multimodal - Multiple Images")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    print("""
Using multiple images in one request:

```python
request = CompletionRequest(
    messages=[
        UserMessage(
            content="Compare these two images",
            images=[
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg"
            ]
        )
    ],
    model="gpt-4-vision"
)

response = provider.complete(request)
print(response.content)
```

You can mix different image sources:
- URLs
- File paths
- Base64 data URLs

All are handled transparently by Skye.
""")


def vision_models():
    """Example showing different vision models."""
    print("\n" + "=" * 60)
    print("Multimodal - Vision Models")
    print("=" * 60)
    
    print("""
Different providers support different vision models:

**OpenAI:**
- gpt-4-vision (GPT-4 with vision)
- gpt-4-turbo (includes vision)
- gpt-4o (multimodal)

**Anthropic:**
- claude-3-opus (vision capable)
- claude-3-sonnet (vision capable)
- claude-3-haiku (vision capable)

**Google:**
- gemini-pro-vision
- gemini-1.5-pro (multimodal)

**AWS Bedrock:**
- anthropic.claude-3-opus (vision)
- anthropic.claude-3-sonnet (vision)
- anthropic.claude-3-haiku (vision)

Example with Anthropic:

```python
from skye.models import ProviderRegistry

provider = ProviderRegistry.get_model_provider(
    "anthropic",
    api_key="sk-ant-..."
)

request = CompletionRequest(
    messages=[
        UserMessage(
            content="What's in this image?",
            images=["https://example.com/image.jpg"]
        )
    ],
    model="claude-3-sonnet-20240229"
)

response = provider.complete(request)
print(response.content)
```
""")


def image_analysis_workflow():
    """Example of a complete image analysis workflow."""
    print("\n" + "=" * 60)
    print("Multimodal - Image Analysis Workflow")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = ProviderRegistry.get_model_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    print("""
Complete workflow for image analysis:

```python
from pathlib import Path
from skye.base.completion import CompletionRequest
from skye.base.messages import UserMessage
from skye.models import ProviderRegistry

# Initialize provider
provider = ProviderRegistry.get_model_provider(
    "openai",
    api_key="sk-..."
)

# Step 1: Analyze image
image_path = Path("screenshot.png")

request = CompletionRequest(
    messages=[
        UserMessage(
            content="Analyze this screenshot and describe what you see",
            images=[str(image_path)]
        )
    ],
    model="gpt-4-vision",
    max_tokens=500
)

response = provider.complete(request)
analysis = response.content

print("Analysis:", analysis)

# Step 2: Ask follow-up question
request = CompletionRequest(
    messages=[
        UserMessage(
            content="Analyze this screenshot and describe what you see",
            images=[str(image_path)]
        ),
        response.to_message(),
        UserMessage(content="What are the main UI elements?")
    ],
    model="gpt-4-vision",
    max_tokens=300
)

response = provider.complete(request)
print("UI Elements:", response.content)

# Step 3: Extract structured data
from pydantic import BaseModel

class UIElement(BaseModel):
    name: str
    type: str
    location: str

request = CompletionRequest(
    messages=[
        UserMessage(
            content="Extract UI elements from this screenshot",
            images=[str(image_path)]
        )
    ],
    model="gpt-4-vision",
    response_schema=UIElement
)

response = provider.complete(request)
element = response.structured_output
print(f"Element: {element.name} ({element.type})")
```
""")


def main():
    """Run all examples."""
    print("\n" + "🖼️  " * 20)
    print("SKYE - Multimodal Input Examples")
    print("🖼️  " * 20)
    
    try:
        image_from_url()
        image_from_file()
        image_from_base64()
        multiple_images()
        vision_models()
        image_analysis_workflow()
        
        print("\n" + "=" * 60)
        print("✅ Examples completed!")
        print("=" * 60)
        print("\nKey points:")
        print("  • Images can be from URLs, file paths, or base64")
        print("  • Skye handles format conversion automatically")
        print("  • Different providers support different vision models")
        print("  • Combine with structured outputs for data extraction")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
