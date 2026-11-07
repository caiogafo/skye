"""Cold start of the library: how long a fresh interpreter takes to get from nothing to a router ready to send a request.

Skye is built for serverless architectures, where the size of the library and its cold start make a difference. This test measures
the part of a cold start that the library controls: `import skye`, the router, one target and one request, with no network, in a
fresh interpreter, best of several runs. The limit is `[cold_start] max_cold_start_ms` in budgets.toml, which also explains why that
number is compatible with serverless (a thin Python function starts in 100 to 300 ms on AWS Lambda; an init of 500 to 2000 ms is
usually acceptable for an LLM application, whose model call takes seconds).

The bare `import skye` is checked separately (`[load] max_import_ms`); this test adds the router and the request, which is what a
handler does before its first call. It also checks that the cold path loads no provider SDK or optional library.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile

from tests.budget.measure import load_budgets

COLD_PATH = """
import json, sys, time
before = set(sys.modules)
t0 = time.perf_counter()
import skye
from skye.base.messages import UserMessage
from skye.base.completion import CompleteRequest
from skye.router import ModelRouter, ModelTarget, RouteConfig
from skye.base.interfaces.router import RoutingStrategy
router = ModelRouter(routes=[RouteConfig(alias="a", targets=[ModelTarget(model="gpt-4", provider="openai", api_key="k")], strategy=RoutingStrategy.ROUND_ROBIN)])
request = CompleteRequest(messages=[UserMessage(content="hi")], model="a")
elapsed = time.perf_counter() - t0
# only what the cold path itself loaded: a .pth file of an installed SDK pre-imports `google` at interpreter start-up
print(json.dumps({"ms": elapsed * 1000, "loaded": sorted({m.split(".")[0] for m in set(sys.modules) - before})}))
"""


def _run(runs: int) -> list[dict]:
    return [
        json.loads(subprocess.check_output([sys.executable, "-c", COLD_PATH], text=True, cwd=tempfile.gettempdir()))
        for _ in range(runs)
    ]


def test_cold_start_stays_below_the_serverless_limit() -> None:
    budget = load_budgets()["cold_start"]
    results = _run(budget["runs"])
    best = min(r["ms"] for r in results)
    assert best <= budget["max_cold_start_ms"], (
        f"cold start (import, router, request) takes {best:.0f} ms, over the limit of {budget['max_cold_start_ms']} ms "
        f"(target {budget['target_cold_start_ms']} ms). Move the heavy import behind a function, or drop the dependency."
    )


def test_the_cold_path_loads_no_provider_sdk_or_optional_library() -> None:
    forbidden = set(load_budgets()["load"]["forbidden_at_import"]) - set(load_budgets()["load"]["known_leaks"])
    loaded = set(_run(1)[0]["loaded"])
    assert not (forbidden & loaded), f"the cold path imports {sorted(forbidden & loaded)}"


def test_the_target_is_not_above_the_limit() -> None:
    budget = load_budgets()["cold_start"]
    assert budget["target_cold_start_ms"] <= budget["max_cold_start_ms"]
