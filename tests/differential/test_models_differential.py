"""Model adapters: built-in REST vs official SDK.

Scaffolding only. The model adapters in ``skye.models.llm`` are built-in REST adapters; the
vendor SDKs (dev group) are the oracle. Comparing them needs live credentials, so add per provider: same request through both, assert (a) text/usage/finish_reason
field-subset equality, (b) numeric epsilon on token counts/latency, (c) error-category
equivalence (auth/rate-limit/validation). Tests needing live credentials must skip when the
credential env var is absent.
"""

import pytest

pytestmark = pytest.mark.skip(reason="built-in REST adapters landed; SDK-vs-REST comparison needs live credentials (scaffold)")


@pytest.mark.parametrize("provider", ["openai", "anthropic", "bedrock", "google"])
def test_rest_vs_sdk_equivalence(provider):  # pragma: no cover
    raise NotImplementedError
