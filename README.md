# hookrelay

A tiny self-hosted webhook relay. It listens for inbound webhooks, matches them
against routes you define in a small JSON config, optionally verifies an HMAC
signature, renders a message from the payload, and forwards it to a sink.

No framework, no database, stdlib only.

## Install

```sh
pip install -e .
```

Python 3.11+.

## Quick start

Write a config (see `examples/config.json`), then:

```sh
hookrelay check -c config.json   # validate and print a summary
hookrelay run -c config.json     # start the server
```

## Config

Each route has a `match` (path, headers, body_equals), an optional `signature`
block for HMAC verification, a `template` string, and one or more `sinks`.
Sinks are `slack` or `generic` for now.

Templates expand `{{ dotted.path }}` placeholders from the JSON payload. A few
builtins are available: `{{ _route }}`, `{{ _path }}`, `{{ _body }}`.

## License

MIT.
