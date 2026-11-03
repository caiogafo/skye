"""RS256 assertions: a known key, PKCS#1 and PKCS#8, and the missing extra."""

import base64
import json
import sys

import pytest

from skye.auth import rsa_signing as r
from skye.base.exceptions import ConfigurationError, MissingExtraError

rsa = pytest.importorskip("rsa")


def _der(tag: int, content: bytes) -> bytes:
    n = len(content)
    head = (
        bytes([n]) if n < 0x80 else bytes([0x80 | len(n.to_bytes(2, "big"))]) + n.to_bytes(2, "big")
    )
    return bytes([tag]) + head + content


def _pem(label: str, der: bytes) -> str:
    body = base64.encodebytes(der).decode()
    return f"-----BEGIN {label}-----\n{body}-----END {label}-----\n"


@pytest.fixture(scope="module")
def key():
    _, private = rsa.newkeys(1024)
    return private


@pytest.fixture(scope="module")
def pkcs1(key):
    return key.save_pkcs1().decode()


@pytest.fixture(scope="module")
def pkcs8(key):
    algorithm = _der(0x30, bytes.fromhex("06092a864886f70d0101010500"))  # rsaEncryption, NULL
    inner = _der(0x04, key.save_pkcs1("DER"))
    return _pem("PRIVATE KEY", _der(0x30, _der(0x02, b"\x00") + algorithm + inner))


def _parts(jwt: str):
    h, p, s = jwt.split(".")
    pad = lambda x: x + "=" * (-len(x) % 4)  # noqa: E731
    return (
        json.loads(base64.urlsafe_b64decode(pad(h))),
        json.loads(base64.urlsafe_b64decode(pad(p))),
        base64.urlsafe_b64decode(pad(s)),
    )


@pytest.mark.parametrize("which", ["pkcs1", "pkcs8"])
def test_the_jwt_verifies_with_the_public_key(which, request, key):
    pem = request.getfixturevalue(which)
    jwt = r.sign_rs256_jwt({"iss": "me", "n": 1}, pem, headers={"kid": "k1"})
    header, payload, signature = _parts(jwt)
    assert header == {"alg": "RS256", "typ": "JWT", "kid": "k1"} and payload == {
        "iss": "me",
        "n": 1,
    }
    public = rsa.PublicKey(key.n, key.e)
    assert rsa.verify(jwt.rsplit(".", 1)[0].encode(), signature, public) == "SHA-256"


def test_service_account_assertion_claims(pkcs8):
    info = {
        "client_email": "sa@p.iam",
        "private_key": pkcs8,
        "private_key_id": "kid9",
        "token_uri": "https://t/token",
    }
    header, payload, _ = _parts(
        r.service_account_assertion(info, "scope-a scope-b", clock=lambda: 1000)
    )
    assert header["kid"] == "kid9"
    assert payload == {
        "iss": "sa@p.iam",
        "scope": "scope-a scope-b",
        "aud": "https://t/token",
        "iat": 1000,
        "exp": 4600,
    }


def test_a_service_account_file_missing_a_field_names_it(pkcs8):
    with pytest.raises(ConfigurationError, match="client_email"):
        r.service_account_assertion({"private_key": pkcs8}, "s")


def test_entra_assertion_carries_the_certificate_thumbprint(pkcs1):
    cert = _pem("CERTIFICATE", b"not-a-real-cert-der")
    header, payload, _ = _parts(
        r.entra_client_assertion("tenant", "client", pkcs1, cert, clock=lambda: 50)
    )
    assert header["x5t#S256"] == r.certificate_thumbprint(cert)
    assert payload["iss"] == payload["sub"] == "client" and payload["aud"].endswith(
        "/tenant/oauth2/v2.0/token"
    )
    assert payload["exp"] == 650


def test_bad_keys_are_configuration_errors_that_never_echo_the_key():
    with pytest.raises(ConfigurationError) as caught:
        r.sign_rs256_jwt({}, "-----BEGIN PRIVATE KEY-----\nAAAA\n-----END PRIVATE KEY-----")
    assert "AAAA" not in str(caught.value)
    with pytest.raises(ConfigurationError):
        r.sign_rs256_jwt({}, "no key here")
    with pytest.raises(ConfigurationError, match="encrypted"):
        r.sign_rs256_jwt({}, _pem("ENCRYPTED PRIVATE KEY", b"x"))
    with pytest.raises(ConfigurationError):
        r.certificate_thumbprint("nothing")


def test_without_rsa_the_error_names_the_extra(monkeypatch, pkcs1):
    monkeypatch.setitem(sys.modules, "rsa", None)
    with pytest.raises(MissingExtraError) as caught:
        r.sign_rs256_jwt({}, pkcs1)
    assert "auth" in str(caught.value)
