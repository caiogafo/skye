"""A serverless handler: create the client once, outside the handler, so a warm invocation pays nothing.

Skye is built for serverless architectures, where the size of the library and its cold start make a difference. The core imports only
the standard library; a provider is called over REST with the standard library, so nothing else is shipped. This file shows the shape
of a handler (written for AWS Lambda, but any serverless runtime works the same way).
"""

import os

import skye
from skye import UserMessage

# Created at cold start, reused by every warm invocation. Credentials come from the provider's standard variables.
CLIENT = skye.provider("bedrock", region=os.getenv("AWS_REGION", "us-east-1"))
MODEL = os.getenv("MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")


def handler(event: dict, context: object = None) -> dict:
    response = CLIENT.complete(messages=[UserMessage(content=event["prompt"])], model=MODEL)
    return {"response": response.content}


if __name__ == "__main__":
    print(handler({"prompt": "Say hello in one word"}))
