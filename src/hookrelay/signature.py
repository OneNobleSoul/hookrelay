from __future__ import annotations

import hashlib
import hmac


def compute(secret: str, body: bytes, algorithm: str = "sha256") -> str:
    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"unsupported algorithm: {algorithm}")
    # pass the name straight to hmac/hashlib.new instead of getattr(hashlib, ...):
    # some entries in algorithms_available (ripemd160, sm3, sha512_224, md5-sha1)
    # have no matching hashlib module attribute and would falsely raise here.
    return hmac.new(secret.encode("utf-8"), body, algorithm).hexdigest()


def verify(
    secret: str,
    body: bytes,
    provided: str | None,
    algorithm: str = "sha256",
    prefix: str = "",
) -> bool:
    if not provided:
        return False
    if prefix and provided.startswith(prefix):
        provided = provided[len(prefix):]
    expected = compute(secret, body, algorithm)
    # timing-safe compare, don't leak length via early exit
    return hmac.compare_digest(expected, provided)
