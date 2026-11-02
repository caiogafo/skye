"""Multimodal content examples for Skye Prompts Support.

This script demonstrates multimodal content support using the
comprehensive agent templates and enhanced prompt system.
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from skye.prompts import MockPromptBuilder


def basic_image_content():
    """Demonstrate basic image content support."""
    print("=== Basic Image Content ===")
    
    builder = MockPromptBuilder()
    
    # Register template for image analysis
    builder.register_template(
        name="image_analysis",
        template="""Analyze the following image and describe what you see.

Image: {image}

Description:"""
    )
    
    # Configure image content
    builder.add_image_content("image_analysis", "image", image_format="url")
    
    # Render with image URL
    messages = builder.render("image_analysis", {
        "image": "https://example.com/sample-image.jpg"
    })
    
    print(f"Image analysis prompt:\n{messages[0].content}")
    
    # Check metadata
    metadata = builder.get_template_metadata("image_analysis")
    print(f"Content types: {metadata['content_types']}")
    print()


def multiple_image_formats():
    """Demonstrate different image format support."""
    print("=== Multiple Image Formats ===")
    
    builder = MockPromptBuilder()
    
    # Register template for image comparison
    builder.register_template(
        name="compare_images",
        template="""Compare these two images and identify the differences.

Image 1: {image1}
Image 2: {image2}

Differences:"""
    )
    
    # Configure different image formats
    builder.add_image_content("compare_images", "image1", image_format="url")
    builder.add_image_content("compare_images", "image2", image_format="base64")
    
    # Render with different formats
    messages = builder.render("compare_images", {
        "image1": "https://example.com/image1.jpg",
        "image2": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
    })
    
    print(f"Image comparison prompt:\n{messages[0].content}")
    print()


def multimodal_content_types():
    """Demonstrate multiple content types in one template."""
    print("=== Multiple Content Types ===")
    
    builder = MockPromptBuilder()
    
    # Register template for multimedia analysis
    builder.register_template(
        name="multimedia_analysis",
        template="""Analyze the following multimedia content:

Text: {text_content}
Image: {image_content}
Audio: {audio_content}
Video: {video_content}

Provide a comprehensive analysis covering all modalities:"""
    )
    
    # Configure multiple content types
    builder.add_multimodal_content("multimedia_analysis", {
        "text_content": "text",
        "image_content": "image",
        "audio_content": "audio",
        "video_content": "video"
    })
    
    # Render with multimodal content
    messages = builder.render("multimedia_analysis", {
        "text_content": "This is a sample text document about AI.",
        "image_content": "https://example.com/ai-diagram.png",
        "audio_content": "https://example.com/ai-lecture.mp3",
        "video_content": "https://example.com/ai-demo.mp4"
    })
    
    print(f"Multimedia analysis prompt:\n{messages[0].content}")
    
    # Check content configuration
    metadata = builder.get_template_metadata("multimedia_analysis")
    print(f"Configured content types: {metadata['content_types']}")
    print()


def structured_output_schema():
    """Demonstrate structured output with Pydantic-like schemas."""
    print("=== Structured Output Schema ===")
    
    builder = MockPromptBuilder()
    
    # Register template for entity extraction
    builder.register_template(
        name="extract_entities",
        template="""Extract named entities from the following text.

Text: {text}

{output_instructions}

Entities:"""
    )
    
    # Define output schema (mock Pydantic model)
    class EntitySchema:
        def __init__(self):
            self.name = "EntitySchema"
            self.fields = {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "label": {"type": "string"},
                            "start": {"type": "integer"},
                            "end": {"type": "integer"}
                        }
                    }
                }
            }
    
    # Set output schema
    builder.set_output_schema("extract_entities", EntitySchema())
    
    # Get output instructions
    instructions = builder.get_output_instructions("extract_entities")
    
    # Render with schema instructions
    messages = builder.render("extract_entities", {
        "text": "Apple Inc. was founded by Steve Jobs in Cupertino.",
        "output_instructions": instructions
    })
    
    print(f"Entity extraction with schema:\n{messages[0].content}")
    print()


def json_schema_output():
    """Demonstrate JSON schema for structured output."""
    print("=== JSON Schema Output ===")
    
    builder = MockPromptBuilder()
    
    # Register template for sentiment analysis with confidence
    builder.register_template(
        name="sentiment_with_confidence",
        template="""Analyze the sentiment of the following text and provide a confidence score.

Text: "{text}"

{output_instructions}

Analysis:"""
    )
    
    # Define JSON schema
    json_schema = {
        "type": "object",
        "properties": {
            "sentiment": {
                "type": "string",
                "enum": ["positive", "negative", "neutral"]
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0
            },
            "reasoning": {
                "type": "string",
                "description": "Explanation for the sentiment classification"
            }
        },
        "required": ["sentiment", "confidence"]
    }
    
    # Set JSON schema
    builder.set_output_schema("sentiment_with_confidence", json_schema)
    
    # Get formatted instructions
    instructions = builder.get_output_instructions("sentiment_with_confidence")
    
    # Render with schema
    messages = builder.render("sentiment_with_confidence", {
        "text": "I absolutely love this new feature!",
        "output_instructions": instructions
    })
    
    print(f"Sentiment analysis with JSON schema:\n{messages[0].content}")
    print()


def multimodal_with_structured_output():
    """Demonstrate combining multimodal content with structured output."""
    print("=== Multimodal + Structured Output ===")
    
    builder = MockPromptBuilder()
    
    # Register template for image captioning with metadata
    builder.register_template(
        name="image_caption_structured",
        template="""Generate a detailed caption for the following image.

Image: {image}
Context: {context}

{output_instructions}

Caption Analysis:"""
    )
    
    # Configure image content
    builder.add_image_content("image_caption_structured", "image", image_format="url")
    
    # Define structured output schema
    caption_schema = {
        "type": "object",
        "properties": {
            "caption": {
                "type": "string",
                "description": "Main caption describing the image"
            },
            "objects": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of objects detected in the image"
            },
            "scene": {
                "type": "string",
                "description": "Overall scene or setting"
            },
            "mood": {
                "type": "string",
                "enum": ["happy", "sad", "neutral", "energetic", "calm"]
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0
            }
        },
        "required": ["caption", "objects", "scene"]
    }
    
    builder.set_output_schema("image_caption_structured", caption_schema)
    
    # Get output instructions
    instructions = builder.get_output_instructions("image_caption_structured")
    
    # Render with multimodal content and structured output
    messages = builder.render("image_caption_structured", {
        "image": "https://example.com/beach-sunset.jpg",
        "context": "This image was taken during a vacation",
        "output_instructions": instructions
    })
    
    print(f"Multimodal structured output:\n{messages[0].content}")
    print()


def content_validation_example():
    """Demonstrate content validation and error handling."""
    print("=== Content Validation ===")
    
    builder = MockPromptBuilder()
    
    # Register template with strict content requirements
    builder.register_template(
        name="validated_analysis",
        template="""Analyze the provided content.

Image: {image}
Text: {text}

Analysis:"""
    )
    
    # Configure content with validation
    builder.add_multimodal_content("validated_analysis", {
        "image": "image",
        "text": "text"
    })
    
    # Test with valid content
    try:
        messages = builder.render("validated_analysis", {
            "image": "https://example.com/valid-image.jpg",
            "text": "This is valid text content."
        })
        print("✓ Valid content rendered successfully")
        print(f"Content: {messages[0].content[:100]}...")
    except Exception as e:
        print(f"✗ Error with valid content: {e}")
    
    # Test validation through template validation
    validation = builder.validate_template("validated_analysis")
    print(f"Template validation: {validation}")
    print()


def main():
    """Run all multimodal content examples."""
    print("Skye Prompts Support - Multimodal Content Examples")
    print("=" * 58)
    
    basic_image_content()
    multiple_image_formats()
    multimodal_content_types()
    structured_output_schema()
    json_schema_output()
    multimodal_with_structured_output()
    content_validation_example()
    
    print("All multimodal content examples completed successfully!")


if __name__ == "__main__":
    main()