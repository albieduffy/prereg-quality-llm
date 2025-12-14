#!/usr/bin/env python3
"""CLI script to scrape preregistrations from OSF API"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.osf import OSFScraper


def main():
    parser = argparse.ArgumentParser(
        description="Scrape preregistrations from OSF API (Phase 1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch specific OSF IDs
  python scripts/scrape_osf.py --ids abc12 def34 ghi56
  
  # Fetch from a file (one OSF ID per line)
  python scripts/scrape_osf.py --file osf_ids.txt
  
  # Specify output directory
  python scripts/scrape_osf.py --ids abc12 --output data/preregistrations
  
  # Use API token for authenticated requests
  python scripts/scrape_osf.py --ids abc12 --token YOUR_TOKEN
  # Or set OSF_API_TOKEN environment variable
        """,
    )
    parser.add_argument("--ids", nargs="+", help="OSF IDs to fetch (space-separated)")
    parser.add_argument(
        "--file", type=Path, help="File containing OSF IDs (one per line)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw"),
        help="Output directory for raw JSON files (default: data/raw)",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="OSF API token (optional, can also use OSF_API_TOKEN env var)",
    )

    args = parser.parse_args()

    if not args.ids and not args.file:
        parser.error("Must provide either --ids or --file")

    # Get OSF IDs
    if args.file:
        if not args.file.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        with open(args.file, "r") as f:
            osf_ids = [line.strip() for line in f if line.strip()]
        print(f"Reading {len(osf_ids)} OSF IDs from {args.file}")
    else:
        osf_ids = args.ids

    # Initialize scraper and fetch
    scraper = OSFScraper(api_token=args.token)
    print(f"\nFetching {len(osf_ids)} preregistration(s)...\n")

    successful = scraper.fetch_multiple(osf_ids, args.output)

    print(f"\n{'=' * 50}")
    print(f"Successfully fetched: {len(successful)}/{len(osf_ids)}")
    print(f"Output directory: {args.output}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
