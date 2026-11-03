"""Handling provider errors; retry lives at the router (proposed-interface, guarded).

This example shows the real ``ProviderError`` type and how the ``SkyeError`` hierarchy
lets you catch provider failures with one ``except``. It does not fake a retry switch:
transient-error retry is a router-level concern, configured where a request is routed
across providers (see ``examples/routing``), not a per-call flag on a model client.

Every error line that is provoked on purpose contains the word ``Expected`` so the
offline harness reads it as a deliberate demonstration rather than a real failure.
"""

from skye.base.exceptions import ProviderError, SkyeError


def main() -> None:
    # A ProviderError carries the provider name and, when known, an HTTP status code.
    transient = ProviderError(
        "upstream was briefly unavailable", provider="openai", status_code=503
    )

    try:
        raise transient
    except SkyeError as error:
        print("Expected caught a provider failure through the SkyeError umbrella:")
        print(f"  type    : {type(error).__name__}")
        print(f"  message : {error.message}")
        print(f"  provider: {error.details.get('provider')}")
        print(f"  status  : {error.details.get('status_code')}")

    status = transient.details.get("status_code")
    retryable = isinstance(status, int) and status in (429, 500, 502, 503, 504)
    print(f"\nLooks retryable at the router level: {retryable}")
    print("Configure retry where requests are routed, not per call; see examples/routing.")


if __name__ == "__main__":
    main()
