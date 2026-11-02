"""Azure OpenAI Provider Example (Boto3-style Skye API).

This version demonstrates:
- Basic completion with Azure OpenAI
- Streaming responses
- Azure-specific configuration (endpoint, deployment)
- Simple client creation: create_provider("azure")
"""

import os
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage, SystemMessage


def basic_completion():
    """Basic completion using Azure OpenAI."""
    print("=" * 60)
    print("Azure OpenAI - Basic Completion")
    print("=" * 60)
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if not api_key or not endpoint:
        print("⚠️  Azure OpenAI credentials not set")
        print("   Set with:")
        print("   export AZURE_OPENAI_API_KEY='...'")
        print("   export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com'")
        return
    
    try:
        client = create_provider(
            "azure",
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-02-15-preview"
        )
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use Azure OpenAI, install with: pip install skyeai[azure]")
        return
    
    messages = [
        SystemMessage("You are a helpful assistant."),
        UserMessage("What is the capital of France?"),
    ]
    
    # Note: For Azure, model is your deployment name
    response = client.complete(
        messages=messages,
        model="gpt-4",  # Your Azure deployment name
        temperature=0.7,
        max_tokens=100,
    )
    
    print("\nResponse:")
    print("  Text:", response.content)
    print("  Model:", response.model)
    print("  Tokens:", response.usage.total_tokens)
    print("  Finish reason:", response.finish_reason)


def streaming_example():
    """Streaming completion using Azure OpenAI."""
    print("\n" + "=" * 60)
    print("Azure OpenAI - Streaming")
    print("=" * 60)
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if not api_key or not endpoint:
        print("⚠️  Azure OpenAI credentials not set")
        return
    
    client = create_provider(
        "azure",
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-02-15-preview"
    )
    
    messages = [UserMessage("Write a short poem about cloud computing")]
    
    print("\nStreaming response:")
    print("-" * 40)
    
    for chunk in client.stream(messages=messages, model="gpt-4"):
        print(chunk.delta, end="", flush=True)
    
    print("\n" + "-" * 40)


def multiple_deployments():
    """Example using different Azure deployments."""
    print("\n" + "=" * 60)
    print("Azure OpenAI - Multiple Deployments")
    print("=" * 60)
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if not api_key or not endpoint:
        print("⚠️  Azure OpenAI credentials not set")
        return
    
    client = create_provider(
        "azure",
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-02-15-preview"
    )
    
    # Different deployment names in your Azure resource
    deployments = [
        "gpt-4",
        "gpt-35-turbo",
    ]
    
    prompt = "What is artificial intelligence?"
    messages = [UserMessage(prompt)]
    
    print(f"\nPrompt: {prompt}")
    print("-" * 40)
    
    for deployment in deployments:
        print(f"\nDeployment: {deployment}")
        response = client.complete(messages=messages, model=deployment, max_tokens=80)
        print("  Response:", response.content[:80], "...")
        print("  Tokens:", response.usage.total_tokens)


def configuration_example():
    """Example showing Azure configuration options."""
    print("\n" + "=" * 60)
    print("Azure OpenAI - Configuration")
    print("=" * 60)
    
    print("""
Azure OpenAI requires specific configuration:

```python
from skye.models.registry import provider as create_provider

client = create_provider(
    "azure",
    api_key="your-api-key",
    azure_endpoint="https://your-resource.openai.azure.com",
    api_version="2024-02-15-preview"
)

# The model parameter is your deployment name
response = client.complete(
    messages=[UserMessage("Hello")],
    model="gpt-4"  # Your deployment name in Azure
)
```

Environment variables:
```bash
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
```
""")


def main():
    """Run all examples."""
    print("\n" + "☁️  " * 20)
    print("SKYE - Azure OpenAI Provider Examples")
    print("☁️  " * 20)
    
    try:
        basic_completion()
        streaming_example()
        multiple_deployments()
        configuration_example()
        
        print("\n" + "=" * 60)
        print("✅ Examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Installed skyeai[azure]: pip install skyeai[azure]")
        print("  2. Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")
        print("  3. Created deployments in your Azure OpenAI resource")


if __name__ == "__main__":
    main()
