"""AWS Bedrock Provider Example (Boto3-style Nimbus API).

This version demonstrates:
- Basic completion with messages (SystemMessage, UserMessage)
- Multiple model support (Claude, Titan)
- Streaming responses
- AWS region/profile configuration
- Lambda-friendly design
- Boto3-like provider creation: nimbus.provider("bedrock")
"""

import nimbus
from nimbus.messages import UserMessage, SystemMessage


def basic_completion():
    """Basic completion with Bedrock."""
    print("=" * 60)
    print("AWS Bedrock Basic Completion")
    print("=" * 60)
    
    try:
        provider = ProviderRegistry.get_model_provider(
            "bedrock",
            region_name="us-east-1"
        )
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use Bedrock, install with: pip install nimbus[bedrock]")
        return
    
    request = CompletionRequest(
        messages=[
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="What is the capital of France?")
        ],
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        temperature=0.7,
        max_tokens=100
    )
    
    print("\nRequest:")
    print(f"  Model: {request.model}")
    print(f"  Region: us-east-1")
    print(f"  Messages: {len(request.messages)}")
    
    try:
        response = provider.complete(request)
        
        print("\nResponse:")
        print(f"  Content: {response.content}")
        print(f"  Provider: {response.provider}")
        print(f"  Tokens used: {response.usage.total_tokens}")
        print(f"  Finish reason: {response.finish_reason}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. AWS credentials configured (AWS_PROFILE or AWS_ACCESS_KEY_ID)")
        print("  2. Access to Bedrock in your AWS account")
        print("  3. Model access enabled in Bedrock console")


def multiple_models():
    """Example with different Bedrock models."""
    print("\n" + "=" * 60)
    print("AWS Bedrock - Multiple Models")
    print("=" * 60)
    
    try:
        provider = ProviderRegistry.get_model_provider(
            "bedrock",
            region_name="us-west-2"
        )
    except ImportError:
        print("⚠️  Bedrock provider not available")
        return
    
    models = [
        ("anthropic.claude-3-sonnet-20240229-v1:0", "Claude 3 Sonnet"),
        ("anthropic.claude-3-haiku-20240307-v1:0", "Claude 3 Haiku"),
        ("amazon.titan-text-express-v1", "Amazon Titan"),
    ]
    
    prompt = "What is artificial intelligence?"
    
    print(f"\nPrompt: {prompt}")
    print("-" * 40)
    
    for model_id, model_name in models:
        print(f"\n{model_name}:")
        
        request = CompletionRequest(
            messages=[UserMessage(content=prompt)],
            model=model_id,
            max_tokens=100
        )
        
        try:
            response = provider.complete(request)
            print(f"  Response: {response.content[:80]}...")
            print(f"  Tokens: {response.usage.total_tokens}")
        except Exception as e:
            print(f"  ⚠️  Error: {str(e)[:60]}...")


def streaming_example():
    """Streaming completion with Bedrock."""
    print("\n" + "=" * 60)
    print("AWS Bedrock Streaming")
    print("=" * 60)
    
    try:
        provider = ProviderRegistry.get_model_provider(
            "bedrock",
            region_name="us-east-1"
        )
    except ImportError:
        print("⚠️  Bedrock provider not available")
        return
    
    request = CompletionRequest(
        messages=[
            UserMessage(content="Write a short story about a robot learning to paint")
        ],
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        stream=True
    )
    
    print("\nStreaming response:")
    print("-" * 40)
    
    try:
        for chunk in provider.stream(request):
            print(chunk.delta, end="", flush=True)
        print("\n" + "-" * 40)
    except Exception as e:
        print(f"\n❌ Error: {e}")


def lambda_deployment_example():
    """Example showing Lambda-friendly usage."""
    print("\n" + "=" * 60)
    print("AWS Lambda Deployment Example")
    print("=" * 60)
    
    print("""
In AWS Lambda, boto3 is pre-installed in the runtime.
You don't need to include it in your deployment package.

Example Lambda handler:

```python
from nimbus.completion import CompletionRequest
from nimbus.messages import UserMessage
from nimbus.providers import ProviderRegistry

def lambda_handler(event, context):
    # Bedrock provider works without boto3 in dependencies
    provider = ProviderRegistry.get_model_provider(
        "bedrock",
        region_name="us-east-1"
    )
    
    request = CompletionRequest(
        messages=[UserMessage(content=event['prompt'])],
        model="anthropic.claude-3-sonnet-20240229-v1:0"
    )
    
    response = provider.complete(request)
    
    return {
        'statusCode': 200,
        'body': response.content
    }
```

Deployment:
1. Create deployment package with nimbus (without boto3)
2. Upload to Lambda
3. Set environment variables if needed
4. Lambda runtime provides boto3 automatically
""")


def aws_profile_example():
    """Example using AWS profiles."""
    print("\n" + "=" * 60)
    print("AWS Bedrock - Using AWS Profiles")
    print("=" * 60)
    
    print("""
You can specify an AWS profile for Bedrock:

```python
from nimbus.providers import ProviderRegistry

# Use specific AWS profile
provider = ProviderRegistry.get_model_provider(
    "bedrock",
    region_name="us-east-1",
    profile_name="my-profile"
)
```

Or use environment variables:

```bash
export AWS_PROFILE=my-profile
export AWS_REGION=us-east-1
```

Then:

```python
provider = ProviderRegistry.get_model_provider(
    "bedrock",
    region_name="us-east-1"
)
```
""")


def main():
    """Run all examples."""
    print("\n" + "🏔️  " * 20)
    print("NIMBUS - AWS Bedrock Provider Examples")
    print("🏔️  " * 20)
    
    try:
        basic_completion()
        multiple_models()
        streaming_example()
        lambda_deployment_example()
        aws_profile_example()
        
        print("\n" + "=" * 60)
        print("✅ Examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Installed nimbus[bedrock]: pip install nimbus[bedrock]")
        print("  2. AWS credentials configured")
        print("  3. Access to Bedrock models")


if __name__ == "__main__":
    main()
