from hookrelay.template import get_path, render


def test_simple_key():
    assert render("hi {{ name }}", {"name": "sam"}) == "hi sam"


def test_nested_dotted():
    payload = {"repository": {"full_name": "u/hookrelay"}}
    assert render("{{ repository.full_name }}", payload) == "u/hookrelay"


def test_missing_key_default_empty():
    assert render("x{{ nope }}y", {}) == "xy"


def test_missing_key_custom_default():
    assert render("{{ nope }}", {}, default="-") == "-"


def test_builtins():
    out = render("{{ _route }}: {{ _body }}", {}, builtins={"_route": "r", "_body": "b"})
    assert out == "r: b"


def test_builtin_missing_uses_default():
    assert render("{{ _route }}", {}, default="?") == "?"


def test_list_index():
    payload = {"commits": [{"id": "abc"}, {"id": "def"}]}
    assert render("{{ commits.1.id }}", payload) == "def"


def test_negative_list_index():
    payload = {"items": [1, 2, 3]}
    assert render("{{ items.-1 }}", payload) == "3"


def test_stringify_number_and_bool():
    assert render("{{ n }} {{ b }}", {"n": 5, "b": True}) == "5 true"


def test_stringify_nested_object():
    assert render("{{ obj }}", {"obj": {"a": 1}}) == '{"a":1}'


def test_none_renders_empty():
    assert render("[{{ v }}]", {"v": None}) == "[]"


def test_whitespace_in_placeholder():
    assert render("{{   name   }}", {"name": "ok"}) == "ok"


def test_get_path_missing_returns_default():
    assert get_path({"a": 1}, "a.b.c", default="X") == "X"


def test_get_path_bad_list_index():
    assert get_path({"a": [1]}, "a.five", default="X") == "X"
