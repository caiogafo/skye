"""Quick start: create a client with one call and ask a question.

``skye.provider(name, **config)`` is the one way to create the client of a provider, in the style of ``boto3.client``. The same
line works for every provider; only the name and the configuration change.

With OPENAI_API_KEY set the example calls OpenAI; without a key it runs a scripted client and says so.
"""

from skye import UserMessage

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402


def main() -> None:
    client = get_client("openai")  # skye.provider("openai", api_key=...) when the key is set

    response = client.complete(
        messages=[UserMessage(content="Hello, world!")],
        model="gpt-4",
        temperature=0.7,
    )
    print(response.content)

    # The same call for another provider; with no api_key the key comes from the provider's standard variable:
    #   client = skye.provider("anthropic")                 # ANTHROPIC_API_KEY
    #   client = skye.provider("bedrock", region="us-east-1")  # AWS credentials; AWS_REGION when region is omitted


if __name__ == "__main__":
    main()
