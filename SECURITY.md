# Security

hookrelay handles webhook secrets and forwards payloads, so a few notes.

If you find a security issue, please don't open a public issue. Email me at
75739931+UnterwegsDev@users.noreply.github.com with details and I'll get back to
you.

A couple of things worth knowing:

- Inbound signatures are checked with `hmac.compare_digest`, so the compare is
  timing-safe. Header name matching is case-insensitive.
- Secrets live in your config file in plain text. Keep it out of version control
  and lock down its permissions.
- Only the latest release gets fixes.
