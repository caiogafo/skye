# Implementation Plan: models

## Overview

Milestones in build order for the `models` component (codename zephyr): the shared transport first, then the base providers,
then the per-provider REST adapters, embeddings, token counting and cost, the decision model, and the differential oracle.
Status is judged from the code in `src/skye/models` and the tests in `tests/`, not from the former `model-providers` checkboxes.
Each task cites the steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it
honors.

## Tasks

- [x] 1. Shared transport (stdlib only)
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

- [x] 2. Base providers and registry
  - [x] 2.1 `BaseModelProvider` / `BaseEmbeddingProvider` with retry, health and `Runnable.invoke`
    - Evidence: `src/skye/models/base.py`; `tests/unit/models/test_base_provider.py`, `test_base_embedding_provider.py`, `test_runnable_conformance.py`.
    - _Requirements: 9.1, 9.5, 9.10, 16.1_
  - [x] 2.2 Registry behind the registry Port + `provider()` factory
    - Evidence: `src/skye/models/registry.py` (`ProviderRegistry`, `provider`); `tests/unit/models/test_provider_registry.py`, `test_provider_registration.py`.
    - _Requirements: 9.9, 6.1_
  - [x]* 2.3 Health metrics unit tests
    - Evidence: `tests/unit/models/test_health_monitoring.py`.
    - _Requirements: 17.2, 18.3_

- [x] 3. REST adapters (one per provider)
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
  - [x] 3.5 Google adapter authentication through the `auth` component
    - Evidence: `src/skye/models/llm/google_provider.py` imports `AuthenticationInterface` from `skye.base.interfaces.authentication`, resolves credentials via `skye.auth.google.resolve_google_auth`, has `_initialize_client` return `None` (no vendor SDK), and exposes a lazy `authenticator` property that signs requests over the shared transport; `src/skye/auth/google.py`.
    - _Requirements: 9.3, 11.1, 11.9_

- [x] 4. Embedding adapters behind the `vector_encoder` Port
  - [x] 4.1 OpenAI, Bedrock (Titan), Cohere, Google embeddings
    - Evidence: `src/skye/models/embeddings/openai_embeddings.py`, `bedrock_embeddings.py`, `cohere_embeddings.py`, `google_embeddings.py`; `tests/unit/models/test_openai_embeddings.py`, `test_bedrock_embeddings.py`, `test_cohere_embeddings.py`, `test_google_embeddings.py`.
    - _Requirements: 25.1, 25.2, 25.3_
  - [x] 4.2 Google multimodal embeddings (image inputs, text-shaped vectors)
    - Evidence: `src/skye/models/embeddings/google_multimodal_embeddings.py`; `tests/unit/models/test_google_multimodal_embeddings.py`.
    - _Requirements: 25.4, 26.1, 26.3_

- [x] 5. Multimodal inputs at the boundary
  - [x] 5.1 `ImageHandler`: URL / data URL / path / bytes -> provider shape
    - Evidence: `src/skye/models/transport/multimodal.py`.
    - _Requirements: 26.1, 26.2, 26.3_
  - [x] 5.2 Carry images in a message and convert them in each adapter
    - Evidence: `src/skye/base/messages.py` (`UserMessage.images`: URL, `data:` URI, path or bytes; `to_dict` turns them into JSON-safe text; `sniff_image_mime`), `src/skye/models/transport/multimodal.py` (`ImageHandler.to_google_format`, MIME sniffing for bytes, `to_bedrock_format` rejects a URL because Bedrock does not fetch them), the four adapters' `_transform_messages` (OpenAI `image_url` parts, Anthropic `image` blocks before the text, Bedrock `image` blocks with base64 bytes, Google `inlineData`/`fileData` parts); `tests/unit/models/test_message_images.py` (each provider's request body over a fake network); the example `examples/advanced/multimodal.py` shows a message with an image. Decision taken on 2026-11-03: images live in a field of `UserMessage`, not in `ContentChunk` parts.
    - _Requirements: 26.1, 26.2, 26.3_

- [x] 6. Token counting and cost
  - [x] 6.1 Cost estimation and custom pricing
    - Evidence: `src/skye/models/transport/cost.py` (`CostCalculator`); `tests/unit` cost coverage.
    - _Requirements: 19.1, 19.2_
  - [x] 6.2 Tokenizer per D25: stdlib approximate by default, lazy `tiktoken` extra
    - Evidence: `src/skye/models/transport/token_counter.py` (stdlib estimate by default; `tiktoken` through `LazyImporter` with `install_extra="tokens"`); decision D33 renames the extra `openai` to `tokens` (option A of the former O22; `openai` stays as an empty extra), with `pyproject.toml`, `[extras.tokens]` in `budgets.toml`, the CI footprint job and `tests/budget` following; `tests/unit/models/test_token_counter_without_extra.py` (`import skye` loads no tokenizer, counting works with `tiktoken` blocked, the counter asks for the `tokens` extra). D33 was taken by the assistant on the instruction to implement every task: change it if you decide otherwise.
    - _Requirements: 28.1, 28.2, 28.3; D25_

- [x] 7. Decision model (Jev)
  - [x] 7.1 Implement `models/decision/jev.py` behind the `decision` Port
    - Evidence: `src/skye/models/decision/jev.py` (`JevDecisionModel` implements `DecisionModel`; `normalize_probabilities` checks every option has a probability in 0..1 and scales them to sum to 1; the choice is the most probable option, the first on a tie; an empty, duplicated or non-string option set raises `ValidationError` and nothing is sent; a malformed answer raises `ProviderError` and returns no choice), exported from `skye.models`; `tests/unit/models/test_jev_decision.py`. The wire format (`{"prompt", "options"}` in, `{"probabilities": {option: p} | [p, ...]}` out) is the one the spec and the gateway assume; it was not checked against a hosted Jev service, so `_build_request` and `_read_probabilities` are the two places to adapt. No environment variable is read (D18). The gateway selector stays under O8.
    - _Requirements: 9.8_
  - [x]* 7.2 Property test: probabilities are well-formed
    - Evidence: `tests/unit/models/test_jev_decision.py` (`test_probabilities_are_well_formed_for_any_non_empty_option_set`: 300 seeded random option sets, each probability in 0..1, sum 1, the chosen option has the maximum; the empty set raises and sends nothing). No property-testing library is a dev dependency, so it uses a seeded `random.Random`.
    - _Requirements: 9.8_

- [x] 8. Structured output on dataclasses (D24)
  - [x] 8.1 Move `response_schema` / `structured_output` off pydantic
    - Evidence: `src/skye/models/transport/structured.py` (`schema_of`, `strict_schema`, `parse_structured`, `schema_instruction`, `STRUCTURED_TOOL`), used by `models/base.py` and the adapters; a `@validated` or plain `@dataclass` is the declared shape, a user's pydantic model still works through `model_json_schema` / `model_validate_json`, and a reply that does not conform raises `ValidationError` naming the field (not retried: `_complete_with_retry` no longer wraps it). OpenAI: `json_schema` response format, `strict` only when every property is required. Anthropic and Bedrock had no structured path: they now force one tool (`skye_structured_output`) and read its input (function calling, Requirement 27.1); Google asks for `application/json` with the schema in the system instruction. `src/skye/base/validated.py` gained enum fields (validation, schema, serialization). `tests/unit/models/test_structured_output_dataclass.py`, `tests/unit/test_validated.py`; the request shapes are tested over a fake network, not against the live services.
    - _Requirements: 27.1, 27.2; D24_
  - [x] 8.2 Rewrite the structured-output examples off pydantic
    - Evidence: `examples/advanced/structured_output.py`, `examples/providers/structured_output_example.py`, `examples/basic/simple_completion.py` and `examples/providers/multimodal_example.py` use `@validated` dataclasses and no pydantic import; the docs (`docs/models/structured-outputs.md`, `docs/getting-started.md`, `docs/models/provider-guide.md`, the examples READMEs) follow. `tests/examples` runs them.
    - _Requirements: 24.2, 24.3; D24_

- [x] 9. Differential oracle (SDK vs REST)
  - [x] 9.1 Resolve the 4 skipped differential tests
    - Evidence: `tests/differential/test_models_differential.py` and `tests/differential/fake_model_server.py`: the same request goes through the built-in REST adapter and the vendor SDK (`openai`, `anthropic`, `boto3`, each pointed at a local fake server speaking the provider's wire format), and the text, finish reason and token usage (epsilon 0) must match, as must the error category (401, 429) and the user text sent. OpenAI, Anthropic and Bedrock are covered; Google is not, because the Vertex SDK cannot be redirected to a local server (the file says so). It needs no credentials, so no case skips on a missing key. It found a real defect, fixed: `ProviderError` lost the HTTP status when the adapter wrapped the transport's error (`models/base.py`; unit test in `tests/unit/models/test_message_images.py`). Run with `make differential`.
    - _Requirements: 9.4; D14_

- [x] 10. Checkpoint
  - Evidence: full `models` suite green — `uv run pytest tests/unit/models tests/differential -q` → 426 passed (2026-11-03). Open follow-ups noted elsewhere in this plan: D33 (extra `tokens`) and the Jev wire format were assistant decisions pending owner ratification, the Google differential case is uncovered, and O8 (gateway selector for Jev) remains open.

## Notes

- Tasks marked with `*` are optional (tests) and can be skipped for a faster path.
- Status reflects the code in `src/skye/models` and `tests/` at migration time, not the former `model-providers` checkboxes.
- The `models` extra is empty (stdlib REST); `google` declares only its SDK and exact token counting declares only `tiktoken` (design "Extras and budgets"; D25).
- Done on 2026-11-03: every task except the final checkpoint (10), left for Kiro. Decisions taken on the instruction to implement everything: D33 (extra `tokens`), images as a `UserMessage` field, the Jev wire format as an assumption (7.1). Still open: O8 (gateway selector for Jev), the Google differential case, a live check of the request shapes against the real services.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "1.5"] },
    { "id": 1, "tasks": ["2.1", "2.2", "5.1", "6.1"] },
    { "id": 2, "tasks": ["2.3", "3.1", "3.2", "3.3", "3.4", "5.2", "6.2", "7.1"] },
    { "id": 3, "tasks": ["3.5", "4.1", "7.2", "8.1"] },
    { "id": 4, "tasks": ["4.2", "8.2", "9.1"] },
    { "id": 5, "tasks": ["10"] }
  ]
}
```
