# auth

What you learn: a custom credential source. Read in this order:

1. `credential_sources.py`: Authentication for AWS requests: Bedrock API keys and SigV4 signing (Live)
2. `custom_credential_source.py`: Your own authenticator behind the AuthenticationInterface Port (Live)

Run: `python examples/auth/credential_sources.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
