---
title: "Lazy loading and serverless deployment"
status: current
last_updated: 2026-11-02
---

## Lazy Loading and Optional Dependencies

Skye uses lazy loading to defer importing provider SDKs until they're actually used. This means:

1. **Minimal startup overhead**: Only import what you use
2. **Optional dependencies**: Install only the providers you need
3. **Serverless-friendly**: Bedrock needs no boto3 at all (the SigV4 signer is in the standard library), so nothing extra is shipped

```python
import skye

# This doesn't import OpenAI SDK until you actually use it
client = skye.provider("openai", api_key="sk-...")

# SDK is imported here when complete() is called
response = client.complete(
    messages=[...],
    model="gpt-4"
)
```

## Serverless deployment

Skye is built for serverless architectures, where the size of the library and its cold start make a difference. A user installs only the extras they need; nothing forces a third-party library. Example on AWS Lambda:

```python
# Bedrock is called over REST with the standard library: no boto3, no SDK to ship
import skye
from skye import UserMessage

def lambda_handler(event, context):
    # Bedrock provider works without boto3 in dependencies
    client = skye.provider("bedrock", region="us-east-1")
    
    response = client.complete(
        messages=[UserMessage(content=event['prompt'])],
        model="anthropic.claude-3-sonnet-20240229-v1:0"
    )
    
    return {"response": response.content}
```
