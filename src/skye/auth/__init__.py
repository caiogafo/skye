"""Authentication and credentials.

Component: auth. Layer: 0 (next to base). Imports only base.

Every outbound request is authenticated through one Port (``AuthenticationInterface``); this
component implements it for each provider's documented non-interactive modes and never launches a
login. Modules:

- ``sigv4``, ``aws``, ``aws_profile``, ``sts``: AWS (SigV4, Bedrock API key, environment, profile,
  container and instance credentials, assume-role, web identity, IAM Identity Center cache).
- ``google``: bearer, metadata server, API key, service account, authorized user, impersonation,
  Workload Identity Federation.
- ``azure``: API key, client secret, certificate, federated token, managed identity, CLI cache.
- ``openai_compatible``: API key and bearer for OpenAI-compatible providers, Anthropic and Cohere.
- ``oauth2``: client-credentials and token-exchange flows.
- ``cache``, ``refresh``: the lazy token cache and the 401 refresh-and-retry-once helper.
- ``rsa_signing``: RS256 assertions with the pure-Python ``rsa`` (extra ``auth``).
- ``secrets``: AWS Secrets Manager, SSM Parameter Store, Azure Key Vault, Google Secret Manager.
- ``registry``: the one extension point, a registry of credential sources.

`auth` is authentication and credentials; `policy` is authorization.

Codename: ozone.
"""
