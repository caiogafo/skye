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
    """Basic completion using Bedrock."""
    print("=" * 60)
    print("AWS Bedrock - Basic Completion")
    print("=" * 60)
    
    try:
        client = nimbus.provider(
            "bedrock",
            region="us-east-1",
            model="anthropic.claude-3-sonnet-20240229-v1:0"
        )
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use Bedrock, install with: pip install nimbus[bedrock]")
        return
    
    messages = [
        SystemMessage("You are a helpful assistant."),
        UserMessage("What is the capital of France?"),
    ]
    
    response = client.complete(messages=messages, temperature=0.7, max_tokens=100)
    
    print("\nResponse:")
    print("  Text:", response.content)
    print("  Model:", response.model)
    print("  Tokens:", response.usage.total_tokens)
    print("  Finish reason:", response.finish_reason)


def multiple_models():
    """Run the same prompt on different models."""
    print("\n" + "=" * 60)
    print("AWS Bedrock - Multiple Models")
    print("=" * 60)
    
    client = nimbus.provider("bedrock", region="us-west-2")
    
    models = [
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "amazon.titan-text-express-v1",
    ]
    
    prompt = "What is artificial intelligence?"
    messages = [UserMessage(prompt)]
    
    print(f"\nPrompt: {prompt}")
    print("-" * 40)
    
    for model in models:
        print(f"\nModel: {model}")
        response = client.complete(messages=messages, model=model, max_tokens=80)
        print("  Response:", response.content[:80], "...")
        print("  Tokens:", response.usage.total_tokens)


def streaming_example():
    """Streaming completion using Bedrock."""
    print("\n" + "=" * 60)
    print("AWS Bedrock - Streaming")
    print("=" * 60)
    
    client = nimbus.provider("bedrock", region="us-east-1")
    
    messages = [UserMessage("Write a short story about a robot learning to paint.")]
    
    print("\nStreaming response:")
    print("-" * 40)
    
    for chunk in client.stream(
        messages=messages, model="anthropic.claude-3-sonnet-20240229-v1:0"
    ):
        print(chunk.delta, end="", flush=True)
    
    print("\n" + "-" * 40)


def lambda_deployment_example():
    """Lambda-friendly example."""
    print("\n" + "=" * 60)
    print("AWS Lambda Deployment Example")
    print("=" * 60)
    
    print("""
Example AWS Lambda handler using Nimbus:

```python
import nimbus
from nimbus.messages import UserMessage

client = nimbus.provider("bedrock", region="us-east-1")

def lambda_handler(event, context):
    messages = [UserMessage(event["prompt"])]
    
    response = client.complete(
        messages=messages,
        model="anthropic.claude-3-sonnet-20240229-v1:0"
    )
    
    return {
        "statusCode": 200,
        "body": response.content
    }
```

Deployment:
1. Create deployment package with nimbus (boto3 is pre-installed in Lambda)
2. Upload to Lambda
3. Set IAM permissions for Bedrock access
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
import nimbus

# Use specific AWS profile
client = nimbus.provider(
    "bedrock",
    region="us-east-1",
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
client = nimbus.provider("bedrock", region="us-east-1")
```
""")


def router_example():
    """Example using router for multi-region load balancing."""
    print("\n" + "=" * 60)
    print("AWS Bedrock - Router for Multi-Region")
    print("=" * 60)
    
    print("""
Use RouterRegistry for load balancing across regions:

```python
import nimbus
from nimbus import routes as rt
from nimbus.messages import UserMessage

# Define multi-region setup
registry = rt.RouterRegistry([
    rt.RouteConfig(
        alias="claude",
        targets=[
            rt.ModelTarget(
                model="anthropic.claude-3-sonnet-20240229-v1:0",
                provider="bedrock",
                region="us-east-1"
            ),
            rt.ModelTarget(
                model="anthropic.claude-3-sonnet-20240229-v1:0",
                provider="bedrock",
                region="us-west-2"
            ),
        ],
        strategy="round-robin"
    )
])

# Create client with router
client = nimbus.provider("bedrock", router=registry)

# Use alias - router handles region selection
response = client.complete(
    messages=[UserMessage("Hello")],
    model="claude"  # Routes to us-east-1 or us-west-2
)
```

Benefits:
- Automatic failover between regions
- Load balancing for better performance
- Single alias for multiple deployments
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
        router_example()
        
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
