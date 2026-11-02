---
title: "Lazy loading and AWS Lambda deployment"
status: current
last_updated: 2026-11-02
---

## Lazy Loading and Optional Dependencies

Skye uses lazy loading to defer importing provider SDKs until they're actually used. This means:

1. **Minimal startup overhead**: Only import what you use
2. **Optional dependencies**: Install only the providers you need
3. **Lambda-friendly**: Bedrock works in AWS Lambda without boto3 as a dependency (it's pre-installed)

```python
from skye.models.registry import provider as create_provider

# This doesn't import OpenAI SDK until you actually use it
client = create_provider("openai", api_key="sk-...")

# SDK is imported here when complete() is called
response = client.complete(
    messages=[...],
    model="gpt-4"
)
```

## AWS Lambda Deployment

Skye is Lambda-friendly:

```python
# In AWS Lambda, boto3 is pre-installed
# No need to include it in your deployment package
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage

def lambda_handler(event, context):
    # Bedrock provider works without boto3 in dependencies
    client = create_provider("bedrock", region="us-east-1")
    
    response = client.complete(
        messages=[UserMessage(content=event['prompt'])],
        model="anthropic.claude-3-sonnet-20240229-v1:0"
    )
    
    return {"response": response.content}
```
