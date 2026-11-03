---
title: "auth"
codename: "ozone"
status: current
last_updated: 2026-11-03
---

# auth

*codename: ozone*

Authentication and credentials: strategies, credential sources and a token cache. Authorization is `policy`.

Every outbound request is authenticated through one Port, `AuthenticationInterface.apply(method, url, headers, body)`, which returns a
new header dict and never changes the input. `auth` implements it for each provider's documented, non-interactive modes. No mode runs
an interactive login: where one needs an earlier `aws sso login`, `az login` or `gcloud auth application-default login`, `auth` reads
the cache that tool left and, if it is missing or expired, raises `LoginRequiredError` saying which command to run again.

| Provider | Modes |
|---|---|
| AWS | environment, profile keys, container credentials, IMDSv2, assume-role (also cross-account), web identity, IAM Identity Center (cache), Bedrock API key |
| Google | access token, API key, service account (RS256), authorized user, impersonation, Workload Identity Federation, metadata server, gcloud login (cache) |
| Microsoft Entra ID (Azure OpenAI) | API key, client secret, certificate (RS256), federated token file, managed identity, `az login` (cache) |
| OpenAI-compatible, Anthropic, Cohere | API key or bearer, from the provider's standard variable |
| Any OAuth2 server | client credentials, token exchange |
| Secrets | AWS Secrets Manager, SSM Parameter Store, Azure Key Vault, Google Secret Manager |

```python
from skye.auth.registry import resolve_credential_source

auth = resolve_credential_source("google")                       # picks the first usable mode
vault = resolve_credential_source("aws-secrets-manager", region="eu-west-1")
password = vault.get("prod/db/password")
```

## Rules that hold everywhere
- **No secret leaves the component:** none in a log, a `repr` or an error; errors name the variable or file, never its value.
- **No background work:** the token cache refreshes on the calling thread, a little before a token expires; no timer, no thread, no subprocess.
- **A 401 refreshes once:** `skye.auth.refresh.send_with_refresh` refreshes the credential and retries the request once; a second 401 is raised.
- **Provider-standard variables only:** `AWS_*`, `GOOGLE_*`, `AZURE_*`, `OPENAI_API_KEY` and the like; the only prefixed variables of the library are the three of `base`.
- **One third-party library:** `rsa`, in the extra `auth` (`pip install skyeai[auth]`), imported only when a token is signed. Without it `MissingExtraError` names the extra.

## Your own source
Register a factory under a name; it can return an authenticator or a secret source with `get(name)`.

```python
from skye.auth.registry import register_credential_source, resolve_credential_source

register_credential_source("vault", lambda **config: MyVaultAuth(**config))
auth = resolve_credential_source("vault", token="...")
```
