"""Tests for TokenBucket rate limiter."""

import asyncio
import time

import pytest
from osf_scraper.scraper import TokenBucket


def test_token_bucket_allows_burst():
    """Bucket with capacity=5 should allow 5 immediate acquisitions."""

    async def run():
        bucket = TokenBucket(rate=5.0, capacity=5.0)
        start = time.monotonic()
        for _ in range(5):
            await bucket.acquire()
        return time.monotonic() - start

    elapsed = asyncio.run(run())
    assert elapsed < 1.0, f"Burst of 5 took too long: {elapsed:.2f}s"


def test_token_bucket_rate_limits():
    """Acquiring more than capacity should introduce a delay."""

    async def run():
        bucket = TokenBucket(rate=10.0, capacity=1.0)
        await bucket.acquire()  # consume the single token
        start = time.monotonic()
        await bucket.acquire()  # must wait ~0.1s for next token
        return time.monotonic() - start

    elapsed = asyncio.run(run())
    assert elapsed >= 0.05, f"Expected rate limiting delay, got {elapsed:.3f}s"
