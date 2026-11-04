# UX rules

Rules that follow from the audit in `report.md` and from the owner's decisions. A rule marked **tested** has a test that fails when
it is broken; the others are reviewed by hand until a test is written. A rule that becomes a requirement moves to
`.kiro/steering/10-requirements.md` and stays here only as a pointer.

## Imports

1. **At most two levels.** A user-facing import is `skye` or `skye.<name>`; never `skye.a.b` or deeper. (D34, Requirement 7.14; **tested**
   by `tests/budget/test_public_imports.py`.)
2. **Never through `skye.base`.** `base` is the architectural name of the foundation layer, not a path a user types. (**Tested**.)
3. **Never into a module inside a component.** Import `skye.models.ImageHandler`, not `skye.models.transport.multimodal`; `skye.tools.CapabilityRegistry`,
   not `skye.tools.registry`. If the name a user needs is not exported by the package, export it there. (**Tested** by rule 1.)
4. **The public paths are fixed:**
   - `skye`: the commonest names (the four messages, `CompletionRequest`, `CompletionResponse`, `StreamChunk`, `TokenUsage`, the five
     errors, `provider`); loaded lazily, so `import skye` stays light.
   - `skye.interfaces`: every Port. `skye.data`: `Validated`, `validated`, `field`. `skye.messages`, `skye.completion`,
     `skye.exceptions`, `skye.config`: the full contents of those modules.
   - each component package (`skye.models`, `skye.router`, `skye.tools`, `skye.store`, `skye.auth`, ...) exports what a user of it needs.
5. **Short names are preferred.** A new public module or package gets one short word; no `_utils`, no `_helpers`, no names longer than about
   eight letters unless a domain word requires it.
6. **One name, one home.** A public name is defined once; any other path re-exports it. A new class never reuses the name of a public
   class (the three `CapabilitySchema` and two `CapabilityExecutionError` of the report are the debt to remove).
7. **Facades only re-export.** A facade contains no logic and no new names; adding a name to it means adding it to its source first.
8. **Examples show the shortest working import**, grouped one `from` line per package, `from skye import ...` first.

## Names

9. **A name says what a user does or has.** Verbs for actions (`complete`, `stream`, `register`), nouns for things; the sync and async
   forms are `x` and `ax`. `get_x` reads one thing, `list_x` many, `set_x` configures, `register` adds.
10. **A contract class is named `*Interface`**, except the documented exceptions (`Runnable`, `DecisionModel`, `StorageBackend`); the
    docs say "a Port is a class named `*Interface`".
11. **Capability, tool and function call mean one thing**; the docs state it once and use "capability" for the library's own objects.
12. **A file is named after the one idea in it**; a provider file is `<provider>.py`, an embeddings file `<provider>_embeddings.py`.

## Contracts (Ports)

13. **A Port describes the call users make.** If the implementation takes `messages=...`, so does the Port. A signature that differs from
    its Port is a bug in one of them, never a `type: ignore`.
14. **Sync and async match the Port.** A Port method that is `def` is `def` in every implementation; an async iterator is typed
    `AsyncIterator`.
15. **Every Port states its error contract**: what it raises (a `SkyeError` subclass), what it returns when something is missing, whether
    it may be called from several threads or tasks, and, for hooks and observers, that their exceptions are logged and swallowed.
16. **Conformance is checked on signatures**, for abstract bases and `Protocol`s alike, and every built-in implementation is run
    through the check in one test.
17. **A Port with no implementation and no test is not exported** until a component needs it.
18. **Large Ports are split by role** (a caller that only selects takes the selector, not the whole router).

## Examples

19. **Every example runs with no key and no network**, prints a result, and never ends in a traceback; where a real service is needed it
    says so and shows what the output looks like. (Partly **tested**: `tests/examples` runs every example offline.)
20. **One idea per example, about 80 lines or fewer**; long variations go to the docs.
21. **No empty files, no duplicates:** a second example of the same idea replaces the first.
22. **Install strings are true.** `pip install skyeai[...]` names an extra that exists and declares a library; `pip install skyeai` is enough
    for every provider.
23. **Plain output:** section titles, no banners or emoji rows, labels aligned.
24. **Each folder has a short README** (what you learn, the command, what you will see, what you need), and it lists exactly the files
    of the folder.
25. **A reading order** is numbered in `examples/README.md`.

## Docs and docstrings

26. **The first docstring a user reads is run.** The package and Port docstring examples are checked (network calls skipped), so a field
    that does not exist (`response.text`) cannot appear.
27. **Docs use the same import paths as the examples** (**tested** by rule 1, which scans `docs/` and `README.md`).

## Status (2026-11-03)

- Rules 1 to 4, 7 and 8 are applied: facades added, 66 files rewritten, test added, decision D34 and Requirement 7.14 recorded.
- Rules 6, 9 to 18 and 19 to 26 are open; their findings and an order of work are in `report.md` (Parts 1 to 3).
