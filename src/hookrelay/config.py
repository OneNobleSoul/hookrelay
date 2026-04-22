from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

VALID_SINKS = {"slack", "generic"}


class ConfigError(Exception):
    """Raised when a config file is missing required bits or malformed."""


@dataclass
class Match:
    path: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    body_equals: dict[str, object] = field(default_factory=dict)


@dataclass
class Signature:
    secret: str
    header: str = "X-Hub-Signature-256"
    algorithm: str = "sha256"
    prefix: str = ""


@dataclass
class Sink:
    type: str
    url: str
    options: dict = field(default_factory=dict)


@dataclass
class Route:
    name: str
    match: Match
    sinks: list[Sink]
    template: str = "{{ _body }}"
    signature: Signature | None = None


@dataclass
class Config:
    routes: list[Route]
    host: str = "127.0.0.1"
    port: int = 8080


def _parse_match(data: object, route_name: str) -> Match:
    if data is None:
        return Match()
    if not isinstance(data, dict):
        raise ConfigError(f"route {route_name!r}: match must be an object")
    headers = data.get("headers", {})
    body_equals = data.get("body_equals", {})
    if not isinstance(headers, dict):
        raise ConfigError(f"route {route_name!r}: match.headers must be an object")
    if not isinstance(body_equals, dict):
        raise ConfigError(f"route {route_name!r}: match.body_equals must be an object")
    return Match(path=data.get("path"), headers=dict(headers), body_equals=dict(body_equals))


def _parse_signature(data: object, route_name: str) -> Signature | None:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ConfigError(f"route {route_name!r}: signature must be an object")
    if not data.get("secret"):
        raise ConfigError(f"route {route_name!r}: signature.secret is required")
    return Signature(
        secret=str(data["secret"]),
        header=str(data.get("header", "X-Hub-Signature-256")),
        algorithm=str(data.get("algorithm", "sha256")),
        prefix=str(data.get("prefix", "")),
    )


def _parse_sink(data: object, route_name: str) -> Sink:
    if not isinstance(data, dict):
        raise ConfigError(f"route {route_name!r}: each sink must be an object")
    stype = data.get("type")
    if stype not in VALID_SINKS:
        raise ConfigError(
            f"route {route_name!r}: unknown sink type {stype!r} "
            f"(valid: {', '.join(sorted(VALID_SINKS))})"
        )
    url = data.get("url")
    if not url:
        raise ConfigError(f"route {route_name!r}: sink {stype!r} is missing a url")
    return Sink(type=stype, url=str(url), options=dict(data.get("options", {})))


def _parse_route(data: object) -> Route:
    if not isinstance(data, dict):
        raise ConfigError("each route must be an object")
    name = data.get("name")
    if not name:
        raise ConfigError("route is missing a name")
    sinks_data = data.get("sinks")
    if not isinstance(sinks_data, list) or not sinks_data:
        raise ConfigError(f"route {name!r}: needs at least one sink")
    sinks = [_parse_sink(s, name) for s in sinks_data]
    return Route(
        name=str(name),
        match=_parse_match(data.get("match"), name),
        sinks=sinks,
        template=str(data.get("template", "{{ _body }}")),
        signature=_parse_signature(data.get("signature"), name),
    )


def parse_config(data: object) -> Config:
    if not isinstance(data, dict):
        raise ConfigError("config root must be an object")
    routes_data = data.get("routes")
    if not isinstance(routes_data, list) or not routes_data:
        raise ConfigError("config needs a non-empty 'routes' list")
    routes = [_parse_route(r) for r in routes_data]
    return Config(
        routes=routes,
        host=str(data.get("host", "127.0.0.1")),
        port=int(data.get("port", 8080)),
    )


def load_config(path: str | Path) -> Config:
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"config file not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"{p}: invalid json: {e}") from e
    return parse_config(data)
