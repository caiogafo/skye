"""Authentication for AWS requests: Bedrock API keys and SigV4 signing (Live).

``skye.auth.aws`` carries the standard-library authenticators. ``BedrockApiKeyAuthenticator``
adds a bearer token; ``SigV4Authenticator`` signs a request with SigV4. Both implement the
``AuthenticationInterface`` Port: ``apply(method, url, headers, body=b"")`` returns a new dict of
headers with authentication added, without touching the network.

This example passes explicit/static credentials so no metadata call fires. In production,
``CredentialProvider`` resolves credentials in order: explicit arguments, environment variables,
web identity, a named profile, the ECS container endpoint, then EC2 instance metadata (IMDSv2).

No secret values are printed, only the header names that authentication added.
"""

from skye.auth import AwsCredentials, BedrockApiKeyAuthenticator, SigV4Authenticator

URL = "https://bedrock-runtime.us-east-1.amazonaws.com/"


def main() -> None:
    # 1. A Bedrock API key becomes a bearer token.
    api_key_auth = BedrockApiKeyAuthenticator(api_key="demo")
    headers = api_key_auth.apply("GET", URL, {})
    print("BedrockApiKeyAuthenticator added headers:", sorted(headers))

    # 2. SigV4 signing with explicit static credentials (no CredentialProvider lookup, so no
    #    environment, profile or IMDS call is attempted).
    credentials = AwsCredentials(access_key="AKIAEXAMPLE", secret_key="secret")
    sigv4_auth = SigV4Authenticator(region="us-east-1", service="bedrock", credentials=credentials)
    signed = sigv4_auth.apply("GET", URL, {})
    print("SigV4Authenticator added headers:", sorted(signed))

    # In production, hand a CredentialProvider instead of static keys and it resolves the source
    # for you (environment, named profile, container or EC2 metadata):
    #   from skye.auth.aws import CredentialProvider
    #   provider = CredentialProvider(profile_name="prod", region="us-east-1")
    #   auth = SigV4Authenticator(region="us-east-1", service="bedrock", credentials=provider)


if __name__ == "__main__":
    main()
