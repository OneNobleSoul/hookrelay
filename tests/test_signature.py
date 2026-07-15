import hashlib
import hmac

import pytest

from hookrelay.signature import compute, verify


def test_compute_matches_hmac():
    body = b'{"a":1}'
    expected = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert compute("secret", body) == expected


def test_verify_valid():
    body = b"payload"
    sig = compute("secret", body)
    assert verify("secret", body, sig)


def test_verify_invalid():
    assert not verify("secret", b"payload", "deadbeef")


def test_verify_wrong_secret():
    body = b"payload"
    sig = compute("secret", body)
    assert not verify("other", body, sig)


def test_verify_with_prefix():
    body = b"payload"
    sig = "sha256=" + compute("secret", body)
    assert verify("secret", body, sig, prefix="sha256=")


def test_verify_none_provided():
    assert not verify("secret", b"payload", None)


def test_verify_empty_provided():
    assert not verify("secret", b"payload", "")


def test_unsupported_algorithm():
    with pytest.raises(ValueError):
        compute("secret", b"x", algorithm="rot13")


def test_compute_algorithm_without_hashlib_attribute():
    # ripemd160 is in hashlib.algorithms_available on most builds but has no
    # hashlib.ripemd160 attribute, so getattr(hashlib, ...) would wrongly
    # reject it even though it's a valid, config-approved algorithm.
    if "ripemd160" not in hashlib.algorithms_available:
        pytest.skip("ripemd160 not available on this build")
    expected = hmac.new(b"secret", b"x", "ripemd160").hexdigest()
    assert compute("secret", b"x", algorithm="ripemd160") == expected
