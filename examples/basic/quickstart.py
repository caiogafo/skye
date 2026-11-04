"""Quick start: create a client with one call and ask a question.

``skye.provider(name, **config)`` is the one way to create the client of a provider, in the style of ``boto3.client``. The same
line works for every provider; only the name and the configuration change.

Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, or AWS credentials for Bedrock.
"""

import os

import skye
from skye import UserMessage


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set, skipping")
        return

    client = skye.provider("openai", api_key=api_key)

    response = client.complete(
        messages=[UserMessage(content="Hello, world!")],
        model="gpt-4",
        temperature=0.7,
    )
    print(response.content)

    # The same call for another provider (credentials come from the provider's standard variables):
    #   client = skye.provider("anthropic", api_key=os.environ["ANTHROPIC_API_KEY"])
    #   client = skye.provider("bedrock", region="us-east-1")


if __name__ == "__main__":
    main()
