"""The credential-source registry: register a custom source and resolve it by name."""

import pytest

from skye.auth import registry
from skye.auth.openai_compatible import BearerAuth
from skye.base.exceptions import ConfigurationError
from skye.base.interfaces.authentication import AuthenticationInterface


class VaultAuth:
    def __init__(self, token="t"):
        self._token = token

    def apply(self, method, url, headers, body=b""):
        return {**headers, "X-Vault-Token": self._token}


@pytest.fixture(autouse=True)
def isolated():
    before = dict(registry._custom)
    yield
    registry._custom.clear()
    registry._custom.update(before)


def test_a_custom_source_is_registered_and_resolved_by_name():
    registry.register_credential_source("vault", VaultAuth)
    assert "vault" in registry.list_credential_sources()
    source = registry.resolve_credential_source("vault", token="abc")
    assert isinstance(source, AuthenticationInterface)
    assert source.apply("GET", "u", {}) == {"X-Vault-Token": "abc"}


def test_a_name_in_use_needs_replace_and_unregister_removes_it():
    registry.register_credential_source("vault", VaultAuth)
    with pytest.raises(ConfigurationError, match="already registered"):
        registry.register_credential_source("vault", VaultAuth)
    registry.register_credential_source("vault", lambda **kw: "replaced", replace=True)
    assert registry.resolve_credential_source("vault") == "replaced"
    registry.unregister_credential_source("vault")
    with pytest.raises(ConfigurationError, match="No credential source named 'vault'"):
        registry.resolve_credential_source("vault")


def test_a_built_in_name_cannot_be_taken_by_accident():
    with pytest.raises(ConfigurationError):
        registry.register_credential_source("google", VaultAuth)


def test_bad_registrations_are_rejected():
    with pytest.raises(ConfigurationError):
        registry.register_credential_source("", VaultAuth)
    with pytest.raises(ConfigurationError):
        registry.register_credential_source("x", "not callable")  # type: ignore[arg-type]


def test_the_built_in_sources_resolve_lazily():
    names = registry.list_credential_sources()
    for expected in ("openai", "google", "azure", "aws", "aws-secrets-manager", "azure-key-vault"):
        assert expected in names
    assert isinstance(registry.resolve_credential_source("openai", api_key="k"), BearerAuth)


def test_the_unknown_name_error_lists_what_exists():
    with pytest.raises(ConfigurationError) as caught:
        registry.resolve_credential_source("nope")
    assert "openai" in str(caught.value)
