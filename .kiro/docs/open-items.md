# Open items

Status on 2026-11-02, after the structure migration, the Nimbus → Skye rename and the stress-test fix.
Verified at that point: `tests` 1244 passed, 7 skipped, 1 xfailed, 1 xpassed; `make budget` 9 passed;
`make differential` 11 passed, 4 skipped.

## Owner actions (not doable from the repository)

- [ ] **Trademark.** Confirm the check of "Skye" in software (USPTO, TMview, WIPO; classes 9 and 42).
      Web search on 2026-11-02 (no registry checked) found conflicts: Skye AI LLC (skyeai.io, AI sales automation,
      claims its "Skye AI" marks in its terms of service; same name as the `skyeai` distribution), Skye by
      Signull Labs (funded AI iPhone app), sankhya-ai/Skye (open-source coding-agent orchestrator), plus unrelated
      uses (Tinubu Skye, Skye Virtual Agent, a sleep app, a shapes.inc chatbot). Still to do: registry search
      (USPTO, TMview, WIPO; classes 9 and 42) and a decision: keep the name, get legal advice, or pick another.
- [ ] **GitHub.** Rename the repository to match `skye`. The local folder is still `nimbus/core`.
- [ ] **Placeholder URLs.** `README.md` (`github.com/your-org/skye`) and `examples/README.md`
      (`github.com/skyeai/skye`, `support@skyeai.com`) are invented. Replace them with real ones.
- [ ] **PyPI token.** Replace the account-wide token with one limited to the `skyeai` project, and
      revoke the token that was pasted in a chat. `~/.pypirc` has a pypi.org token under `[testpypi]`
      too (use a test.pypi.org token there, or drop the section).
- [ ] **PyPI names.** `skyeai` 0.0.1 is a placeholder. `skye-ai` cannot be registered: PyPI blocks it as
      too similar to `skyeai`, which also protects it. Publish a real release under `skyeai` later.
- [ ] **Commit.** About 314 files are uncommitted (structure work, `auth`, REST adapters, `docs/`, rename,
      router fix). Suggested split: structure/auth/REST, router fix, rename, docs + wiki + specs.

## Decisions to take

- [ ] **`tiktoken`: keep, drop, or make pluggable?** It is optional (extra `openai`), used only to count tokens
      exactly for `gpt-*`/`o1-*`/`o3-*`; every other model, Claude included, uses the stdlib estimate
      (about 4 characters per token), and so do `gpt-*` when it is missing. Against it: compiled (Rust) wheel,
      downloads its vocabulary over the network on first use (a problem in Lambda), and the count is only an
      estimate for rate-limit checks (real usage comes back in provider responses). Options:
      1. keep it optional and add it to the dev group, so the 3 skipped tests in
         `tests/unit/utils/test_token_counter.py` run;
      2. drop it, stdlib estimate only;
      3. drop it and add `TokenCounter.register_tokenizer(prefix, encoder)`, so users who want exact counts plug
         `tiktoken` (or another tokenizer) in themselves. Recommended.
      If 2 or 3: remove `tiktoken` from the `openai` extra and the bundles in `pyproject.toml`, update
      `budgets.toml`, replace the 3 skipped tests with tests on a fake tokenizer.

## Spec bookkeeping

`skye-structure` (formerly `structure`) is the one cross-cutting spec; `skye` (base), `skye-consolidation` and `wiki` are merged into its three files (specs are never archived); their requirements moved to steering, see `.kiro/docs/spec-migration.md`. Requirements and high-level design
are in `.kiro/steering/10-requirements.md` and `11-design.md`; decisions in `12-decisions.md`.
- [ ] **Migrate the old specs** to component specs named like the component, with user stories that cite requirement numbers,
      a design that opens with `Builds on:`, and the tasks: `model-providers` to `models`, `capability-support`
      to `tools`, `prompts-support` to `prompts`, `policy-engine` to `policy`, `agent-runtime` to `agents`.
- [ ] **Create the missing specs:** `auth`, `router`, `store`, `memory`, `guard`, `observe`, `teams`, `flows`.
- [ ] **Write `.kiro/specs/README.md`**, the progression view across components.
- [ ] **Docs work (from the wiki spec):** `docs/budgets.md` into its area; migrate the loose pages; shrink `README.md`; add the docs
      test in `tests/docs` (front matter, links resolve, every page reachable from `docs/index.md`).
- [ ] **Prompts** `.kiro/prompts/01..03` are one-off instructions: move them to `.kiro/prompts/done/` after copying any owner choice
      to `12-decisions.md`. Prompt 03 needs rewriting for the new model first.

## Code

- [ ] **`auth` strategies and credential sources.** `aws.py` and `google.py` exist; the OAuth2/Azure strategies,
      the token cache, the secret-manager sources (AWS Secrets Manager, SSM, Key Vault, Google Secret Manager)
      and the credential-source extension point are the `auth` spec. The `auth` extra declares `rsa`, but no code
      imports it yet (that is the one `xfail`).
- [ ] **pydantic → dataclasses.** Core models still use pydantic (a core dependency). Product constraint 6 of the
      structure prompt defers this to a later step.
- [ ] **README as manual.** `README.md` is 1075 lines; moving its content into the wiki sections belongs to the
      docs prompt, not the `wiki` spec.
- [ ] **Router review.** The router fix replaced the sync tracker reads with an async snapshot
      (`routing_strategies.prepare`) and added `aget_usage_stats` / `aget_cooldown_models`. Read the diff of
      `router/model_router.py`, `router/routing_strategies.py`, `router/health_tracker.py` before committing.

## Tests

- [ ] **xpass.** `test_extras_footprint.py::test_import_stays_within_module_budget` is marked xfail (non-strict) but
      passes now. Remove the marker, or make it strict.
- [ ] **4 skipped** in `tests/differential/test_models_differential.py`: an SDK-vs-REST scaffold that needs live
      credentials. Write the comparisons or delete the scaffold.
- [ ] **3 skipped** in `tests/unit/utils/test_token_counter.py`: `tiktoken` is not in the dev environment. Depends on
      the `tiktoken` decision above.
- [ ] **Old directory names.** `tests/unit/providers`, `routes` and `capabilities` still use the pre-rename names;
      rename them to `models`, `router`, `tools`.
- [ ] `make budget-fast` has not been run on its own since the rename (`make budget` and `make differential` have).
