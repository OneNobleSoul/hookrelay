from __future__ import annotations

import json
from dataclasses import dataclass, field

from .config import Sink


@dataclass
class OutboundRequest:
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    body: bytes = b""


def build_slack(url: str, text: str, options: dict | None = None) -> OutboundRequest:
    body = json.dumps({"text": text}).encode("utf-8")
    return OutboundRequest("POST", url, {"Content-Type": "application/json"}, body)


def build_generic(url: str, text: str, options: dict | None = None) -> OutboundRequest:
    options = options or {}
    headers = {"Content-Type": str(options.get("content_type", "application/json"))}
    for k, v in (options.get("headers") or {}).items():
        headers[str(k)] = str(v)
    return OutboundRequest("POST", url, headers, text.encode("utf-8"))


_BUILDERS = {
    "slack": build_slack,
    "generic": build_generic,
}


def build_request(sink: Sink, text: str) -> OutboundRequest:
    builder = _BUILDERS.get(sink.type)
    if builder is None:
        raise ValueError(f"unknown sink type: {sink.type}")
    return builder(sink.url, text, sink.options)
