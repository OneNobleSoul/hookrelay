import json

import pytest

from hookrelay.config import Sink
from hookrelay.sinks import (
    DISCORD_LIMIT,
    build_discord,
    build_generic,
    build_ntfy,
    build_request,
    build_slack,
    truncate,
)


def test_slack_payload():
    req = build_slack("http://slack", "hello")
    assert req.method == "POST"
    assert json.loads(req.body) == {"text": "hello"}
    assert req.headers["Content-Type"] == "application/json"


def test_discord_payload():
    req = build_discord("http://d", "hey")
    assert json.loads(req.body) == {"content": "hey"}


def test_discord_no_truncation_at_limit():
    text = "a" * DISCORD_LIMIT
    req = build_discord("http://d", text)
    assert json.loads(req.body)["content"] == text


def test_discord_truncation_over_limit():
    text = "a" * (DISCORD_LIMIT + 500)
    content = json.loads(build_discord("http://d", text).body)["content"]
    assert len(content) == DISCORD_LIMIT
    assert content.endswith("...")


def test_truncate_short_unchanged():
    assert truncate("hi", limit=10) == "hi"


def test_truncate_tiny_limit():
    assert truncate("hello", limit=2) == ".."


def test_ntfy_headers():
    req = build_ntfy(
        "http://n", "body", {"title": "T", "priority": 4, "tags": ["warning", "skull"]}
    )
    assert req.body == b"body"
    assert req.headers["Title"] == "T"
    assert req.headers["Priority"] == "4"
    assert req.headers["Tags"] == "warning,skull"


def test_ntfy_no_options():
    req = build_ntfy("http://n", "body")
    assert "Title" not in req.headers
    assert "Priority" not in req.headers


def test_ntfy_string_tags():
    req = build_ntfy("http://n", "b", {"tags": "warning"})
    assert req.headers["Tags"] == "warning"


def test_generic_default_content_type():
    req = build_generic("http://g", "raw")
    assert req.headers["Content-Type"] == "application/json"
    assert req.body == b"raw"


def test_generic_custom_headers():
    req = build_generic(
        "http://g", "x", {"content_type": "text/plain", "headers": {"X-Token": "abc"}}
    )
    assert req.headers["Content-Type"] == "text/plain"
    assert req.headers["X-Token"] == "abc"


def test_build_request_dispatch():
    req = build_request(Sink("slack", "http://s"), "hi")
    assert json.loads(req.body) == {"text": "hi"}


def test_build_request_unknown():
    with pytest.raises(ValueError):
        build_request(Sink("carrier-pigeon", "http://p"), "hi")
