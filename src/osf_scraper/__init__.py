"""osf-scraper — A Python package for scraping the Open Science Framework (OSF)."""

__version__ = "0.1.0"

from .discovery import OSFIDScraper
from .processing import analyse_registrations, process_registrations
from .scraper import (
    ScraperConfig,
    ScraperState,
    TokenBucket,
    fetch_with_retry,
    process_batch,
    process_ids_in_batches,
)
from .utils import compute_remaining_ids

__all__ = [
    "OSFIDScraper",
    "ScraperConfig",
    "ScraperState",
    "TokenBucket",
    "fetch_with_retry",
    "process_batch",
    "process_ids_in_batches",
    "process_registrations",
    "analyse_registrations",
    "compute_remaining_ids",
]
