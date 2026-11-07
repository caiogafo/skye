"""The router examples were converted from YAML to ``.skye`` once; this keeps the proof that nothing
the router uses was lost.

``tests/fixtures/legacy_router_yaml/*.json`` hold the old YAML files, parsed, byte for byte as data.
The router built from each
of them (``ModelRouter.from_config_dict``) must equal the router built from the new ``.skye`` file
in ``examples/routing`` on
every field the router reads: routes, targets, strategies, fallback chains, retry and allowed-fails
policies, cooldown and
pre-call checks. Not compared, because the router never reads them (owner decision, noted for
version 2): ``priority`` and
``cost_per_1k_*_tokens`` of a target.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from skye.base.dsl import build, parse_duration
from skye.router import ModelRouter

ROOT = Path(__file__).resolve().parents[3]
LEGACY = ROOT / "tests" / "fixtures" / "legacy_router_yaml"
EXAMPLES = ROOT / "examples" / "routing"
CASES = [("router_config", "main"), ("router_config_simple", "simple")]
DROPPED_TARGET_FIELDS = ("priority", "cost_per_1k_prompt_tokens", "cost_per_1k_completion_tokens")


def _set_env(monkeypatch, text: str) -> None:
    for name in set(re.findall(r"\$\{(\w+)\}", text)):
        monkeypatch.setenv(name, f"value-of-{name}")


def _fields(target) -> dict:
    """The fields of a target, without the dropped ``priority`` and ``cost_per_1k_*`` of the old
    YAML (the router never read them).
    """
    fields = target.model_dump() if hasattr(target, "model_dump") else dict(vars(target))
    extras = fields.pop("extras", {})
    assert set(extras) <= set(DROPPED_TARGET_FIELDS), extras
    for name in DROPPED_TARGET_FIELDS:
        fields.pop(name, None)
    return fields


def _used(router: ModelRouter) -> dict:
    """Every field the router reads, in a comparable form."""
    return {
        "strategy": router.strategy.value,
        "cooldown_seconds": router.cooldown_seconds,
        "pre_call_checks": router.pre_call_checks_enabled,
        "routes": {
            alias: {
                "strategy": route.strategy.value,
                "fallback_on_error": route.fallback_on_error,
                "targets": [_fields(t) for t in route.targets],
            }
            for alias, route in router.aliases.items()
        },
        "fallbacks": {k: list(v) for k, v in router.fallbacks.items()},
        "retry_policy": dict(router.retry_policy),
        "allowed_fails_policy": dict(router.allowed_fails_policy),
        "config": router.to_config(include_secrets=True),
    }


@pytest.mark.parametrize(("stem", "label"), CASES)
def test_the_skye_router_equals_the_old_yaml_router(stem, label, monkeypatch):
    old = json.loads((LEGACY / f"{stem}.json").read_text(encoding="utf-8"))
    _set_env(monkeypatch, json.dumps(old))
    before = ModelRouter.from_config_dict(old)
    after = ModelRouter.from_file(EXAMPLES / f"{stem}.skye", name=label)
    assert _used(after) == _used(before)
    assert _used(after)["routes"], "the comparison must cover real routes"


@pytest.mark.parametrize(("stem", "label"), CASES)
def test_the_fields_the_language_reads_are_kept(stem, label):
    """Retry delays and backoff are not applied by the router yet, but the language holds them as
    the YAML did.
    """
    old = json.loads((LEGACY / f"{stem}.json").read_text(encoding="utf-8"))
    spec = build(
        (EXAMPLES / f"{stem}.skye").read_text(encoding="utf-8"),
        filename=str(EXAMPLES / f"{stem}.skye"),
    ).router(label)
    policies = {p.error_type: p for p in spec.retry_policies}
    assert set(policies) == {p["error_type"] for p in old["retry_policies"]}
    for entry in old["retry_policies"]:
        policy = policies[entry["error_type"]]
        assert policy.max_retries == entry["max_retries"]
        assert policy.exponential_backoff == entry.get("exponential_backoff", False)
        if "retry_after_seconds" in entry:
            assert parse_duration(policy.retry_after) == entry["retry_after_seconds"]


@pytest.mark.parametrize(("stem", "label"), CASES)
def test_only_the_unread_target_fields_were_dropped(stem, label):
    old = json.loads((LEGACY / f"{stem}.json").read_text(encoding="utf-8"))
    spec = build(
        (EXAMPLES / f"{stem}.skye").read_text(encoding="utf-8"),
        filename=str(EXAMPLES / f"{stem}.skye"),
    ).router(label)
    assert [r.alias for r in spec.routes] == [r["alias"] for r in old["routes"]]
    declared = {name for r in old["routes"] for t in r["targets"] for name in t}
    assert declared - set(DROPPED_TARGET_FIELDS) <= {
        "model",
        "provider",
        "api_key",
        "api_base",
        "api_version",
        "region",
        "tpm",
        "rpm",
        "weight",
        "tags",
        "metadata",
    }
