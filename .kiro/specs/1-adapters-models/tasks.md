# Implementation Plan: models

## Overview

Milestones in build order for the `models` component (codename zephyr): the shared transport first, then the base providers,
then the per-provider REST adapters, embeddings, token counting and cost, the decision model, and the differential oracle.
Status is judged from the code in `src/skye/models` and the tests in `tests/`, not from the former `model-providers` checkboxes.
Each task cites the steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it
honors.

## Tasks

- [ ] 1. Shared transport (stdlib only)
  - [x] 1.1 JSON REST over `base/http.py`
    - Evidence: `src/skye/models/transport/rest.py` (`post_json`, `stream_sse_json`, `JsonObject`), `src/skye/models/transport/http.py`; `tests/unit/test_rest_transport.py`, `tests/unit/test_transport.py`.
    - _Requirements: 9.1, 9.3_
  - [x] 1.2 SSE streaming decoder
    - Evidence: `src/skye/models/transport/streaming.py` (`parse_sse`); `tests/unit/test_transport.py`.
    - _Requirements: 9.9, 16.5_
  - [x] 1.3 Bedrock eventstream decoder
    - Evidence: `src/skye/models/transport/eventstream.py`; `tests/unit/test_eventstream.py`.
    - _Requirements: 9.9, 16.5_
  - [x] 1.4 Retry policy (3 after first attempt)
    - Evidence: `src/skye/models/transport/retry.py` (`with_retry`); `tests/unit/models/test_retry_logic.py`.
    - _Requirements: 9.2_
  - [x] 1.5 Error mapping to the SkyeError hierarchy
    - Evidence: `src/skye/models/transport/error_mapping.py`; `tests/unit/models/test_error_handling.py`.
    - _Requirements: 9.9, 18.1_

- [ ] 2. Base providers and registry
  - [x] 2.1 `BaseModelProvider` / `BaseEmbeddingProvider` with retry, health and `Runnable.invoke`
    - Evidence: `src/skye/models/base.py`; `tests/unit/models/test_base_provider.py`, `test_base_embedding_provider.py`, `test_runnable_conformance.py`.
    - _Requirements: 9.1, 9.5, 9.10, 16.1_
  - [x] 2.2 Registry behind the registry Port + `provider()` factory
    - Evidence: `src/skye/models/registry.py` (`ProviderRegistry`, `provider`); `tests/unit/models/test_provider_registry.py`, `test_provider_registration.py`.
    - _Requirements: 9.9, 6.1_
  - [x]* 2.3 Health metrics unit tests
    - Evidence: `tests/unit/models/test_health_monitoring.py`.
    - _Requirements: 17.2, 18.3_

- [ ] 3. REST adapters (one per provider)
  - [x] 3.1 OpenAI and Azure OpenAI (one family keyed by base URL + key)
    - Evidence: `src/skye/models/llm/openai_compatible.py` (`OpenAIProvider`, `AzureOpenAIProvider`); `tests/unit/models/test_openai_provider.py`, `test_azure_provider.py`, `tests/unit/test_openai_shape.py`.
    - _Requirements: 9.3, 9.5, 9.6, 9.10, 22.1_
  - [x] 3.2 Anthropic (Messages API, system message separate)
    - Evidence: `src/skye/models/llm/anthropic.py`; `tests/unit/models/test_anthropic_provider.py`.
    - _Requirements: 9.3, 9.5, 9.6, 9.10_
  - [x] 3.3 Bedrock (Converse + stream, SigV4 via auth, boto3 not required)
    - Evidence: `src/skye/models/llm/bedrock.py`; `tests/unit/models/test_bedrock_provider.py`.
    - _Requirements: 9.3, 9.5, 9.9, 7.3_
  - [x] 3.4 Google adapter (formerly "Vertex AI", renamed `google`)
    - Evidence: `src/skye/models/llm/google_provider.py` (`GoogleProvider`), registered as `"google"` in `src/skye/models/__init__.py`; `tests/unit/models/test_google_provider.py`.
    - _Requirements: 9.3; D19_
  - [ ] 3.5 Google adapter authentication through the `auth` component
    - Note: `GoogleProvider` must obtain Google service-account / metadata / ADC credentials through the `auth` authentication Port (RS256 with `rsa`, impersonation, metadata server, WIF, API key) rather than any in-adapter credential handling. Depends on the `auth` component and its credential sources; wire `GoogleProvider._initialize_client` to accept an `AuthenticationInterface` and sign over `base/http.py`.
    - _Requirements: 9.3, 11.1, 11.9_

- [ ] 4. Embedding adapters behind the `vector_encoder` Port
  - [x] 4.1 OpenAI, Bedrock (Titan), Cohere, Google embeddings
    - Evidence: `src/skye/models/embeddings/openai_embeddings.py`, `bedrock_embeddings.py`, `cohere_embeddings.py`, `google_embeddings.py`; `tests/unit/models/test_openai_embeddings.py`, `test_bedrock_embeddings.py`, `test_cohere_embeddings.py`, `test_google_embeddings.py`.
    - _Requirements: 25.1, 25.2, 25.3_
  - [x] 4.2 Google multimodal embeddings (image inputs, text-shaped vectors)
    - Evidence: `src/skye/models/embeddings/google_multimodal_embeddings.py`; `tests/unit/models/test_google_multimodal_embeddings.py`.
    - _Requirements: 25.4, 26.1, 26.3_

- [ ] 5. Multimodal inputs at the boundary
  - [x] 5.1 `ImageHandler`: URL / data URL / path / bytes -> provider shape
    - Evidence: `src/skye/models/transport/multimodal.py`.
    - _Requirements: 26.1, 26.2, 26.3_

- [ ] 6. Token counting and cost
  - [x] 6.1 Cost estimation and custom pricing
    - Evidence: `src/skye/models/transport/cost.py` (`CostCalculator`); `tests/unit` cost coverage.
    - _Requirements: 19.1, 19.2_
  - [ ] 6.2 Tokenizer per D25: stdlib approximate by default, lazy `tiktoken` extra
    - Note: `src/skye/models/transport/token_counter.py` already defaults to a stdlib approximation and falls back when `tiktoken` is absent, but it imports `tiktoken` via `LazyImporter.import_module("tiktoken", install_extra="openai")`. Change `install_extra` to the dedicated `tiktoken` extra (D25) so the extra name matches `budgets.toml`, and add a test asserting `import skye` imports no tokenizer and that counting works without the extra installed.
    - _Requirements: 28.1, 28.2, 28.3; D25_

- [ ] 7. Decision model (Jev)
  - [ ] 7.1 Implement `models/decision/jev.py` behind the `decision` Port
    - Note: No `decision/` package exists under `src/skye/models` yet. Implement `DecisionModel` (Jev) at `src/skye/models/decision/jev.py`: finite option set in, one choice with a probability per option (each 0..1, summing to 1), empty set rejected with an error and no choice. Consumed by `gateway`, `router`, `guard`. See open decision O8 on whether this gets its own milestone and a gateway selector.
    - _Requirements: 9.8_
  - [ ]* 7.2 Property test: probabilities are well-formed
    - Note: for any non-empty option set the returned probabilities are each in 0..1 and sum to 1; an empty set raises and returns no choice.
    - _Requirements: 9.8_

- [ ] 8. Structured output on dataclasses (D24)
  - [ ] 8.1 Move `response_schema` / `structured_output` off pydantic
    - Note: `src/skye/base/completion.py` still types `response_schema: type[BaseModel]` and `structured_output: BaseModel | None`. Under D24/O4, the declared output shape must be a dataclass and validation must raise `ValidationError` naming the field. Coordinate with the `base` spec (O4) before changing the shared completion models; update the adapters' structured-output paths to validate against the dataclass.
    - _Requirements: 27.1, 27.2; D24_

- [ ] 9. Differential oracle (SDK vs REST)
  - [ ] 9.1 Resolve the 4 skipped differential tests
    - Note: `tests/differential/test_models_differential.py` is a module-level `pytest.mark.skip` scaffold parametrized over `["openai", "anthropic", "bedrock", "google"]` (4 cases) with a `raise NotImplementedError` body. Either implement the comparison (same request through built-in REST and the vendor SDK, assert field-subset equality, numeric epsilon on token counts, and error-category equivalence; skip per provider when the credential env var is absent) or delete the scaffold if the oracle is tracked elsewhere.
    - _Requirements: 9.4; D14_

- [ ] 10. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional (tests) and can be skipped for a faster path.
- Status reflects the code in `src/skye/models` and `tests/` at migration time, not the former `model-providers` checkboxes.
- The `models` extra is empty (stdlib REST); `google` declares only its SDK and exact token counting declares only `tiktoken` (design "Extras and budgets"; D25).
- Open items at migration: 3.5 (Google auth through `auth`), 6.2 (`tiktoken` extra name), 7.1 (Jev not yet in `src`), 8.1 (pydantic structured output under O4), 9.1 (differential scaffold).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "1.5"] },
    { "id": 1, "tasks": ["2.1", "2.2", "5.1", "6.1"] },
    { "id": 2, "tasks": ["2.3", "3.1", "3.2", "3.3", "3.4", "6.2", "7.1"] },
    { "id": 3, "tasks": ["3.5", "4.1", "7.2", "8.1"] },
    { "id": 4, "tasks": ["4.2", "9.1"] }
  ]
}
```
