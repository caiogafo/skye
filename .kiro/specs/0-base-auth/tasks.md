# Implementation Plan: auth

## Overview

Milestones in build order for the `auth` component (codename ozone): the tier-A pieces that need no network (SigV4 signing,
AWS credential sources, the simple header strategies), then the tier-B HTTP and metadata flows and the token cache, then the
tier-C RSA minting and vendor-cache reads, the native secret managers, and the extension point, with the budget guards
throughout. Status is judged from the code in `src/skye/auth` and the tests in `tests/unit/auth` and `tests/budget`. Each task
cites the steering requirement numbers it satisfies (`Requirement N.k` of `10-requirements.md`) or the decision it honors.

## Tasks

- [x] 1. Tier A — signing and credentials without network
  - [x] 1.1 Stdlib SigV4 signer
    - Evidence: `src/skye/auth/sigv4.py` (`sign_request`: canonical request, scope, signing key over `hashlib`/`hmac`/`datetime`); `tests/unit/test_transport.py` asserts the AWS documentation vector.
    - _Requirements: 11.1, 11.9_
  - [x] 1.2 AWS credential sources and authenticators
    - Evidence: `src/skye/auth/aws.py` (`AwsCredentials` with the expiry margin; `CredentialProvider` resolving explicit -> env -> profile static keys -> container -> IMDSv2; `SigV4Authenticator`; `BedrockApiKeyAuthenticator`; `bedrock_authenticator`), `tests/unit/auth/test_aws.py`. Since then `CredentialProvider` also resolves web identity, assume-role and SSO profiles (tasks 2.4 and 3.4).
    - _Requirements: 11.1, 11.9_
  - [x] 1.3 API key / bearer strategies for OpenAI-compatible providers, Anthropic and Cohere
    - Evidence: `src/skye/auth/openai_compatible.py` (`BearerAuth`, `ApiKeyAuth`, `openai_authenticator`, `anthropic_authenticator`, `cohere_authenticator`, `api_key_authenticator`; each reads its provider's standard variable, a missing key names the variable, no mutation, `repr` shows the class name only); `tests/unit/auth/test_oauth2_and_keys.py`.
    - _Requirements: 11.1, 11.6, 11.9_

- [x] 2. Tier B — HTTP exchanges, metadata and the token cache
  - [x] 2.1 Google bearer, metadata-server and API-key authenticators
    - Evidence: `src/skye/auth/google.py` (`GoogleBearerAuth`, `GoogleMetadataAuth` caching until an expiry skew, `GoogleApiKeyAuth`, `resolve_google_auth`), `tests/unit/auth/test_google.py`. Service-account JWT and Workload Identity raise a "not supported yet" hint (completed in task 3).
    - _Requirements: 11.1, 11.9_
  - [x] 2.2 Shared lazy token cache with an expiry margin
    - Evidence: `src/skye/auth/cache.py` (`TokenCache` keyed by credential identity with an expiry margin and no thread; `CachedBearerAuth`, the bearer authenticator the Google, Azure and OAuth2 modes are built on); `tests/unit/auth/test_cache_refresh.py`.
    - _Requirements: 11.1, 11.3_
  - [x] 2.3 401-refresh-and-retry-once helper
    - Evidence: `src/skye/auth/refresh.py` (`send_with_refresh`: a 401 calls the authenticator's `refresh()` and retries once, a second 401 or any other error is raised); `tests/unit/auth/test_cache_refresh.py`, `tests/unit/auth/test_secrets.py` (used by the secret managers).
    - _Requirements: 11.2_
  - [x] 2.4 OAuth2 flows and AWS web identity / assume-role over STS
    - Evidence: `src/skye/auth/oauth2.py` (`ClientCredentialsAuth`, `TokenExchangeAuth`, `token_request`, `file_token`), `src/skye/auth/google.py` (`GoogleAuthorizedUserAuth`), `src/skye/auth/sts.py` (`assume_role` signed with `sigv4.py`, `assume_role_with_web_identity`) wired into `CredentialProvider` in `src/skye/auth/aws.py` (`role_arn`, `AWS_ROLE_ARN` with `AWS_WEB_IDENTITY_TOKEN_FILE`, profile `role_arn` and `source_profile`); `tests/unit/auth/test_oauth2_and_keys.py`, `tests/unit/auth/test_aws_sts_sso.py`, `tests/unit/auth/test_google_credentials.py`.
    - _Requirements: 11.1, 11.9_

- [x] 3. Tier C — RSA minting and vendor-cache reads
  - [x] 3.1 RS256 assertions with the pure-Python `rsa`
    - Evidence: `src/skye/auth/rsa_signing.py` (`sign_rs256_jwt`, `load_private_key` for PKCS#1 and PKCS#8, `service_account_assertion`, `entra_client_assertion`, `certificate_thumbprint`; `rsa` imported inside the functions through `missing_extra("rsa", extra="auth")`); `tests/unit/auth/test_rsa_signing.py` (signature verified with the public key, `MissingExtraError` when `rsa` is absent). The `EXTRA_XFAIL["auth"]` entry is removed (task 7.1).
    - _Requirements: 11.4; honors D12_
  - [x] 3.2 Google service-account, impersonation and Workload Identity Federation
    - Evidence: `src/skye/auth/google.py` (`GoogleServiceAccountAuth`, `GoogleImpersonatedAuth`, `GoogleExternalAccountAuth` for Workload Identity Federation from a file or a URL, `load_credentials_file`, `resolve_google_auth` reading `GOOGLE_APPLICATION_CREDENTIALS` and the gcloud file); the "not supported yet" hint is gone; `tests/unit/auth/test_google_credentials.py`, `tests/unit/auth/test_google.py`.
    - _Requirements: 11.4, 11.9_
  - [x] 3.3 Microsoft Entra ID for Azure OpenAI
    - Evidence: `src/skye/auth/azure.py` (`AzureManagedIdentityAuth` for IMDS and App Service, `AzureClientSecretAuth`, `AzureCertificateAuth`, `AzureFederatedTokenAuth`, `AzureApiKeyAuth`, `resolve_azure_auth` over the standard Azure variables); `tests/unit/auth/test_azure.py`.
    - _Requirements: 11.4, 11.9_
  - [x] 3.4 Read vendor-tool caches, never an interactive login
    - Evidence: `src/skye/auth/errors.py` (`LoginRequiredError` names the command to run again), `src/skye/auth/aws_profile.py` (IAM Identity Center: the `aws sso login` token cache plus the portal call), `src/skye/auth/azure.py` (`AzureCliCacheAuth` reads the Azure CLI token cache), `src/skye/auth/google.py` (the gcloud application-default-credentials file, `GoogleAuthorizedUserAuth` raises `LoginRequiredError` when the refresh token is revoked); no module runs a login (`tests/unit/auth/test_no_leak_and_env_surface.py` scans for it); `tests/unit/auth/test_aws_sts_sso.py`, `test_azure.py`, `test_google_credentials.py`.
    - _Requirements: 11.3, 11.7_

- [x] 4. Extension point
  - [x] 4.1 Credential-source registry for a user-supplied source
    - Evidence: `src/skye/auth/registry.py` (`register_credential_source`, `resolve_credential_source`, `list_credential_sources`, `unregister_credential_source`; the built-in sources are registered by dotted name and imported only when resolved); `tests/unit/auth/test_registry.py`.
    - _Requirements: 11.5; honors D10_

- [x] 5. No-leak, no-background, bounded-surface guarantees
  - [x] 5.1 No secret in a log, repr or error; no background thread; no interactive login
    - Evidence: `tests/unit/auth/test_no_leak_and_env_surface.py` (an AST scan finds no thread, timer, subprocess, `webbrowser` or `input` in `src/skye/auth`; no secret in the `repr` or `str` of 19 authenticators; a missing credential names the variable, not a value; a failed exchange and a bad key leak nothing to the error or the log); `AwsCredentials` no longer shows its keys in `repr`.
    - _Requirements: 11.3_
  - [x] 5.2 Credentials only from provider-standard variables; three prefixed variables only
    - Evidence: `tests/unit/auth/test_no_leak_and_env_surface.py` (every variable name in `src/skye/auth` starts with a provider-standard prefix; no `SKYE_` text; `ALL_ENV_VARS` of `base` is still the three).
    - _Requirements: 11.6; honors D18_

- [x] 6. Native secret managers (O6 closed by D32)
  - [x] 6.1 AWS Secrets Manager, SSM Parameter Store, Azure Key Vault, Google Secret Manager
    - Evidence: `src/skye/auth/secrets.py` (`AwsSecretsManager`, `AwsParameterStore` over SigV4; `AzureKeyVault` and `GoogleSecretManager` over a bearer token; all over `base/http.py`, each with the 401 refresh once, each reachable through the registry as `aws-secrets-manager`, `aws-ssm`, `azure-key-vault`, `google-secret-manager`); O6 is closed by decision D32 (`.kiro/steering/12-decisions.md`); `tests/unit/auth/test_secrets.py`.
    - _Requirements: 11.1; O6_

- [x] 7. Budget and structure guards
  - [x] 7.1 The `auth` extra declares exactly `rsa`; `google` never declares it
    - Evidence: `tests/budget/test_extras_footprint.py` (`EXTRA_XFAIL` is empty: `test_extra_declares_exactly_what_its_component_imports[auth]` passes on live code, and `test_auth_extra_declares_exactly_rsa` passes); `budgets.toml` `[extras.auth]` stays at `rsa` only (1 MB, 0 compiled).
    - _Requirements: 11.4_
  - [x] 7.2 `auth` imports only `base`; `rsa` and provider libraries never load on a clean import
    - Evidence: `tests/budget/test_import_matrix.py` (`ALLOWED["auth"] == {"base"}`, layer base), `tests/budget/test_footprint_budget.py`/`test_clean_import.py` (`forbidden_at_import` has no `rsa` leak; `import skye` pulls no provider library). `rsa` is imported lazily by the minting function only (task 3.1).
    - _Requirements: 11.4_
  - [x] 7.3 Codename ozone only in the sanctioned places
    - Evidence: `src/skye/auth/__init__.py` (docstring ends "Codename: ozone."), `tests/budget/test_codenames.py` (`COMPONENT_CODENAMES["auth"] == "ozone"`).
    - _Requirements: 11.1_

- [x] 8. Checkpoint
  - Done 2026-11-03: `uv run pytest tests/unit/auth tests/budget` is green (196 passed, 0 xfailed), `uv run mypy src/skye/auth` clean, `uv run ruff check src/skye/auth` and `uv run black --check src/skye/auth` clean.

## Notes

- Tasks marked with `*` are optional (tests) and can be skipped for a faster path; this plan has none, because the budget
  guards (task 7) are mandatory.
- Status reflects the code in `src/skye/auth` and the tests at 2026-11-03: every task is done, including the final checkpoint (8),
  verified green.
- The authentication Port itself (`base/interfaces/authentication.py`) is owned by `0-base-base`, not this spec; `auth` only
  implements it.
- O6 is closed by decision D32: `base/http.py` stays in `base`, and the cloud secret managers are in scope of `auth`.
- Not covered, by scope (Requirement 11.8): on-premises Active Directory, SAML, hardware modules and non-RSA signing. Two modes of
  the documented list are partial: Google external accounts support file and URL sources only (no AWS-sourced external account),
  and the Azure CLI and AWS SSO caches are read, never refreshed.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1", "7.2", "7.3"] },
    { "id": 1, "tasks": ["1.3", "2.2", "2.3"] },
    { "id": 2, "tasks": ["2.4", "3.1", "4.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "7.1"] },
    { "id": 4, "tasks": ["5.1", "5.2", "6.1"] },
    { "id": 5, "tasks": ["8"] }
  ]
}
```
