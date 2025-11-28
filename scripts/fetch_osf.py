#!/usr/bin/env python3
"""Script to fetch preregistrations from OSF API"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.osf.fetch_osf import OSFFetcher, fetch_from_file
from src.utils.logging import setup_logging

logger = setup_logging()


def main():
    parser = argparse.ArgumentParser(
        description="Fetch preregistrations from OSF API"
    )
    parser.add_argument(
        "--ids",
        nargs="+",
        help="OSF IDs to fetch (space-separated)"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="File containing OSF IDs (one per line)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw"),
        help="Output directory for raw JSON files (default: data/raw)"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="OSF API token (optional, can also use OSF_API_TOKEN env var)"
    )
    
    args = parser.parse_args()
    
    if not args.ids and not args.file:
        parser.error("Must provide either --ids or --file")
    
    # Get API token from args or environment
    import os
    api_token = args.token or os.getenv("OSF_API_TOKEN")
    
    fetcher = OSFFetcher(api_token=api_token)
    
    if args.file:
        logger.info(f"Fetching from file: {args.file}")
        fetch_from_file(args.file, args.output, api_token=api_token)
    else:
        logger.info(f"Fetching {len(args.ids)} preregistrations")
        successful = fetcher.fetch_multiple(args.ids, args.output)
        logger.info(f"Successfully fetched {len(successful)}/{len(args.ids)} preregistrations")


if __name__ == "__main__":
    main()

