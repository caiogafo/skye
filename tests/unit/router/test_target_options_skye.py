"""``options`` of a target in a ``.skye`` router (owner decision of 2026-11-11, router task 7.6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from skye.base.dsl import build, to_text
from skye.router import ModelRouter

ROUTER = """\
router "app" {
  route "chat" {
    target {
      model = "gemini-2.5-flash"
      provider = "google"
      options = { project_id = "my-project", location = "europe-west1", token = env.GOOGLE_TOKEN }
    }
  }
}
"""


def test_options_parse_and_reach_the_model_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_TOKEN", "secret")
    path = tmp_path / "app.skye"
    path.write_text(ROUTER, encoding="utf-8")
    router = ModelRouter.from_file(str(path))
    target = router.get_route("chat").targets[0]
    assert target.options["project_id"] == "my-project"
    assert target.options["location"] == "europe-west1"


def test_options_round_trip_and_keep_env_references() -> None:
    document = build(ROUTER)
    assert not document.diagnostics
    assert document.routers[0].routes[0].targets[0].options["token"] == "${GOOGLE_TOKEN}"
    text = to_text(document)
    assert "options = {" in text and "token = env.GOOGLE_TOKEN" in text
    assert "secret" not in text
    again = build(text)
    assert (
        again.routers[0].routes[0].targets[0].options
        == document.routers[0].routes[0].targets[0].options
    )


def test_options_in_a_shorthand_entry() -> None:
    text = (
        'router "r" { route "x" = '
        '[{ model = "google/gemini-2.5-flash", options = { location = "us" } }] }'
    )
    document = build(text)
    assert not document.diagnostics
    assert document.routers[0].routes[0].targets[0].options == {"location": "us"}
