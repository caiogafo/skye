# Implementation Plan: auth

## Overview

Milestones in build order for the `auth` component (codename ozone): the tier-A pieces that need no network (SigV4 signing,
AWS credential sources, the simple header strategies), then the tier-B HTTP and metadata flows and the token cache, then the
tier-C RSA minting and vendor-cache reads, the native secret managers, and the extension point, with the budget guards
throughout. Status is judged from the code in `src/skye/auth` and the tests in `tests/unit/auth` and `tests/budget`. Each task
cites the steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it honors.

## Tasks

- [ ] 1. Tier A — signing and credentials without network
  - [x] 1.1 Stdlib SigV4 signer
    - Evidence: `src/skye/auth/sigv4.py` (`sign_request`: canonical request, scope, signing key over `hashlib`/`hmac`/`datetime`); `tests/unit/test_transport.py` asserts the AWS documentation vector.
    - _Requirements: 11.1, 11.9_
  - [x] 1.2 AWS credential sources and authenticators
    - Evidence: `src/skye/auth/aws.py` (`AwsCredentials` with the expiry margin; `CredentialProvider` resolving explicit -> env -> profile static keys -> container -> IMDSv2; `SigV4Authenticator`; `BedrockApiKeyAuthenticator`; `bedrock_authenticator`), `tests/unit/auth/test_aws.py`. SSO/assume-role profiles are rejected with a log-in-again message.
    - _Requirements: 11.1, 11.9_
  - [ ] 1.3 API key / bearer strategies for OpenAI-compatible providers, Anthropic and Cohere
    - Note: add `src/skye/auth/openai_compatible.py` with `AuthenticationInterface` implementations for an API key and a bearer header, reading each provider's standard variable (never a prefixed one). Keep the no-mutation and no-secret-in-error rules.
    - _Requirements: 11.1, 11.6, 11.9_

- [ ] 2. Tier B — HTTP exchanges, metadata and the token cache
  - [x] 2.1 Google bearer, metadata-server and API-key authenticators
    - Evidence: `src/skye/auth/google.py` (`GoogleBearerAuth`, `GoogleMetadataAuth` caching until an expiry skew, `GoogleApiKeyAuth`, `resolve_google_auth`), `tests/unit/auth/test_google.py`. Service-account JWT and Workload Identity raise a "not supported yet" hint (completed in task 3).
    - _Requirements: 11.1, 11.9_
  - [ ] 2.2 Shared lazy token cache with an expiry margin
    - Note: add `src/skye/auth/cache.py`, a token cache keyed by credential identity returning a cached token until within a margin of expiry, generalizing the `GoogleMetadataAuth` skew for OAuth2, token exchange and secret-manager tokens. No background thread (D1, D27).
    - _Requirements: 11.1, 11.3_
  - [ ] 2.3 401-refresh-and-retry-once helper
    - Note: add `src/skye/auth/refresh.py` so an HTTP caller that gets a 401 forces one credential refresh and retries exactly once; a second 401 surfaces the error.
    - _Requirements: 11.2_
  - [ ] 2.4 OAuth2 flows and AWS web identity / assume-role over STS
    - Note: implement the OAuth2 client-credentials and token-exchange flows and Google's authorized-user refresh over `base/http.py`, and AWS assume-role (including cross-account) and web identity (OIDC token from a file) through signed STS reusing `sigv4.py`.
    - _Requirements: 11.1, 11.9_

- [ ] 3. Tier C — RSA minting and vendor-cache reads
  - [ ] 3.1 RS256 assertions with the pure-Python `rsa`
    - Note: add `src/skye/auth/rsa_signing.py` minting RS256 JWT assertions for a Google service-account file and a Microsoft Entra ID certificate; import `rsa` lazily inside the minting function through the `missing_extra` helper (D12: not `google-auth`, not `cryptography`). This is the code that makes the `auth` extra import `rsa` and removes the `EXTRA_XFAIL["auth"]` entry (task 7.1).
    - _Requirements: 11.4; honors D12_
  - [ ] 3.2 Google service-account, impersonation and Workload Identity Federation
    - Note: complete `src/skye/auth/google.py` so a service-account file (RS256 via 3.1), impersonation and Workload Identity Federation resolve to a bearer; replace the "not supported yet" hint with the working path.
    - _Requirements: 11.4, 11.9_
  - [ ] 3.3 Microsoft Entra ID for Azure OpenAI
    - Note: add `src/skye/auth/azure.py` for managed identity, client secret, certificate (RS256 via 3.1), federated token file and API key.
    - _Requirements: 11.4, 11.9_
  - [ ] 3.4 Read vendor-tool caches, never an interactive login
    - Note: where a mode needs an earlier login (AWS IAM Identity Center SSO, `az login`, `gcloud auth login`, application-default-credentials login), read that tool's cache and, when it is missing or expired, raise a log-in-again error; never launch an interactive login.
    - _Requirements: 11.3, 11.7_

- [ ] 4. Extension point
  - [ ] 4.1 Credential-source registry for a user-supplied source
    - Note: add `src/skye/auth/registry.py` letting user code register a custom credential source and resolve it by name, the one extension point for `auth`; adding a source edits only `auth`.
    - _Requirements: 11.5; honors D10_

- [ ] 5. No-leak, no-background, bounded-surface guarantees
  - [ ] 5.1 No secret in a log, repr or error; no background thread; no interactive login
    - Note: audit every module so no secret value appears in a log, repr or error (they already name the missing variable, not its value), confirm no background thread or long-lived process, and confirm no interactive login path. Add a test asserting an error message for a missing credential carries the variable name and not the value.
    - _Requirements: 11.3_
  - [ ] 5.2 Credentials only from provider-standard variables; three prefixed variables only
    - Note: confirm every source reads the provider's standard variable (`AWS_*`, `GOOGLE_*`, the Azure and OpenAI-compatible equivalents) and never a prefixed one, and that `auth` adds no prefixed variable beyond the three owned by `base`.
    - _Requirements: 11.6; honors D18_

- [ ] 6. Native secret managers (blocked on O6)
  - [ ] 6.1 AWS Secrets Manager, SSM Parameter Store, Azure Key Vault, Google Secret Manager
    - Note: add `src/skye/auth/secrets.py` reading a secret over `base/http.py`, each call authenticated with the matching `auth` strategy, each source reachable through the registry (task 4.1). Blocked on open decision O6 (where `base/http.py` lives and whether cloud secret managers are in scope of `auth`); record the decision in `12-decisions.md` before the code lands.
    - _Requirements: 11.1; O6_

- [ ] 7. Budget and structure guards
  - [ ] 7.1 The `auth` extra declares exactly `rsa`; `google` never declares it
    - Note: once task 3.1 imports `rsa`, remove `EXTRA_XFAIL["auth"]` in `tests/budget/test_extras_footprint.py` so `test_auth_extra_declares_exactly_rsa` enforces declare-exactly on live code; confirm `budgets.toml` `[extras.auth]` stays at `rsa` only.
    - Evidence (today): `tests/budget/test_extras_footprint.py` (`test_auth_extra_declares_exactly_rsa`, currently xfail), `budgets.toml` (`[extras.auth]` -> `rsa`, 1 MB, 0 compiled).
    - _Requirements: 11.4_
  - [x] 7.2 `auth` imports only `base`; `rsa` and provider libraries never load on a clean import
    - Evidence: `tests/budget/test_import_matrix.py` (`ALLOWED["auth"] == {"base"}`, layer base), `tests/budget/test_footprint_budget.py`/`test_clean_import.py` (`forbidden_at_import` has no `rsa` leak; `import skye` pulls no provider library). `rsa` is imported lazily by the minting function only (task 3.1).
    - _Requirements: 11.4_
  - [x] 7.3 Codename ozone only in the sanctioned places
    - Evidence: `src/skye/auth/__init__.py` (docstring ends "Codename: ozone."), `tests/budget/test_codenames.py` (`COMPONENT_CODENAMES["auth"] == "ozone"`).
    - _Requirements: 11.1_

- [ ] 8. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional (tests) and can be skipped for a faster path; this plan has none, because the budget
  guards (task 7) are mandatory.
- Status reflects the code in `src/skye/auth` and the tests at writing time: SigV4 (1.1), AWS sources (1.2), the Google
  bearer/metadata/API-key authenticators (2.1), the import-matrix/clean-import guards (7.2) and the codename (7.3) are done;
  the RSA-dependent modes, Azure, the OpenAI-compatible strategies, the token cache, the 401 retry, the registry and the
  secret managers are the remaining authentication milestone.
- The authentication Port itself (`base/interfaces/authentication.py`) is owned by `0-base-base`, not this spec; `auth` only
  implements it.
- Open items: 6.1 (O6, secret managers and where `base/http.py` lives).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1", "7.2", "7.3"] },
    { "id": 1, "tasks": ["1.3", "2.2", "2.3"] },
    { "id": 2, "tasks": ["2.4", "3.1", "4.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "7.1"] },
    { "id": 4, "tasks": ["5.1", "5.2", "6.1"] }
  ]
}
```
