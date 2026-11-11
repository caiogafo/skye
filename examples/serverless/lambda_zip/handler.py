"""A complete AWS Lambda function: the handler that `build.sh` packs into a zip with Skye and nothing else.

The Lambda Python runtime already has everything Skye needs: the standard library. The function's role gives the AWS
credentials and Lambda sets AWS_REGION, so the code reads no key. The client is created once, at cold start, and reused by
every warm invocation. Set MODEL_ID to a Bedrock model or inference profile your account can call.
"""

import os

import skye
from skye import UserMessage

CLIENT = skye.provider("bedrock", region=os.environ.get("AWS_REGION", "us-east-1"))  # Lambda sets AWS_REGION
MODEL = os.environ.get("MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")


def handler(event: dict, context: object = None) -> dict:
    response = CLIENT.complete(messages=[UserMessage(content=event["prompt"])], model=MODEL)
    return {"answer": response.content, "tokens": response.usage.total_tokens}


if __name__ == "__main__":
    if os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE"):
        print(handler({"prompt": "Say hello in one word"}))
    else:
        print("No AWS credentials: set them (and AWS_REGION) to call Bedrock; on Lambda the function's role gives them.")
