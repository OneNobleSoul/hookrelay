from __future__ import annotations

import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from .sinks import OutboundRequest


@dataclass
class DeliveryResult:
    ok: bool
    attempts: int
    status: int | None = None
    error: str | None = None


def http_send(req: OutboundRequest, timeout: float = 10.0) -> int:
    request = urllib.request.Request(
        req.url, data=req.body, method=req.method, headers=req.headers
    )
    with urllib.request.urlopen(request, timeout=timeout) as resp:  # noqa: S310
        return resp.status


def deliver(
    req: OutboundRequest,
    sender: Callable[[OutboundRequest], int | None] = http_send,
    retries: int = 3,
    backoff: float = 0.5,
    sleeper: Callable[[float], None] = time.sleep,
) -> DeliveryResult:
    """Try to deliver, retrying with exponential backoff.

    `sender` and `sleeper` are injectable so tests don't hit the network or wait.
    """
    attempt = 0
    last_err: str | None = None
    while attempt < retries:
        attempt += 1
        try:
            status = sender(req)
            if status is not None and 200 <= status < 300:
                return DeliveryResult(True, attempt, status=status)
            last_err = f"status {status}"
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        if attempt < retries:
            sleeper(backoff * (2 ** (attempt - 1)))
    return DeliveryResult(False, attempt, error=last_err)
