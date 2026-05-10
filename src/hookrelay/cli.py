from __future__ import annotations

import argparse
import logging
import sys

from . import __version__
from .config import ConfigError, load_config
from .server import serve


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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    return args.func(args)
