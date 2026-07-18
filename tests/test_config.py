import json

import pytest

from hookrelay.config import ConfigError, load_config, parse_config

BASE = {
    "routes": [
        {
            "name": "r1",
            "match": {"path": "/a"},
            "sinks": [{"type": "slack", "url": "http://s"}],
        }
    ]
}


def test_parse_defaults():
    cfg = parse_config(BASE)
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8080
    assert cfg.retries == 3
    assert len(cfg.routes) == 1
    assert cfg.routes[0].template == "{{ _body }}"


def test_parse_overrides():
    cfg = parse_config({**BASE, "host": "0.0.0.0", "port": 9000, "retries": 5})
    assert cfg.host == "0.0.0.0"
    assert cfg.port == 9000
    assert cfg.retries == 5


def test_max_body_bytes_default():
    cfg = parse_config(BASE)
    assert cfg.max_body_bytes == 1_048_576


def test_max_body_bytes_override():
    cfg = parse_config({**BASE, "max_body_bytes": 4096})
    assert cfg.max_body_bytes == 4096


def test_max_body_bytes_must_be_positive():
    with pytest.raises(ConfigError):
        parse_config({**BASE, "max_body_bytes": 0})


def test_missing_routes():
    with pytest.raises(ConfigError):
        parse_config({})


def test_empty_routes():
    with pytest.raises(ConfigError):
        parse_config({"routes": []})


def test_route_missing_name():
    with pytest.raises(ConfigError):
        parse_config({"routes": [{"sinks": [{"type": "slack", "url": "http://s"}]}]})


def test_route_no_sinks():
    with pytest.raises(ConfigError):
        parse_config({"routes": [{"name": "r", "sinks": []}]})


def test_unknown_sink_type():
    bad = {"routes": [{"name": "r", "sinks": [{"type": "fax", "url": "http://s"}]}]}
    with pytest.raises(ConfigError):
        parse_config(bad)


def test_sink_missing_url():
    bad = {"routes": [{"name": "r", "sinks": [{"type": "slack"}]}]}
    with pytest.raises(ConfigError):
        parse_config(bad)


def test_signature_requires_secret():
    bad = {
        "routes": [
            {
                "name": "r",
                "signature": {"header": "X-Sig"},
                "sinks": [{"type": "slack", "url": "http://s"}],
            }
        ]
    }
    with pytest.raises(ConfigError):
        parse_config(bad)


def test_signature_rejects_unsupported_algorithm():
    bad = {
        "routes": [
            {
                "name": "r",
                "signature": {"secret": "shh", "algorithm": "sha265"},
                "sinks": [{"type": "slack", "url": "http://s"}],
            }
        ]
    }
    with pytest.raises(ConfigError):
        parse_config(bad)


def test_signature_parsed():
    data = {
        "routes": [
            {
                "name": "r",
                "signature": {"secret": "shh", "prefix": "sha256="},
                "sinks": [{"type": "slack", "url": "http://s"}],
            }
        ]
    }
    cfg = parse_config(data)
    assert cfg.routes[0].signature.secret == "shh"
    assert cfg.routes[0].signature.prefix == "sha256="


def test_duplicate_route_names():
    data = {
        "routes": [
            {"name": "dup", "sinks": [{"type": "slack", "url": "http://s"}]},
            {"name": "dup", "sinks": [{"type": "slack", "url": "http://s"}]},
        ]
    }
    with pytest.raises(ConfigError):
        parse_config(data)


def test_load_config_from_file(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps(BASE), encoding="utf-8")
    cfg = load_config(p)
    assert cfg.routes[0].name == "r1"


def test_load_config_missing_file(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "nope.json")


def test_load_config_bad_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(p)
