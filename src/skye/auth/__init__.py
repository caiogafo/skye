"""Authentication and credentials.

Component: auth. Layer: 0 (next to base). Imports only base. Empty this phase: the strategies
(API key, bearer, SigV4, OAuth2) and credential sources (environment, files, instance metadata,
cloud secret managers) are the authentication milestone of the auth and models specs. The only
module so far is the stdlib SigV4 signer moved here from models/transport.

`auth` is authentication and credentials; `policy` is authorization.

`aws` holds the stdlib AWS authenticators (SigV4, Bedrock API key) and credential sources.

Codename: ozone.
"""
