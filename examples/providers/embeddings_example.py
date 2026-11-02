"""Embedding Providers Example.

This example demonstrates how to use embedding providers with Skye.

Features shown:
- OpenAI embeddings (text-embedding-3-small)
- AWS Bedrock embeddings (Titan)
- Google embeddings (textembedding-gecko)
- Single text encoding
- Batch encoding
- Async encoding
- Similarity calculations

Usage:
    python embeddings_example.py

Requirements:
    - Set OPENAI_API_KEY for OpenAI examples
    - Configure AWS credentials for Bedrock examples
    - Set GOOGLE_CLOUD_PROJECT for Google examples
"""

import asyncio
import math
import os

from skye.models.registry import provider as create_provider


def openai_embeddings():
    """OpenAI embeddings example using text-embedding-3-small."""
    print("=" * 60)
    print("OpenAI Embeddings (text-embedding-3-small)")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        # Use the modern create_provider() interface
        embedder = create_provider(
            "openai",
            model="text-embedding-3-small",
            api_key=api_key,
            provider_type="embedding"
        )
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use OpenAI embeddings, install with: pip install skyeai[openai]")
        return
    
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Python is a popular programming language"
    ]
    
    print(f"\nEncoding {len(texts)} texts...")
    print("-" * 40)
    
    try:
        embeddings = embedder.encode_batch(texts)
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"✓ Vector dimension: {embedder.get_vector_dimension()}")
        print(f"✓ First embedding (first 5 values): {embeddings[0][:5]}")
        
        # Calculate similarity between first two texts
        similarity = cosine_similarity(embeddings[0], embeddings[1])
        print(f"✓ Similarity between text 1 and 2: {similarity:.4f}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def bedrock_embeddings():
    """Bedrock embeddings example using Titan Embeddings."""
    print("\n" + "=" * 60)
    print("AWS Bedrock Embeddings (Titan)")
    print("=" * 60)
    
    try:
        embedder = create_provider(
            "bedrock",
            model="amazon.titan-embed-text-v1",
            region_name="us-east-1",
            provider_type="embedding"
        )
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use Bedrock embeddings, install with: pip install skyeai[bedrock]")
        return
    
    texts = [
        "Cloud computing enables scalable infrastructure",
        "Serverless computing reduces operational overhead"
    ]
    
    print(f"\nEncoding {len(texts)} texts with Bedrock...")
    print("-" * 40)
    
    try:
        embeddings = embedder.encode_batch(texts)
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"✓ Vector dimension: {embedder.get_vector_dimension()}")
        print(f"✓ First embedding (first 5 values): {embeddings[0][:5]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. AWS credentials configured")
        print("  2. Access to Bedrock embeddings")


def google_embeddings():
    """Google embeddings example."""
    print("\n" + "=" * 60)
    print("Google Embeddings")
    print("=" * 60)
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("⚠️  GOOGLE_CLOUD_PROJECT environment variable not set")
        return
    
    try:
        embedder = create_provider(
            "google",
            model="textembedding-gecko@003",
            project_id=project_id,
            location="us-central1",
            provider_type="embedding"
        )
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use Google embeddings, install with: pip install skyeai[google]")
        return
    
    texts = [
        "Natural language processing is fascinating",
        "Deep learning powers modern AI systems"
    ]
    
    print(f"\nEncoding {len(texts)} texts with Google...")
    print("-" * 40)
    
    try:
        embeddings = embedder.encode_batch(texts)
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"✓ Vector dimension: {embedder.get_vector_dimension()}")
        print(f"✓ First embedding (first 5 values): {embeddings[0][:5]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Google Cloud credentials configured")
        print("  2. Google API enabled")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = math.sqrt(sum(x ** 2 for x in a))
    magnitude_b = math.sqrt(sum(x ** 2 for x in b))
    return dot_product / (magnitude_a * magnitude_b)


def single_text_encoding():
    """Example of encoding a single text."""
    print("\n" + "=" * 60)
    print("Single Text Encoding")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        embedder = create_provider(
            "openai",
            model="text-embedding-3-small",
            api_key=api_key,
            provider_type="embedding"
        )
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    text = "This is a single text to encode"
    
    print(f"\nEncoding: '{text}'")
    print("-" * 40)
    
    try:
        embedding = embedder.encode(text)
        
        print(f"✓ Generated embedding")
        print(f"✓ Vector dimension: {len(embedding)}")
        print(f"✓ First 5 values: {embedding[:5]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def async_encoding():
    """Async encoding example."""
    print("\n" + "=" * 60)
    print("Async Encoding")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        embedder = create_provider(
            "openai",
            model="text-embedding-3-small",
            api_key=api_key,
            provider_type="embedding"
        )
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    texts = [
        "Async operations are non-blocking",
        "Concurrency improves performance"
    ]
    
    print(f"\nAsync encoding {len(texts)} texts...")
    print("-" * 40)
    
    try:
        embeddings = await embedder.aencode_batch(texts)
        
        print(f"✓ Generated {len(embeddings)} embeddings asynchronously")
        print(f"✓ First embedding (first 5 values): {embeddings[0][:5]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def batch_processing():
    """Example of batch processing with embeddings."""
    print("\n" + "=" * 60)
    print("Batch Processing")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        embedder = create_provider(
            "openai",
            model="text-embedding-3-small",
            api_key=api_key,
            provider_type="embedding"
        )
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Simulate a large batch of documents
    documents = [
        "Document 1: Introduction to machine learning",
        "Document 2: Deep learning fundamentals",
        "Document 3: Natural language processing",
        "Document 4: Computer vision applications",
        "Document 5: Reinforcement learning basics",
    ]
    
    print(f"\nProcessing {len(documents)} documents...")
    print("-" * 40)
    
    try:
        # Process in batches
        batch_size = 2
        all_embeddings = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            print(f"Processing batch {i // batch_size + 1}...")
            
            embeddings = embedder.encode_batch(batch)
            all_embeddings.extend(embeddings)
        
        print(f"\n✓ Processed {len(all_embeddings)} documents")
        print(f"✓ Vector dimension: {embedder.get_vector_dimension()}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "📊 " * 20)
    print("SKYE - Embedding Providers Examples")
    print("📊 " * 20)
    print("\nThis example demonstrates various embedding providers and operations.")
    print("Set the appropriate API keys/credentials as environment variables:")
    print("  - OPENAI_API_KEY for OpenAI")
    print("  - AWS credentials for Bedrock")
    print("  - GOOGLE_CLOUD_PROJECT for Google")
    
    try:
        openai_embeddings()
        bedrock_embeddings()
        google_embeddings()
        single_text_encoding()
        batch_processing()
        
        # Run async example
        print("\n" + "=" * 60)
        print("Running async example...")
        print("=" * 60)
        asyncio.run(async_encoding())
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
