from __future__ import annotations

import json
from dataclasses import dataclass, field

from .config import Sink

DISCORD_LIMIT = 2000


@dataclass
class OutboundRequest:
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    body: bytes = b""


def truncate(text: str, limit: int = DISCORD_LIMIT, marker: str = "...") -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + marker


def build_slack(url: str, text: str, options: dict | None = None) -> OutboundRequest:
    body = json.dumps({"text": text}).encode("utf-8")
    return OutboundRequest("POST", url, {"Content-Type": "application/json"}, body)


def build_discord(url: str, text: str, options: dict | None = None) -> OutboundRequest:
    body = json.dumps({"content": truncate(text)}).encode("utf-8")
    return OutboundRequest("POST", url, {"Content-Type": "application/json"}, body)


def build_ntfy(url: str, text: str, options: dict | None = None) -> OutboundRequest:
    options = options or {}
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    if options.get("title"):
        headers["Title"] = str(options["title"])
    if options.get("priority") is not None:
        headers["Priority"] = str(options["priority"])
    tags = options.get("tags")
    if tags:
        if isinstance(tags, (list, tuple)):
            tags = ",".join(str(t) for t in tags)
        headers["Tags"] = str(tags)
    return OutboundRequest("POST", url, headers, text.encode("utf-8"))


def build_generic(url: str, text: str, options: dict | None = None) -> OutboundRequest:
    options = options or {}
    headers = {"Content-Type": str(options.get("content_type", "application/json"))}
    for k, v in (options.get("headers") or {}).items():
        headers[str(k)] = str(v)
    return OutboundRequest("POST", url, headers, text.encode("utf-8"))


_BUILDERS = {
    "slack": build_slack,
    "discord": build_discord,
    "ntfy": build_ntfy,
    "generic": build_generic,
}


def build_request(sink: Sink, text: str) -> OutboundRequest:
    builder = _BUILDERS.get(sink.type)
    if builder is None:
        raise ValueError(f"unknown sink type: {sink.type}")
    return builder(sink.url, text, sink.options)
