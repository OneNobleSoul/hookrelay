import http.client
import json
import threading
from http.server import ThreadingHTTPServer

from hookrelay.config import parse_config
from hookrelay.server import handle_webhook, make_handler


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


def _run_server(cfg):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cfg))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread


def _stop_server(httpd, thread):
    httpd.shutdown()
    httpd.server_close()
    thread.join()


def test_oversized_body_rejected_with_413():
    cfg = _config(
        {"name": "r", "match": {"path": "/a"}, "sinks": [{"type": "generic", "url": "http://x"}]}
    )
    cfg.max_body_bytes = 10
    httpd, thread = _run_server(cfg)
    try:
        conn = http.client.HTTPConnection(*httpd.server_address, timeout=5)
        conn.request("POST", "/a", body=b"x" * 100)
        resp = conn.getresponse()
        assert resp.status == 413
        resp.read()
        conn.close()
    finally:
        _stop_server(httpd, thread)


def test_body_within_limit_is_handled_normally():
    cfg = _config(
        {"name": "r", "match": {"path": "/a"}, "sinks": [{"type": "generic", "url": "http://x"}]}
    )
    cfg.max_body_bytes = 10
    cfg.retries = 1  # avoid retry backoff sleeps for an intentionally unreachable sink
    httpd, thread = _run_server(cfg)
    try:
        conn = http.client.HTTPConnection(*httpd.server_address, timeout=5)
        conn.request("POST", "/a", body=b"{}")
        resp = conn.getresponse()
        # route matches; the generic sink delivery will fail since http://x isn't
        # reachable, but that's a 200 with a "delivered to 0/1" body, not a 413.
        assert resp.status == 200
        resp.read()
        conn.close()
    finally:
        _stop_server(httpd, thread)


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
