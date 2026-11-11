# Rules for code inside Skye

Read this when you write or review code in the library itself.

- **Standard library only in the core.** No pydantic, no tenacity, no PyYAML, no other third-party import. A library that is only needed by one
  feature is an optional extra, imported lazily. New data structures are `@validated` dataclasses from `skye.base.validated`.
- **Short imports:** `skye.messages`, `skye.completion`, `skye.exceptions`, `skye.config`, `skye.interfaces`, `skye.data`. A facade only
  re-exports.
- **Ports.** A Port that third parties implement as a plain class is a `Protocol`; a component never imports another runtime component, it
  receives it as a `Runnable`.
- **Errors** come from `skye.exceptions` (`ValidationError`, `ConfigurationError`, ...). A value that cannot be read raises `ValidationError`
  with the field and the value. A provider failure is a `ProviderError` subclass chosen by the response (D104): `RateLimitError` (429),
  `ServerError` (5xx), `ProviderTimeoutError`, `AuthenticationError` (401/403), `BadRequestError` (other 4xx) and its
  `ContentPolicyError`; each has `.provider`, `.status_code` and `.retry_after` (seconds or `None`). An input form the adapter does
  not accept (Bedrock and an image URL) is an `UnsupportedModalityError` (a `ProviderError`, `.modality`, no `status_code`, never
  retried; Requirement 26.3). An error never logs itself (D105):
  the code that handles it logs it once.
- **No file I/O in `base`:** the parser takes text; the code that reads a file lives in the component or in `skye.utils`.
- **Examples** run with no key (a scripted model), stay small and print plain output.
- **Configuration** is `.skye` (router, flow, prompt) or JSON (library configuration). The library reads no YAML.

## Keeping this skill current

This skill ships inside the package (`src/skye/utils/claude_skill/skye/`) and `skye skill install` copies `SKILL.md` and `references/`.
Whoever changes the command line, the `.skye` grammar or its limits, the public API or a rule above must update the matching file in the same
change. `tests/unit/dsl/test_claude_skill.py` fails when a file names a command, block kind, strategy, prefix or function that does not exist,
or when a `skye` example does not pass `skye check`. `evals/evals.json` holds the test prompts and expectations of the skill; add one when you add
a rule a model could get wrong.
