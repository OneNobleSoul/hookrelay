# hookrelay

A small self-hosted webhook relay. It listens for inbound HTTP webhooks, filters
them, renders a message, and fans out to chat/notification sinks (Slack, Discord,
ntfy, or a generic HTTP endpoint).

I got tired of wiring the same little webhook glue for every service - forward
this GitHub event to that Slack channel, drop those alerts into ntfy, etc. This is
that glue, in one config file, with no runtime dependencies beyond the standard
library.

## Install

```
pipx install hookrelay
```

Runtime is stdlib only (Python 3.11+). Dev extras (`pytest`, `ruff`) live under the
`dev` optional group.

## Config

A config is a JSON file with a list of routes. Each route matches incoming
requests, optionally checks an HMAC signature, renders a template, and delivers to
one or more sinks.

```json
{
  "host": "127.0.0.1",
  "port": 8080,
  "retries": 3,
  "backoff": 0.5,
  "routes": [
    {
      "name": "github-push",
      "match": {
        "path": "/hooks/github",
        "headers": { "X-GitHub-Event": "push" },
        "body_equals": { "ref": "refs/heads/main" }
      },
      "signature": {
        "secret": "change-me",
        "header": "X-Hub-Signature-256",
        "prefix": "sha256="
      },
      "template": "{{ pusher.name }} pushed to {{ repository.full_name }}",
      "sinks": [
        { "type": "slack", "url": "https://hooks.slack.com/services/XXX/YYY/ZZZ" }
      ]
    }
  ]
}
```

## Usage

Validate a config and print a summary:

```
hookrelay check -c config.json
```

Start the server:

```
hookrelay run -c config.json
```

Render and deliver a route once without running the server - handy for testing a
new route or template:

```
hookrelay send -c config.json --route github-push --data @sample.json
echo '{"status":"firing","title":"disk full"}' | hookrelay send -c config.json --route alerts --data -
```

## Sinks

- `slack` - posts `{"text": ...}` to an incoming-webhook url.
- `discord` - posts `{"content": ...}`, truncated to Discord's 2000 char limit.
- `ntfy` - POSTs the body to a topic url. `options` may set `title`, `priority`
  (1-5) and `tags` (list or comma string), sent as the matching headers.
- `generic` - POSTs the rendered text to any url. `options.content_type` and
  `options.headers` let you shape the request.

## How matching works

A route matches when *all* of the conditions it declares are true:

- `path` equals the request path (omit to match any path).
- every entry in `headers` matches the incoming header (case-insensitive names).
- every entry in `body_equals` equals the value at that (dotted) path in the JSON
  body, e.g. `"ref": "refs/heads/main"`.

Routes are checked in order; the first match wins.

## Templating

Templates expand `{{ dotted.path }}` placeholders from the JSON body. List indices
work too (`{{ commits.0.id }}`). A few built-ins are available: `{{ _route }}`,
`{{ _path }}` and `{{ _body }}` (the raw body). Missing keys render empty by
default, or set `default_placeholder` in the config.

## Signatures

If a route has a `signature` block, the raw request body is verified with
`hmac.compare_digest` against the given header before anything else runs. Wrong or
missing signature returns 401.

## Limitations

- No hot reload yet - restart to pick up config changes.
- Delivery retries use plain exponential backoff, no jitter.
- No built-in auth on the admin/health surface (there isn't one; it only speaks
  webhooks).
- One process, threaded. Fine for personal use, not meant to be a queue.

## License

MIT
