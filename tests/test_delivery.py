from hookrelay.delivery import deliver
from hookrelay.sinks import OutboundRequest

REQ = OutboundRequest("POST", "http://x", {}, b"body")


def test_success_first_try():
    calls = []
    result = deliver(REQ, sender=lambda r: 200, sleeper=lambda s: calls.append(s))
    assert result.ok
    assert result.attempts == 1
    assert result.status == 200
    assert calls == []  # no sleep on immediate success


def test_retry_then_success():
    attempts = {"n": 0}
    slept = []

    def sender(req):
        attempts["n"] += 1
        return 500 if attempts["n"] < 2 else 204

    result = deliver(REQ, sender=sender, retries=3, backoff=0.5, sleeper=slept.append)
    assert result.ok
    assert result.attempts == 2
    assert slept == [0.5]


def test_all_fail():
    slept = []
    result = deliver(REQ, sender=lambda r: 503, retries=3, backoff=1.0, sleeper=slept.append)
    assert not result.ok
    assert result.attempts == 3
    assert "503" in result.error
    # sleeps between attempts only, not after the last one
    assert slept == [1.0, 2.0]


def test_exception_is_caught():
    def boom(req):
        raise ConnectionError("refused")

    result = deliver(REQ, sender=boom, retries=2, sleeper=lambda s: None)
    assert not result.ok
    assert "refused" in result.error


def test_backoff_is_exponential():
    slept = []
    deliver(REQ, sender=lambda r: 500, retries=4, backoff=0.25, sleeper=slept.append)
    assert slept == [0.25, 0.5, 1.0]


def test_no_retry_when_retries_one():
    slept = []
    result = deliver(REQ, sender=lambda r: 500, retries=1, sleeper=slept.append)
    assert result.attempts == 1
    assert slept == []
