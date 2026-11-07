"""Anthropic itself: the Anthropic endpoint and its provider label.

The wire format is shared with every compatible endpoint (``anthropic_compatible.py``); this
module holds only what is specific to Anthropic.

Example:
    >>> from skye.models.llm.anthropic import AnthropicProvider
    >>> provider = AnthropicProvider(api_key="sk-ant-...")
    >>> response = provider.complete(request)  # doctest: +SKIP
"""

from skye.models.llm.anthropic_compatible import AnthropicCompatibleProvider


class AnthropicProvider(AnthropicCompatibleProvider):
    """Anthropic: default endpoint ``api.anthropic.com`` and the label ``anthropic``.

    Args:
        api_key: Anthropic API key
        api_base: Optional custom API base URL
        timeout: Seconds before a call fails (default 60)
    """

    provider_name = "anthropic"
    default_api_base = "https://api.anthropic.com"


__all__ = ["AnthropicProvider"]
