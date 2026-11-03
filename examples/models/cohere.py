"""Cohere as a language model (proposed-interface, guarded).

This example targets a planned interface that is not in ``src`` yet, so it guards and
returns before making any call that does not exist.

Today ``cohere`` is registered only as an *embedding* provider, not as a language
model provider, so ``skye.provider("cohere")`` for a completion is not available. The
intended shape, once a cohere language-model adapter ships, would read exactly like any
other provider::

    client = skye.provider("cohere", api_key=os.environ["COHERE_API_KEY"])
    response = client.complete(
        messages=[UserMessage(content="Hello")],
        model="command-r",
    )

The script detects that cohere is absent from the model provider registry and returns
without inventing a completion result.
"""

import skye  # noqa: F401  (imported so the example reads like user code)
from skye.models import ProviderRegistry


def main() -> None:
    model_providers = ProviderRegistry.list_model_providers()
    embedding_providers = ProviderRegistry.list_embedding_providers()

    print(f"Registered model providers    : {model_providers}")
    print(f"Registered embedding providers: {embedding_providers}")

    if "cohere" not in model_providers:
        print("\ncohere is not yet a language model provider in src, skipping the completion.")
        print("It is available as an embedding provider:")
        print('  embedder = skye.provider("cohere", provider_type="embedding")')
        return

    # Proposed shape, reachable only once a cohere language-model adapter ships.
    print("cohere model provider is present; the completion call shape would run here.")


if __name__ == "__main__":
    main()
