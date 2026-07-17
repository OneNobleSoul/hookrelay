import json

import hookrelay.cli as cli

BASE_CONFIG = {
    "routes": [
        {
            "name": "r1",
            "match": {"path": "/a"},
            "sinks": [{"type": "generic", "url": "http://example.invalid"}],
        }
    ]
}


def _write_config(tmp_path, data):
    p = tmp_path / "config.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_run_missing_config_prints_clean_error(tmp_path, capsys):
    missing = str(tmp_path / "does-not-exist.json")
    rc = cli.main(["run", "-c", missing])
    assert rc == 1
    err = capsys.readouterr().err
    assert "config error:" in err
    assert "Traceback" not in err


def test_run_invalid_config_prints_clean_error(tmp_path, capsys):
    # missing required 'routes' key
    path = _write_config(tmp_path, {})
    rc = cli.main(["run", "-c", path])
    assert rc == 1
    err = capsys.readouterr().err
    assert "config error:" in err
    assert "Traceback" not in err


def test_run_valid_config_starts_server(tmp_path, monkeypatch):
    path = _write_config(tmp_path, BASE_CONFIG)
    calls = []
    monkeypatch.setattr(cli, "serve", lambda config: calls.append(config))
    rc = cli.main(["run", "-c", path])
    assert rc == 0
    assert len(calls) == 1
    assert calls[0].routes[0].name == "r1"
