"""AWS Bedrock Provider Example (Boto3-style Skye API).

This version demonstrates:
- Basic completion with messages (SystemMessage, UserMessage)
- Multiple model support (Claude, Titan)
- Streaming responses
- AWS region/profile configuration
- Lambda-friendly design
- Boto3-like provider creation: skye.provider("bedrock")
"""

import skye
from skye import UserMessage, SystemMessage


def basic_completion():
    """Basic completion using Bedrock."""
    print("=" * 60)
    print("AWS Bedrock - Basic Completion")
    print("=" * 60)
    
    try:
        client = skye.provider(
            "bedrock",
            region="us-east-1",
            model="anthropic.claude-3-sonnet-20240229-v1:0"
        )
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use Bedrock, install with: pip install skyeai[bedrock]")
        return
    
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="What is the capital of France?"),
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
    
    client = skye.provider("bedrock", region="us-west-2")
    
    models = [
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "amazon.titan-text-express-v1",
    ]
    
    prompt = "What is artificial intelligence?"
    messages = [UserMessage(content=prompt)]
    
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
    
    client = skye.provider("bedrock", region="us-east-1")
    
    messages = [UserMessage(content="Write a short story about a robot learning to paint.")]
    
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
    
    print("\nExample AWS Lambda handler using Skye:")
    print("-" * 40)
    print("""
import skye
from skye import UserMessage

# Initialize client once (reused across invocations)
client = skye.provider("bedrock", region="us-east-1")

def lambda_handler(event, context):
    '''Handle Lambda invocation.'''
    try:
        prompt = event.get("prompt", "Hello")
        messages = [UserMessage(content=prompt)]
        
        response = client.complete(
            messages=messages,
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            max_tokens=500
        )
        
        return {
            "statusCode": 200,
            "body": {
                "response": response.content,
                "model": response.model,
                "tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }
""")
    
    print("\nDeployment Steps:")
    print("  1. Create deployment package with skye")
    print("  2. Upload to Lambda (boto3 is pre-installed)")
    print("  3. Set IAM permissions for Bedrock access")
    print("  4. Configure environment variables if needed")
    print("  5. Test with sample event")
    
    print("\nSample Lambda Event:")
    print('  {"prompt": "What is AWS Bedrock?"}')


def aws_profile_example():
    """Example using AWS profiles."""
    print("\n" + "=" * 60)
    print("AWS Bedrock - Using AWS Profiles")
    print("=" * 60)
    
    print("\nMethod 1: Using AWS Profile in Code")
    print("-" * 40)
    print("""
import skye

# Use specific AWS profile
client = skye.provider(
    "bedrock",
    region="us-east-1",
    profile_name="my-profile"
)

response = client.complete(
    messages=[UserMessage(content="Hello")],
    model="anthropic.claude-3-sonnet-20240229-v1:0"
)
""")
    
    print("\nMethod 2: Using Environment Variables")
    print("-" * 40)
    print("""
# Set environment variables
export AWS_PROFILE=my-profile
export AWS_REGION=us-east-1

# Then in Python
import skye

client = skye.provider("bedrock", region="us-east-1")
""")
    
    print("\nMethod 3: Using AWS Credentials")
    print("-" * 40)
    print("""
# Set environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1

# Then in Python
import skye

client = skye.provider("bedrock", region="us-east-1")
""")
    
    print("\nProfile Configuration (~/.aws/config):")
    print("-" * 40)
    print("""
[profile my-profile]
region = us-east-1
output = json

[profile my-profile-west]
region = us-west-2
output = json
""")


def router_example():
    """Example using router for multi-region load balancing."""
    print("\n" + "=" * 60)
    print("AWS Bedrock - Router for Multi-Region Load Balancing")
    print("=" * 60)
    
    try:
        from skye.router import ModelRouter, ModelTarget, RouteConfig
        from skye.router import RoutingStrategy
        
        # Define multi-region setup with ModelRouter
        router = ModelRouter(
            routes=[
                RouteConfig(
                    alias="claude",
                    targets=[
                        ModelTarget(
                            model="anthropic.claude-3-sonnet-20240229-v1:0",
                            provider="bedrock",
                            region="us-east-1",
                            tpm=100000,
                            rpm=500,
                            tags=["us-east-1"]
                        ),
                        ModelTarget(
                            model="anthropic.claude-3-sonnet-20240229-v1:0",
                            provider="bedrock",
                            region="us-west-2",
                            tpm=100000,
                            rpm=500,
                            tags=["us-west-2"]
                        ),
                    ],
                    strategy=RoutingStrategy.ROUND_ROBIN
                )
            ],
            strategy=RoutingStrategy.ROUND_ROBIN,
            cooldown_seconds=60.0,
        )
        
        print("\nRouter Configuration:")
        print(f"  Aliases: {router.list_aliases()}")
        print(f"  Strategy: {router.strategy.value}")
        
        # Show route details
        route = router.get_route("claude")
        if route:
            print(f"  Targets for 'claude': {len(route.targets)}")
            for i, target in enumerate(route.targets, 1):
                print(f"    {i}. {target.model} in {target.region}")
        
        print("\nBenefits:")
        print("  ✓ Automatic failover between regions")
        print("  ✓ Load balancing for better performance")
        print("  ✓ Single alias for multiple deployments")
        print("  ✓ Health tracking per region")
        print("  ✓ Rate limiting per region")
        
        print("\nUsage:")
        print("  # Router automatically selects best region")
        print("  response = client.complete(")
        print("      messages=[UserMessage(content='Hello')],")
        print("      model='claude'  # Routes to us-east-1 or us-west-2")
        print("  )")
        
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use ModelRouter, install with: pip install skyeai")
        return


def main():
    """Run all examples."""
    print("\n" + "🏔️  " * 20)
    print("SKYE - AWS Bedrock Provider Examples")
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
        print("  1. Installed skyeai[bedrock]: pip install skyeai[bedrock]")
        print("  2. AWS credentials configured")
        print("  3. Access to Bedrock models")


if __name__ == "__main__":
    main()
