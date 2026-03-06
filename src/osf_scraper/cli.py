"""Command-line interface entry points for osf-scraper."""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def _setup_logging(verbose: bool = False) -> None:
    """Configure root logging for CLI usage."""
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(levelname)s %(name)s: %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
        )


def discover() -> None:
    """Discover preregistration IDs from the OSF registrations endpoint."""
    from .discovery import OSFIDScraper

    parser = argparse.ArgumentParser(
        description="Discover preregistration IDs from the OSF registrations endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  osf-discover
  osf-discover --output data/osf_ids.txt
  osf-discover --max-results 1000
  osf-discover --no-filter
  osf-discover --token YOUR_TOKEN
""",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/osf_ids.txt"),
        help="Output file for OSF IDs (default: data/osf_ids.txt)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Maximum number of IDs to discover (default: all)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        default=False,
        help="Include all registrations, not just preregistrations",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="OSF API token (overrides OSF_API_TOKEN env var)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )

    args = parser.parse_args()
    _setup_logging(args.verbose)

    scraper = OSFIDScraper(api_token=args.token)

    logger.info("=" * 60)
    logger.info("OSF Preregistration ID Discovery")
    logger.info("=" * 60)

    ids = scraper.discover_preregistration_ids(
        max_results=args.max_results,
        filter_category=not args.no_filter,
    )

    scraper.save_ids(ids, args.output)

    logger.info("=" * 60)
    logger.info("Discovery complete!")
    logger.info("Total IDs found: %d", len(ids))
    logger.info("Output file: %s", args.output)
    logger.info("=" * 60)


def scrape() -> None:
    """Scrape OSF registrations from a list of IDs in batches."""
    from dotenv import load_dotenv

    from .scraper import ScraperConfig, process_ids_in_batches

    parser = argparse.ArgumentParser(
        description="Scrape OSF registrations from a list of IDs in batches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  osf-scrape --file data/osf_ids.txt
  osf-scrape --file data/osf_ids.txt --output data/raw/preregistrations.jsonl
  osf-scrape --file data/osf_ids.txt --resume
""",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("data/osf_ids_remaining.txt"),
        help="Input file with OSF IDs (one per line)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/preregistrations.jsonl"),
        help="Output JSONL file (default: data/raw/preregistrations.jsonl)",
    )
    parser.add_argument(
        "--successful-ids",
        type=Path,
        default=Path("data/raw/successful_ids.txt"),
        help="Output file for successfully processed IDs",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Resume a previous run (append instead of overwrite)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of IDs per batch (default: 100)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=None,
        help="Maximum concurrent requests (default: 5)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help="Maximum retry attempts per request (default: 5)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=None,
        help="Maximum requests per second (default: 5.0)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )

    args = parser.parse_args()
    _setup_logging(args.verbose)

    load_dotenv()

    if not args.file.exists():
        logger.error("File not found: %s", args.file)
        sys.exit(1)

    # Build config, overriding defaults with any CLI arguments
    config_overrides: dict = {}
    if args.batch_size is not None:
        config_overrides["batch_size"] = args.batch_size
    if args.max_concurrent is not None:
        config_overrides["initial_max_concurrent"] = args.max_concurrent
    if args.max_retries is not None:
        config_overrides["max_retries"] = args.max_retries
    if args.rate_limit is not None:
        config_overrides["global_rate_limit"] = args.rate_limit
    config = ScraperConfig(**config_overrides)

    logger.info("Starting scraper…")
    logger.info("IDs file: %s", args.file)
    logger.info("Output file: %s", args.output)
    logger.info("Successful IDs file: %s", args.successful_ids)
    logger.info("Batch size: %d", config.batch_size)
    logger.info(
        "Initial max concurrent requests: %d", config.initial_max_concurrent
    )
    logger.info("Min concurrent requests: %d", config.min_concurrent)
    logger.info("Max retries: %d", config.max_retries)
    logger.info("Global rate limit: %.1f req/s", config.global_rate_limit)
    logger.info("Adaptive rate limiting: enabled")
    logger.info("Resume mode: %s", args.resume)

    start_time = time.time()
    asyncio.run(
        process_ids_in_batches(
            args.file,
            args.output,
            args.successful_ids,
            args.resume,
            config,
        )
    )
    elapsed = time.time() - start_time

    logger.info(
        "Total elapsed time: %.1fs (%.1f minutes)", elapsed, elapsed / 60
    )


def process() -> None:
    """Flatten raw JSONL registrations into a normalised DataFrame."""
    from .processing import process_registrations

    parser = argparse.ArgumentParser(
        description="Flatten JSONL registrations into a normalised DataFrame"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/preregistrations.jsonl"),
        help="Input JSONL file (default: data/raw/preregistrations.jsonl)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/preregistrations.jsonl"),
        help="Output JSONL file (default: data/processed/preregistrations.jsonl)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )

    args = parser.parse_args()
    _setup_logging(args.verbose)
    process_registrations(args.input, args.output)


def analyse() -> None:
    """Extract column names from processed registration data."""
    from .processing import analyse_registrations

    parser = argparse.ArgumentParser(
        description="Extract column names from processed registrations"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/preregistrations.jsonl"),
        help="Input JSONL file (default: data/processed/preregistrations.jsonl)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/analysed/columns.json"),
        help="Output JSON file (default: data/analysed/columns.json)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )

    args = parser.parse_args()
    _setup_logging(args.verbose)
    analyse_registrations(args.input, args.output)


def remaining() -> None:
    """Compute remaining unprocessed OSF IDs."""
    from .utils import compute_remaining_ids

    parser = argparse.ArgumentParser(
        description="Compute remaining unprocessed OSF IDs"
    )
    parser.add_argument(
        "--all-ids",
        type=Path,
        default=Path("data/osf_ids.txt"),
        help="File with all OSF IDs",
    )
    parser.add_argument(
        "--successful-ids",
        type=Path,
        default=Path("data/raw/successful_ids-total.txt"),
        help="File with successfully processed IDs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/osf_ids_remaining.txt"),
        help="Output file for remaining IDs",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )

    args = parser.parse_args()
    _setup_logging(args.verbose)

    try:
        compute_remaining_ids(args.all_ids, args.successful_ids, args.output)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        sys.exit(1)
