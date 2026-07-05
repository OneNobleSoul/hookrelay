# Contributing

Thanks for taking a look. This is a small personal tool but patches are welcome.

Setup:

```
pip install -e ".[dev]"
```

Before opening a PR:

```
ruff check .
pytest -q
```

Keep the runtime stdlib-only - no third-party runtime deps. Sink request builders
and the template renderer should stay pure functions so they're easy to test. If
you add behavior, add a test for it.
