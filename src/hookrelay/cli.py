from __future__ import annotations

import argparse
import json
import logging
import sys

from . import __version__
from .config import ConfigError, Route, load_config
from .delivery import deliver
from .server import serve
from .sinks import build_request
from .template import render


def _read_data(spec: str | None) -> str:
    if spec is None:
        return ""
    if spec == "-":
        return sys.stdin.read()
    if spec.startswith("@"):
        with open(spec[1:], encoding="utf-8") as f:
            return f.read()
    return spec


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    serve(config)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 1
    print(f"ok: {len(config.routes)} route(s), bind {config.host}:{config.port}")
    for r in config.routes:
        sinks = ", ".join(s.type for s in r.sinks)
        path = r.match.path or "(any path)"
        sig = " [signed]" if r.signature else ""
        print(f"  - {r.name}: {path} -> {sinks}{sig}")
    return 0


def _deliver_once(config, route: Route, raw: str) -> int:
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as e:
        print(f"invalid json data: {e}", file=sys.stderr)
        return 1
    body_dict = payload if isinstance(payload, dict) else {}
    builtins = {"_route": route.name, "_path": route.match.path or "", "_body": raw}
    text = render(route.template, body_dict, builtins=builtins)
    print(f"rendered: {text}")
    failures = 0
    for sink in route.sinks:
        req = build_request(sink, text)
        result = deliver(req, retries=config.retries, backoff=config.backoff)
        if result.ok:
            print(f"  {sink.type} -> ok ({result.status})")
        else:
            failures += 1
            print(f"  {sink.type} -> failed: {result.error}")
    return 1 if failures else 0


def cmd_send(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 1
    route = next((r for r in config.routes if r.name == args.route), None)
    if route is None:
        print(f"no such route: {args.route}", file=sys.stderr)
        return 1
    return _deliver_once(config, route, _read_data(args.data))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hookrelay", description="tiny self-hosted webhook relay"
    )
    parser.add_argument(
        "--version", action="version", version=f"hookrelay {__version__}"
    )
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="start the relay server")
    p_run.add_argument("-c", "--config", required=True)
    p_run.set_defaults(func=cmd_run)

    p_check = sub.add_parser("check", help="validate a config and print a summary")
    p_check.add_argument("-c", "--config", required=True)
    p_check.set_defaults(func=cmd_check)

    p_send = sub.add_parser("send", help="render + deliver a route once")
    p_send.add_argument("-c", "--config", required=True)
    p_send.add_argument("--route", required=True)
    p_send.add_argument("--data", help="inline json, @file, or - for stdin")
    p_send.set_defaults(func=cmd_send)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    return args.func(args)
