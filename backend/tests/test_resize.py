from ratekit.bucket import TokenBucket


def test_resize_grows_capacity():
    b = TokenBucket(capacity=2, rate=1.0)
    b.resize(5)
    assert b.capacity == 5


def test_resize_keeps_earned_tokens():
    b = TokenBucket(capacity=4, rate=1.0)
    b.resize(8)
    assert b.available() >= 4
