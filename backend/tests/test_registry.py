"""Per-key isolation is the registry's reason to exist, so that is what is pinned."""

import pytest

from ratekit import bucket as bucket_mod
from ratekit import registry as registry_mod
from ratekit.registry import LimiterRegistry


@pytest.fixture
def clock(monkeypatch):
    state = {"t": 500.0}
    monkeypatch.setattr(bucket_mod.time, "monotonic", lambda: state["t"])
    monkeypatch.setattr(registry_mod.time, "monotonic", lambda: state["t"])
    return state


def test_keys_do_not_share_a_budget(clock):
    r = LimiterRegistry(capacity=2, rate=1.0)
    assert r.take("alice") is True
    assert r.take("alice") is True
    assert r.take("alice") is False
    # bob must be untouched by alice exhausting hers
    assert r.take("bob") is True
    assert len(r) == 2


def test_bucket_is_created_once_per_key(clock):
    r = LimiterRegistry(capacity=5, rate=1.0)
    first = r.bucket("alice")
    assert r.bucket("alice") is first
    assert len(r) == 1


def test_sweep_drops_only_idle_keys(clock):
    r = LimiterRegistry(capacity=5, rate=1.0, idle_ttl=100.0)
    r.take("old")
    clock["t"] += 200.0
    r.take("new")
    assert r.sweep() == 1
    assert len(r) == 1
    assert r.bucket("new") is not None
