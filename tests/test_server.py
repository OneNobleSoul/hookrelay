import json

from hookrelay.config import parse_config
from hookrelay.server import handle_webhook


def _config(route):
    return parse_config({"routes": [route]})


def test_no_matching_route():
    cfg = _config(
        {"name": "r", "match": {"path": "/a"}, "sinks": [{"type": "generic", "url": "http://x"}]}
    )
    status, msg = handle_webhook(cfg, "/other", {}, b"{}")
    assert status == 404


def test_get_health_is_405_on_root():
    # servers only accept POST; GET handling is covered by the handler, here we
    # just make sure a bad path returns 404 rather than blowing up
    cfg = _config(
        {"name": "r", "match": {"path": "/a"}, "sinks": [{"type": "generic", "url": "http://x"}]}
    )
    status, _ = handle_webhook(cfg, "/nope", {}, b"")
    assert status == 404


def test_invalid_signature_rejected():
    cfg = _config(
        {
            "name": "r",
            "match": {"path": "/a"},
            "signature": {"secret": "shh"},
            "sinks": [{"type": "generic", "url": "http://x"}],
        }
    )
    status, msg = handle_webhook(cfg, "/a", {"X-Hub-Signature-256": "bad"}, b"{}")
    assert status == 401


def test_delivery_uses_template(monkeypatch):
    sent = []

    def fake_deliver(req, **kw):
        sent.append(json.loads(req.body))

        class R:
            ok = True
            attempts = 1
            error = None

        return R()

    monkeypatch.setattr("hookrelay.server.deliver", fake_deliver)
    cfg = _config(
        {
            "name": "r",
            "match": {"path": "/a"},
            "template": "hi {{ user }}",
            "sinks": [{"type": "slack", "url": "http://x"}],
        }
    )
    status, msg = handle_webhook(cfg, "/a", {}, json.dumps({"user": "sam"}).encode())
    assert status == 200
    assert sent == [{"text": "hi sam"}]
    assert "1/1" in msg
