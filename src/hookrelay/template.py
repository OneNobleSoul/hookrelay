from __future__ import annotations

import json
import re

# {{ dotted.path }} - names can contain letters, digits, underscore, dot, dash
_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_.\-]+)\s*\}\}")

_MISSING = object()


def get_path(data: object, dotted: str, default: object = None) -> object:
    """Walk a dotted path into nested dicts/lists. Returns default if missing."""
    cur = data
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list):
            try:
                idx = int(part)
            except ValueError:
                return default
            if -len(cur) <= idx < len(cur):
                cur = cur[idx]
            else:
                return default
        else:
            return default
    return cur


def _stringify(val: object) -> str:
    if isinstance(val, str):
        return val
    if isinstance(val, bool):
        return "true" if val else "false"
    if val is None:
        return ""
    if isinstance(val, (dict, list)):
        return json.dumps(val, separators=(",", ":"))
    return str(val)


def render(
    template: str,
    payload: object,
    builtins: dict | None = None,
) -> str:
    """Expand {{ dotted.path }} placeholders from payload.

    Keys starting with '_' are looked up in builtins (e.g. _route, _body).
    Missing keys render as an empty string.
    """
    ctx = builtins or {}

    def repl(m: re.Match) -> str:
        key = m.group(1)
        if key.startswith("_"):
            val = ctx.get(key, _MISSING)
        else:
            val = get_path(payload, key, default=_MISSING)
        if val is _MISSING:
            return ""
        return _stringify(val)

    return _PLACEHOLDER.sub(repl, template)
