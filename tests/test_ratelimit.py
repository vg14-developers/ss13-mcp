import time

from vgstation13_mcp.ratelimit import TokenBucket


def test_token_bucket_blocks_after_capacity():
    bucket = TokenBucket(capacity=3, refill_per_second=0)
    assert bucket.take("user1")
    assert bucket.take("user1")
    assert bucket.take("user1")
    assert not bucket.take("user1")


def test_token_bucket_refills():
    bucket = TokenBucket(capacity=2, refill_per_second=10)
    assert bucket.take("user1")
    assert bucket.take("user1")
    assert not bucket.take("user1")
    time.sleep(0.15)
    assert bucket.take("user1")


def test_token_bucket_per_user_isolation():
    bucket = TokenBucket(capacity=1, refill_per_second=0)
    assert bucket.take("alice")
    assert not bucket.take("alice")
    assert bucket.take("bob")
