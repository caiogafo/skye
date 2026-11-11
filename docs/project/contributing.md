---
title: "Contributing"
status: current
---

# Contributing

This page gets a development copy of Skye running and lists the checks a pull request must pass. The rules on licences,
dependencies and specs are in [CONTRIBUTING.md](https://github.com/ggiallo28/skye/blob/main/CONTRIBUTING.md).

## Set up

```bash
git clone https://github.com/ggiallo28/skye.git
cd skye
uv sync --group dev --group docs
```

Always run tools through `uv run` (`uv run pytest`, `uv run ruff`, `uv run mypy`, `uv run black`).

## Checks

| Command | What it checks | Time |
|---|---|---|
| `uv run pytest` | unit, docs, examples, budget and differential tests | a few minutes |
| `make check` | black, ruff and mypy in strict mode | under a minute |
| `make budget-fast` | dependency policy and import rules | a second |
| `make budget` | installs Skye in clean environments and measures size and import time | about a minute |
| `make differential` | built-in REST adapters against the vendor SDKs, on a local fake server | seconds |

A budget only goes down: see [Size and load budgets](budgets.md).

## Documentation

The site is MkDocs Material. Preview it locally:

```bash
uv run mkdocs serve
```

`uv run mkdocs build --strict` must pass, and `tests/docs` checks front matter, links and that every page is reachable. Code in a
page comes from `examples/` through snippets (`--8<-- "examples/..."`), so it runs in the tests; `.skye` blocks use the `skye`
language and must pass `skye check`.

## Specs and decisions

Design work is spec driven: requirements and decisions live in `.kiro/steering/` (`10-requirements.md`, `12-decisions.md`), and
each component has a spec in `.kiro/specs/`. A change of behaviour updates the spec in the same pull request. Open questions are
listed as open decisions in `12-decisions.md`.

## The Claude skill

The package ships a skill that teaches a model to use Skye (`src/skye/utils/claude_skill/skye/`). If a change touches the `skye`
command line, the `.skye` language, the router fields or the public functions of `skye.dsl`, update the matching reference in the
same pull request; `tests/unit/dsl/test_claude_skill.py` fails otherwise.
