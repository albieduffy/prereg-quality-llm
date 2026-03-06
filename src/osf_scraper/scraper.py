"""Async OSF scraper for fetching registration data in batches."""

import asyncio
import json
import logging
import os
import random
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import aiofiles
import aiohttp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class ScraperConfig:
    """Configuration for the async OSF scraper.

    All fields have sensible defaults and can be overridden via the CLI or
    when calling library functions directly.
    """

    base_url: str = "https://api.osf.io/v2/"
    endpoint_template: str = "registrations/{}/"
    initial_max_concurrent: int = 5
    min_concurrent: int = 1
    max_retries: int = 5
    initial_retry_delay: float = 2.0
    request_delay: float = 0.2
    batch_size: int = 100
    timeout_seconds: int = 30
    rate_limit_window: int = 100
    rate_limit_threshold: float = 0.3
    global_rate_limit: float = 5.0


# ---------------------------------------------------------------------------
# Token-bucket rate limiter
# ---------------------------------------------------------------------------
class TokenBucket:
    """Global rate limiter using a token-bucket algorithm."""

    def __init__(self, rate: float, capacity: float):
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._last_refill = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = asyncio.get_running_loop().time()
            if self._last_refill == 0.0:
                self._last_refill = now
            elapsed = now - self._last_refill
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last_refill = now
            if self._tokens < 1:
                wait_time = (1 - self._tokens) / self.rate
                await asyncio.sleep(wait_time)
                self._tokens = 0.0
            else:
                self._tokens -= 1


# ---------------------------------------------------------------------------
# Mutable scraper state
# ---------------------------------------------------------------------------
@dataclass
class ScraperState:
    """Mutable state tracked across batches during a scrape run."""

    max_concurrent: int = 5
    rate_limit_tracker: deque = field(
        default_factory=lambda: deque(maxlen=100)
    )
    token_bucket: TokenBucket | None = None

    @classmethod
    def from_config(cls, config: ScraperConfig) -> "ScraperState":
        """Create a new state initialised from *config*."""
        return cls(
            max_concurrent=config.initial_max_concurrent,
            rate_limit_tracker=deque(maxlen=config.rate_limit_window),
            token_bucket=TokenBucket(
                rate=config.global_rate_limit,
                capacity=config.global_rate_limit,
            ),
        )

    @property
    def recent_rate_limit_rate(self) -> float:
        """Fraction of recent requests that were rate-limited."""
        if len(self.rate_limit_tracker) >= 50:
            return sum(self.rate_limit_tracker) / len(self.rate_limit_tracker)
        return 0.0


# ---------------------------------------------------------------------------
# Core async helpers
# ---------------------------------------------------------------------------
async def fetch_with_retry(
    session: aiohttp.ClientSession,
    osf_id: str,
    semaphore: asyncio.Semaphore,
    state: ScraperState,
    config: ScraperConfig | None = None,
) -> tuple[str, dict | None, bool]:
    """Fetch a single OSF registration with retry logic.

    Returns:
        ``(osf_id, response_data, was_rate_limited)``
    """
    config = config or ScraperConfig()
    url = config.base_url + config.endpoint_template.format(osf_id)
    was_rate_limited = False

    async with semaphore:
        dynamic_delay = config.request_delay * (
            1 + state.recent_rate_limit_rate * 5
        )
        if state.token_bucket is not None:
            await state.token_bucket.acquire()
        await asyncio.sleep(dynamic_delay)

        for attempt in range(config.max_retries + 1):
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=config.timeout_seconds),
                ) as response:
                    status_code = response.status

                    if status_code == 200:
                        data = await response.json()
                        return (osf_id, data.get("data"), was_rate_limited)

                    if status_code == 429:
                        was_rate_limited = True
                        retry_after_str = response.headers.get("Retry-After", "")
                        if retry_after_str:
                            try:
                                retry_after = float(retry_after_str)
                            except ValueError:
                                retry_after = config.initial_retry_delay * (
                                    2**attempt
                                )
                        else:
                            retry_after = config.initial_retry_delay * (
                                2**attempt
                            )

                        base_delay = max(
                            retry_after,
                            config.initial_retry_delay * (2**attempt),
                        )
                        jitter = random.uniform(0, base_delay * 0.5)
                        delay = base_delay + jitter

                        if attempt < config.max_retries:
                            await asyncio.sleep(delay)
                            continue
                        return (osf_id, None, was_rate_limited)

                    # Other error status codes
                    if attempt < config.max_retries:
                        await asyncio.sleep(
                            config.initial_retry_delay * (2**attempt)
                        )
                        continue
                    return (osf_id, None, was_rate_limited)

            except (asyncio.TimeoutError, aiohttp.ClientError):
                if attempt < config.max_retries:
                    await asyncio.sleep(
                        config.initial_retry_delay * (2**attempt)
                    )
                    continue
                return (osf_id, None, was_rate_limited)
            except Exception as exc:
                logger.warning(
                    "Unexpected error fetching %s: %s: %s",
                    osf_id,
                    type(exc).__name__,
                    exc,
                )
                return (osf_id, None, was_rate_limited)

    return (osf_id, None, was_rate_limited)


async def process_batch(
    session: aiohttp.ClientSession,
    batch_ids: list[str],
    batch_num: int,
    output_file: Path,
    successful_ids_file: Path,
    state: ScraperState,
    config: ScraperConfig | None = None,
) -> dict:
    """Process a batch of IDs and return batch statistics."""
    config = config or ScraperConfig()
    semaphore = asyncio.Semaphore(state.max_concurrent)
    write_lock = asyncio.Lock()
    tracker_lock = asyncio.Lock()
    batch_results: dict = {
        "batch_num": batch_num,
        "total": len(batch_ids),
        "successful": 0,
        "failed": 0,
        "successful_ids": [],
    }

    async def _process_id(osf_id: str) -> None:
        osf_id = osf_id.strip()
        if not osf_id:
            return

        _, response_data, was_rate_limited = await fetch_with_retry(
            session, osf_id, semaphore, state, config,
        )

        async with tracker_lock:
            state.rate_limit_tracker.append(was_rate_limited)

        if response_data is not None:
            async with write_lock:
                async with aiofiles.open(output_file, "a", encoding="utf-8") as f:
                    await f.write(
                        json.dumps(response_data, ensure_ascii=False) + "\n"
                    )
                    await f.flush()

            batch_results["successful"] += 1
            batch_results["successful_ids"].append(osf_id)
        else:
            batch_results["failed"] += 1

    tasks = [_process_id(osf_id) for osf_id in batch_ids]
    await asyncio.gather(*tasks, return_exceptions=True)

    if batch_results["successful_ids"]:
        async with aiofiles.open(
            successful_ids_file, "a", encoding="utf-8"
        ) as f:
            for osf_id in batch_results["successful_ids"]:
                await f.write(f"{osf_id}\n")
            await f.flush()

    return batch_results


async def process_ids_in_batches(
    ids_file: Path,
    output_file: Path,
    successful_ids_file: Path,
    resume: bool,
    config: ScraperConfig | None = None,
) -> None:
    """Process IDs in batches with adaptive concurrency control."""
    config = config or ScraperConfig()
    state = ScraperState.from_config(config)
    batch_stats: list = []

    output_file.parent.mkdir(parents=True, exist_ok=True)
    successful_ids_file.parent.mkdir(parents=True, exist_ok=True)

    if not resume:
        if output_file.exists():
            output_file.unlink()
        if successful_ids_file.exists():
            successful_ids_file.unlink()
    else:
        logger.info("Resume mode: appending to existing output files")

    connector = aiohttp.TCPConnector(limit=config.initial_max_concurrent * 2)
    timeout = aiohttp.ClientTimeout(total=config.timeout_seconds)

    api_token = os.getenv("OSF_API_TOKEN")
    headers: dict = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
        logger.info("Using OSF API token for authenticated requests")
    else:
        logger.warning(
            "No OSF_API_TOKEN found. "
            "Using unauthenticated requests (lower rate limits)."
        )

    with open(ids_file, "r", encoding="utf-8") as f:
        all_ids = [line.strip() for line in f if line.strip()]

    total_batches = (len(all_ids) + config.batch_size - 1) // config.batch_size
    logger.info("Total IDs: %d", len(all_ids))
    logger.info(
        "Processing in %d batches of %d", total_batches, config.batch_size
    )

    async with aiohttp.ClientSession(
        connector=connector, timeout=timeout, headers=headers
    ) as session:
        for batch_num in range(total_batches):
            start_idx = batch_num * config.batch_size
            end_idx = min(start_idx + config.batch_size, len(all_ids))
            batch_ids = all_ids[start_idx:end_idx]

            logger.info(
                "Processing batch %d/%d (%d IDs)…",
                batch_num + 1,
                total_batches,
                len(batch_ids),
            )
            batch_start_time = time.time()

            # Adaptive concurrency
            if len(state.rate_limit_tracker) >= 50:
                if (
                    state.recent_rate_limit_rate > config.rate_limit_threshold
                    and state.max_concurrent > config.min_concurrent
                ):
                    state.max_concurrent = max(
                        config.min_concurrent,
                        int(state.max_concurrent * 0.7),
                    )
                    logger.info(
                        "  Reducing concurrency to %d "
                        "(rate limit rate: %.2f%%)",
                        state.max_concurrent,
                        state.recent_rate_limit_rate * 100,
                    )
                elif (
                    state.recent_rate_limit_rate
                    < config.rate_limit_threshold * 0.5
                    and state.max_concurrent < config.initial_max_concurrent
                ):
                    state.max_concurrent = min(
                        config.initial_max_concurrent,
                        int(state.max_concurrent * 1.2),
                    )
                    logger.info(
                        "  Increasing concurrency to %d "
                        "(rate limit rate: %.2f%%)",
                        state.max_concurrent,
                        state.recent_rate_limit_rate * 100,
                    )

            batch_results = await process_batch(
                session,
                batch_ids,
                batch_num + 1,
                output_file,
                successful_ids_file,
                state,
                config,
            )

            batch_elapsed = time.time() - batch_start_time
            batch_success_rate = (
                (batch_results["successful"] / batch_results["total"]) * 100
                if batch_results["total"] > 0
                else 0
            )

            batch_stats.append(
                {
                    "batch": batch_num + 1,
                    "success_rate": batch_success_rate,
                    "successful": batch_results["successful"],
                    "failed": batch_results["failed"],
                    "time": batch_elapsed,
                }
            )

            logger.info(
                "  Batch %d complete: %d/%d successful "
                "(%.1f%%) in %.1fs",
                batch_num + 1,
                batch_results["successful"],
                batch_results["total"],
                batch_success_rate,
                batch_elapsed,
            )

            failure_rate = (
                batch_results["failed"] / batch_results["total"]
                if batch_results["total"] > 0
                else 0
            )
            if failure_rate > 0.2 and batch_num < total_batches - 1:
                cooldown = 10.0 * (1 + failure_rate)
                logger.info(
                    "  High failure rate (%.1f%%), "
                    "cooling down for %.1fs…",
                    failure_rate * 100,
                    cooldown,
                )
                await asyncio.sleep(cooldown)

    # Summary
    total_successful = sum(s["successful"] for s in batch_stats)
    total_failed = sum(s["failed"] for s in batch_stats)
    total_time = sum(s["time"] for s in batch_stats)
    overall_success_rate = (
        (total_successful / (total_successful + total_failed)) * 100
        if (total_successful + total_failed) > 0
        else 0
    )

    logger.info("=" * 60)
    logger.info("BATCH SUMMARY")
    logger.info("=" * 60)
    logger.info("Total batches: %d", total_batches)
    logger.info("Total successful: %d", total_successful)
    logger.info("Total failed: %d", total_failed)
    logger.info("Overall success rate: %.1f%%", overall_success_rate)
    logger.info(
        "Total time: %.1fs (%.1f minutes)", total_time, total_time / 60
    )
    logger.info("Batch-by-batch breakdown:")
    for stat in batch_stats:
        logger.info(
            "  Batch %d: %d/%d (%.1f%%) – %.1fs",
            stat["batch"],
            stat["successful"],
            stat["successful"] + stat["failed"],
            stat["success_rate"],
            stat["time"],
        )
    logger.info("=" * 60)
