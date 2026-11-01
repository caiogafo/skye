"""Model adapters: built-in REST vs official SDK.

Scaffolding only. The model adapters in ``nimbus.models.llm`` have only the SDK path today,
so there is nothing to compare against; fake tests would prove nothing. When a REST adapter
lands, add per provider: same request through both, assert (a) text/usage/finish_reason
field-subset equality, (b) numeric epsilon on token counts/latency, (c) error-category
equivalence (auth/rate-limit/validation). Tests needing live credentials must skip when the
credential env var is absent.
"""

import pytest

pytestmark = pytest.mark.skip(reason="no built-in REST adapter yet")


@pytest.mark.parametrize("provider", ["openai", "anthropic", "bedrock", "google"])
def test_rest_vs_sdk_equivalence(provider):  # pragma: no cover
    raise NotImplementedError
