from __future__ import annotations

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
) -> DeliveryResult:
    try:
        status = sender(req)
        if status is not None and 200 <= status < 300:
            return DeliveryResult(True, 1, status=status)
        return DeliveryResult(False, 1, error=f"status {status}")
    except Exception as e:  # noqa: BLE001
        return DeliveryResult(False, 1, error=str(e))
