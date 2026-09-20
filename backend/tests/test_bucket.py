"""The clamp is the structure's only real invariant, so it gets the most tests.

Time is monkeypatched rather than slept: a sleeping test is slow and, on a
loaded CI runner, not actually deterministic.
"""

import pytest

from ratekit import bucket as bucket_mod
from ratekit.bucket import TokenBucket


@pytest.fixture
def clock(monkeypatch):
    """A monotonic clock the test advances explicitly."""
    state = {"t": 1000.0}
    monkeypatch.setattr(bucket_mod.time, "monotonic", lambda: state["t"])
    return state


def test_starts_full(clock):
    b = TokenBucket(capacity=5, rate=1.0)
    assert b.available() == 5


def test_take_spends_and_refuses_when_short(clock):
    b = TokenBucket(capacity=2, rate=1.0)
    assert b.take() is True
    assert b.take() is True
    assert b.take() is False
    assert b.available() == 0


def test_a_refused_take_spends_nothing(clock):
    b = TokenBucket(capacity=3, rate=1.0)
    assert b.take(3) is True
    assert b.take(2) is False
    clock["t"] += 1.0
    # One second at rate 1.0 buys exactly one token, and the refused take must
    # not have consumed part of the balance on its way to returning False.
    assert b.available() == pytest.approx(1.0)


def test_refill_is_clamped_to_capacity(clock):
    b = TokenBucket(capacity=4, rate=2.0)
    assert b.take(4) is True
    clock["t"] += 3600.0            # an hour idle at 2/s is 7200 tokens earned
    assert b.available() == 4, "an idle bucket must not bank tokens past capacity"


def test_idle_client_cannot_burst_past_capacity(clock):
    b = TokenBucket(capacity=10, rate=5.0)
    clock["t"] += 86_400.0          # a day of silence
    spent = sum(1 for _ in range(100) if b.take())
    assert spent == 10, "a long-idle client must still be held to one bucket"


def test_rejects_nonsense_construction(clock):
    with pytest.raises(ValueError):
        TokenBucket(capacity=0, rate=1.0)
    with pytest.raises(ValueError):
        TokenBucket(capacity=1, rate=0)


def test_retry_after_is_zero_when_tokens_are_available():
    b = TokenBucket(capacity=5, rate=1.0)
    assert b.retry_after() == 0.0


def test_retry_after_reports_the_shortfall():
    b = TokenBucket(capacity=5, rate=2.0)
    for _ in range(5):
        assert b.take()
    # Empty bucket, refilling at 2/s, so one token is half a second away.
    assert 0.4 < b.retry_after() < 0.6

