from __future__ import annotations

import hashlib
import hmac


def compute(secret: str, body: bytes, algorithm: str = "sha256") -> str:
    algo = getattr(hashlib, algorithm, None)
    if algo is None or algorithm not in hashlib.algorithms_available:
        raise ValueError(f"unsupported algorithm: {algorithm}")
    return hmac.new(secret.encode("utf-8"), body, algo).hexdigest()


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
