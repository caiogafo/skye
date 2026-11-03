---
component: auth
codename: ozone
---

Builds on: #[[file:.kiro/steering/11-design.md]] (sections: Layers, Allowed imports, Installation, Ports, Auth component, Extras and budgets, Transport and providers)

# Design Document: auth

## Overview

`auth` is the layer-0 authentication component (codename ozone). It sits next to `base` but is separate because it does I/O
and may need a third-party library: `base` does no file, network or process I/O (apart from `base/http.py`), while `auth`
calls metadata and token endpoints, reads credential files, may read a vendor tool's cache and needs `rsa` to mint tokens
(design "Auth component", D10, D12). It imports only `base` (design "Allowed imports"; enforced by
`tests/budget/test_import_matrix.py`), and every outbound request is authenticated through one Port so no component writes
authentication code per provider.

The authentication Port is defined in `base` (`base/interfaces/authentication.py`): `apply(method, url, headers, body)`
returns the request headers with authentication added or the request signed, without mutating the input. `auth` supplies the
implementations: strategies (API key and bearer, SigV4, OAuth2), credential sources (environment, files, container
credentials, IMDSv2, token exchange, metadata server, secret managers over `base/http.py`), an extensible credential-source
registry, and a lazy token cache with an expiry margin. This document describes only the internals of `auth`; the layer, the
allowed imports (only `base`), the Port catalogue and the extras-and-budgets rule are in the steering sections named above and
are not restated here.

`auth` is authentication (who you are, and signing the request); `policy` is authorization (what you may do). The two never
overlap, and the runtime reaches `policy` through the authorizer Port, never through `auth` (design "Auth component",
"Optional services"; D9, D10).

## Architecture

`auth` is a flat package of per-provider authenticator modules plus the shared pieces (the SigV4 signer, the token cache, the
credential-source registry). The one network-I/O helper is `base/http.py`, used by the HTTP-exchange and metadata-call
sources; the SigV4 signer and the RSA JWT minting are pure computation on the standard library and `rsa`.

Work is ordered by the tiers of the design "Auth component" section:

- **Tier A — no network.** API key and bearer headers, static-key and environment credential sources, SigV4 signing of an
  already-resolved credential, reading a credential or vendor-tool cache file. Pure standard library.
- **Tier B — an HTTP exchange or a metadata call over `base/http.py`.** Container credentials (ECS), IMDSv2, the metadata
  server, OAuth2 client-credentials and token-exchange flows, authorized-user refresh, secret-manager reads.
- **Tier C — RSA, a subprocess, or vendor-format files.** RS256 assertions for Google service accounts and Microsoft Entra ID
  certificates (needs `rsa`), reading the cache left by an earlier `aws sso login` / `az login` / `gcloud auth login` /
  application-default-credentials login.

```
auth/
  __init__.py             package docstring ending "Codename: ozone."
  sigv4.py                stdlib AWS Signature Version 4 signer (hashlib / hmac / datetime)
  aws.py                  AWS credential sources + SigV4Authenticator + Bedrock API key
  aws_profile.py          ~/.aws/config profiles: SSO cache (never a login), assume-role, web identity
  sts.py                  AssumeRole and AssumeRoleWithWebIdentity over STS (SigV4 reused)
  google.py               Google bearer, metadata, API key, service account, authorized user,
                          impersonation, Workload Identity Federation + resolver
  oauth2.py               client-credentials and token-exchange flows
  errors.py               LoginRequiredError (log in again; no mode logs in)
  azure.py                Microsoft Entra ID for Azure OpenAI: managed identity, client secret,
                          certificate (rsa), federated token file, API key
  openai_compatible.py    API key / bearer for OpenAI-compatible providers, Anthropic, Cohere
  cache.py                lazy token cache keyed by credential identity, with an expiry margin
  registry.py             credential-source registry: register and resolve a custom source (R11.5)
  rsa_signing.py          RS256 assertions for Google service accounts and Entra certificates (rsa)
  secrets.py              native secret-manager sources (AWS Secrets Manager, SSM Parameter Store,
                          Azure Key Vault, Google Secret Manager) over base/http.py
  refresh.py              the 401-refresh-and-retry-once helper shared by the HTTP callers
```

Each authenticator implements the `AuthenticationInterface` Port; a credential source resolves a credential set and may hand
it to an authenticator (as `SigV4Authenticator` takes a `CredentialProvider` today). The lazy library `rsa` is imported inside
the function that first mints a token (through the `missing_extra` helper in `base`), never at module import, so `import skye`
and a core-only install pull neither `rsa` nor any provider library (design "Public API and lazy imports"; Requirement 7.4).

## Scope

In scope are the documented, non-deprecated, non-interactive modes at the stated date, per provider (Requirement 11.7, 11.9):

- **AWS** — the serverless execution role (environment variables, container-credentials endpoint, IMDSv2); assume-role,
  including cross-account, through signed STS; web identity (an OIDC token from a file); Bedrock API keys.
- **Google** — service-account files (RS256 with `rsa`), impersonation, the metadata server, the authorized-user refresh
  token, Workload Identity Federation, and an API key or access token from the environment.
- **Microsoft Entra ID for Azure OpenAI** — managed identity, client secret, certificate (with `rsa`), federated token file,
  API key.
- **OpenAI-compatible providers, Anthropic and Cohere** — API key or bearer.

Out of scope (Requirement 11.8): on-premises Active Directory (Kerberos, NTLM, ADFS), SAML, hardware security modules
(PKCS#11) and non-RSA signing. Interactive login is never run (Requirement 11.3): where a mode needs an earlier vendor-tool
login (AWS IAM Identity Center SSO, `az login`, `gcloud auth login`, application-default-credentials login), `auth` reads that
tool's cache and, if it is missing or expired, raises an error saying to log in again.

## Components and Interfaces

### Strategies and the Port (Requirement 11.1)

Every authenticator implements `AuthenticationInterface.apply(method, url, headers, body) -> dict[str, str]`, returning a new
header dict so the caller's mapping is never mutated (the existing AWS and Google authenticators follow this). The strategies
are: API key and bearer (a header), SigV4 (a signature over `hashlib`/`hmac`), and OAuth2 (an HTTP token exchange that yields a
bearer). SigV4 is written once in `sigv4.py` and reused by Bedrock and by any signed STS call (design "Transport and
providers": "SigV4 signing is in `auth` and reused by Bedrock").

### Credential sources and the registry (Requirement 11.1, 11.5)

A credential source resolves a credential set from a place: environment variables, a credential file, container credentials,
instance metadata, a token exchange, the metadata server, or a native secret manager. AWS sources (`aws.py`) already cover
environment, profile static keys, container credentials and IMDSv2 through `CredentialProvider`, which resolves once and
refreshes shortly before expiry. New sources follow the same shape. `registry.py` lets user code register a custom credential
source and have it resolved by name, the one extension point for `auth` (design "Extension points": "credential provider ...
registering it in the `auth` registry"); adding one edits only `auth`.

### Secret managers (Requirement 11.1)

`secrets.py` reads a secret from AWS Secrets Manager, AWS SSM Parameter Store, Azure Key Vault or Google Secret Manager over
`base/http.py`, each call itself authenticated with the matching `auth` strategy (SigV4 for AWS, a bearer for Azure and
Google). A secret-manager source is a credential source like any other and is reachable through the registry.

### Token cache (Requirement 11.1, 11.2)

`cache.py` holds a lazy token cache keyed by the credential identity, returning a cached token until it is within an expiry
margin of its deadline and refreshing it otherwise. `GoogleMetadataAuth` already caches with a 60-second skew; the shared
cache generalizes that for OAuth2, token exchange and secret-manager tokens. On a 401 response, `refresh.py` forces one
refresh of the credential and retries the request exactly once (Requirement 11.2); a second 401 surfaces the error.

### RSA token minting (Requirement 11.4)

`rsa_signing.py` mints RS256 JWT assertions for a Google service-account file and for a Microsoft Entra ID certificate, using
only the pure-Python `rsa` (D12: not `google-auth`, not the compiled `cryptography`). `rsa` is the only third-party library in
the component and is imported lazily inside the minting function. The `auth` extra declares exactly `rsa`; the `google` extra
declares only the Google provider SDK and never `rsa` (Requirement 11.4), which the budget test asserts.

### No secrets in output; no background work (Requirement 11.3)

No authenticator or source puts a secret in a log, a repr or an error message: errors name the variable or file that is
missing, never its value. `auth` starts no background thread and runs no long-lived process (D1, D27): the token cache
refreshes lazily on the calling thread, not on a timer. No interactive login is ever launched.

### Bounded environment surface (Requirement 11.6)

Provider credentials are read only from each provider's standard variables — `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
`AWS_SESSION_TOKEN`, `AWS_BEARER_TOKEN_BEDROCK`, `GOOGLE_OAUTH_ACCESS_TOKEN`, `GOOGLE_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`,
the Azure and OpenAI-compatible equivalents — never from a prefixed variable. The only three prefixed variables are
`SKYE_LOG_LEVEL`, `SKYE_CONFIG`, `SKYE_ENABLE_TELEMETRY`, owned by `base` (D18); `auth` adds none.

## Data Models

`auth` owns the credential value objects, not the Ports (which are in `base`): `AwsCredentials` (access key, secret key,
optional session token, optional `expires_at`, with an `expired()` margin check) in `aws.py`, and the equivalent resolved
credential shapes for Google, Azure and the OAuth2 flows as they land. New structures are dataclasses, not pydantic (D24); the
existing `AwsCredentials` is already a frozen dataclass. These objects carry secrets, so they are never logged or put in a
repr beyond their class name.

## Error Handling

Errors use the `SkyeError` hierarchy from `base` and keep their context (`raise ... from e`). A missing or malformed
credential raises `ConfigurationError` naming the variable, file or profile at fault but never its value (as `aws.py` does
today). A failed HTTP exchange or metadata call maps to a `ProviderError` with the provider and status through `base/http.py`.
A mode that needs an earlier vendor-tool login whose cache is missing or expired raises an error that says to log in again
(Requirement 11.3). A use of a mode that needs `rsa` without the `auth` extra installed raises `MissingExtraError` naming the
extra, through the `missing_extra` helper. The `GoogleAuthError`/`ProviderError` path in `google.py` is the pattern.

## Testing Strategy

Tests are offline and deterministic, using fake credential and token endpoints built on the standard-library `http.server`
(as `tests/differential/fake_mcp_server.py` does), never real network. `tests/unit/auth` already covers the SigV4 signer
against the AWS documentation vector, the AWS credential sources (environment, profile, container, IMDSv2, Bedrock key) and
the Google authenticators (bearer, metadata caching, API key, resolver order, service-account hint). New modules add: the
token cache (hit, expiry-margin refresh, 401-triggered refresh-and-retry-once), RSA assertion minting (a known key and
payload, and `MissingExtraError` when `rsa` is absent), the Azure and OpenAI-compatible authenticators, the secret-manager
sources against fake endpoints, and the credential-source registry (register and resolve a custom source).

The deterministic budget tests guard the architecture: `test_import_matrix.py` (`auth` imports only `base`),
`test_extras_footprint.py` (`test_auth_extra_declares_exactly_rsa`: the `auth` extra declares exactly `rsa`, the `google`
extra does not), `test_codenames.py` (ozone appears only in the sanctioned places) and the clean-import test (`import skye`
and a core-only install pull neither `rsa` nor a provider library). The RSA minting in `rsa_signing.py` imports `rsa`, so the
declare-exactly check for `auth` runs on live code (the former `xfail` in `test_extras_footprint.py` is gone).

## Correctness Properties

*A property is a characteristic that should hold across all valid executions; it bridges the user stories and the tests.*

### Property 1: One Port authenticates every outbound request

For any supported mode, the caller obtains an `AuthenticationInterface` and calls `apply`; the request is authenticated
without any per-provider authentication code in the caller, and the input headers are never mutated.

**Validates: Requirement 1 (Requirement 11.1, 11.9 of steering)**

### Property 2: A 401 triggers exactly one refresh and retry

For any HTTP-exchange credential, a 401 response forces one refresh of the credential and one retry; a second 401 surfaces the
error rather than looping.

**Validates: Requirement 1 (Requirement 11.2 of steering)**

### Property 3: No secret leaves the component, no background work, no interactive login

For any error, log or repr produced by `auth`, no secret value appears; the component starts no background thread and runs no
long-lived process; no mode launches an interactive login, and a mode needing a vendor-tool cache raises a log-in-again error
when the cache is missing or expired.

**Validates: Requirement 1 (Requirement 11.3 of steering)**

### Property 4: `rsa` is the only third-party library, lazy and declared exactly

For any module under `auth`, a static scan finds no third-party import other than `rsa`, `rsa` is imported inside the function
that first mints a token, the `auth` extra declares exactly `rsa`, and the `google` extra never declares it.

**Validates: Requirement 1 (Requirement 11.4 of steering)**

### Property 5: A custom credential source enters through the registry alone

For any user-supplied credential source, registering it in the `auth` registry makes it resolvable, and adding it edits only
the `auth` component.

**Validates: Requirement 1 (Requirement 11.5 of steering)**

### Property 6: Bounded environment surface

For any credential read, the value comes from the provider's standard variable, never a prefixed one; the only prefixed
variables are the three owned by `base`.

**Validates: Requirement 1 (Requirement 11.6 of steering)**

## Open items

- **O6 is closed by D32:** `base/http.py` stays in `base`, and the cloud secret managers are in scope of `auth` (`secrets.py`).
- **Partial modes.** A Google external account takes its subject token from a file or a URL only (not from an AWS environment); the
  AWS SSO and Azure CLI caches are read and never refreshed, so an expired login says to log in again.
