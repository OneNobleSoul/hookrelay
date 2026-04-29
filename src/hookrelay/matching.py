from __future__ import annotations

from .config import Route
from .template import get_path

_MISSING = object()


def header_get(headers: dict, name: str) -> str | None:
    """Case-insensitive header lookup. Incoming header casing is unpredictable."""
    lname = name.lower()
    for k, v in headers.items():
        if k.lower() == lname:
            return v
    return None


def match_route(route: Route, path: str, headers: dict, body: dict) -> bool:
    m = route.match
    if m.path is not None and m.path != path:
        return False
    for name, expected in m.headers.items():
        if header_get(headers, name) != expected:
            return False
    for dotted, expected in m.body_equals.items():
        if get_path(body, dotted, default=_MISSING) != expected:
            return False
    return True


def find_route(routes: list[Route], path: str, headers: dict, body: dict) -> Route | None:
    for route in routes:
        if match_route(route, path, headers, body):
            return route
    return None
