from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .config import Config
from .delivery import deliver
from .matching import find_route, header_get
from .signature import verify
from .sinks import build_request
from .template import render

log = logging.getLogger("hookrelay")


def handle_webhook(
    config: Config, path: str, headers: dict, body_bytes: bytes
) -> tuple[int, str]:
    """Route + verify + render + fan out. Returns (status, message)."""
    try:
        payload = json.loads(body_bytes) if body_bytes else {}
    except json.JSONDecodeError:
        payload = {}
    body_dict = payload if isinstance(payload, dict) else {}

    route = find_route(config.routes, path, headers, body_dict)
    if route is None:
        return 404, "no matching route"

    if route.signature is not None:
        sig = route.signature
        provided = header_get(headers, sig.header)
        if not verify(sig.secret, body_bytes, provided, sig.algorithm, sig.prefix):
            return 401, "invalid signature"

    builtins = {
        "_route": route.name,
        "_path": path,
        "_body": body_bytes.decode("utf-8", "replace"),
    }
    text = render(
        route.template, body_dict, builtins=builtins, default=config.default_placeholder
    )

    delivered = 0
    for sink in route.sinks:
        req = build_request(sink, text)
        result = deliver(req, retries=config.retries, backoff=config.backoff)
        if result.ok:
            delivered += 1
        else:
            log.warning(
                "sink %s failed after %d attempts: %s",
                sink.type,
                result.attempts,
                result.error,
            )
    return 200, f"delivered to {delivered}/{len(route.sinks)} sinks"


def make_handler(config: Config):
    class Handler(BaseHTTPRequestHandler):
        server_version = "hookrelay"

        def do_POST(self):  # noqa: N802
            raw_length = self.headers.get("Content-Length")
            try:
                length = int(raw_length) if raw_length is not None else 0
            except ValueError:
                length = -1
            if length < 0:
                # malformed or negative Content-Length: bail out before rfile.read(),
                # which would otherwise block reading an unbounded/negative size and
                # tie up a worker thread indefinitely.
                self.close_connection = True
                self._respond(400, "invalid content-length")
                return
            if length > config.max_body_bytes:
                # don't buffer an oversized body into memory; the socket still
                # holds unread bytes, so close rather than risk a desync with
                # whatever the next request would be on a kept-alive connection.
                self.close_connection = True
                self._respond(413, "payload too large")
                return
            body = self.rfile.read(length) if length else b""
            status, msg = handle_webhook(config, self.path, dict(self.headers), body)
            self._respond(status, msg)

        def do_GET(self):  # noqa: N802
            self._respond(405, "method not allowed")

        def _respond(self, status: int, msg: str) -> None:
            data = msg.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt, *args):  # noqa: A002
            log.info("%s %s", self.address_string(), fmt % args)

    return Handler


def serve(config: Config) -> None:
    handler = make_handler(config)
    httpd = ThreadingHTTPServer((config.host, config.port), handler)
    log.info("listening on %s:%s", config.host, config.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("shutting down")
    finally:
        httpd.server_close()
