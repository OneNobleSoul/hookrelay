from hookrelay.config import Match, Route, Sink
from hookrelay.matching import find_route, header_get, match_route


def _route(**kw):
    match = kw.pop("match", Match())
    return Route(name=kw.pop("name", "r"), match=match, sinks=[Sink("generic", "http://x")])


def test_header_get_case_insensitive():
    headers = {"X-GitHub-Event": "push"}
    assert header_get(headers, "x-github-event") == "push"


def test_header_get_missing():
    assert header_get({}, "x-none") is None


def test_match_by_path():
    r = _route(match=Match(path="/gh"))
    assert match_route(r, "/gh", {}, {})


def test_no_match_wrong_path():
    r = _route(match=Match(path="/gh"))
    assert not match_route(r, "/other", {}, {})


def test_match_any_path_when_none():
    r = _route(match=Match(path=None))
    assert match_route(r, "/whatever", {}, {})


def test_header_match_case_insensitive():
    r = _route(match=Match(headers={"X-GitHub-Event": "push"}))
    assert match_route(r, "/", {"x-github-event": "push"}, {})


def test_header_mismatch():
    r = _route(match=Match(headers={"X-GitHub-Event": "push"}))
    assert not match_route(r, "/", {"X-GitHub-Event": "pull_request"}, {})


def test_body_equals_match():
    r = _route(match=Match(body_equals={"ref": "refs/heads/main"}))
    assert match_route(r, "/", {}, {"ref": "refs/heads/main"})


def test_body_equals_nested():
    r = _route(match=Match(body_equals={"action": "opened"}))
    assert not match_route(r, "/", {}, {"action": "closed"})


def test_find_route_returns_first_match():
    a = _route(name="a", match=Match(path="/a"))
    b = _route(name="b", match=Match(path="/b"))
    assert find_route([a, b], "/b", {}, {}).name == "b"


def test_find_route_none():
    a = _route(name="a", match=Match(path="/a"))
    assert find_route([a], "/z", {}, {}) is None
