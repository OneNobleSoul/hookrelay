# Changelog

## 0.2.0
- add ntfy and discord sinks
- `send` subcommand for one-off delivery
- retry with exponential backoff, injectable sleeper

## 0.1.0
- first cut: inbound server, path/header/body matching, slack + generic sinks,
  HMAC signature check, `run` and `check` subcommands
