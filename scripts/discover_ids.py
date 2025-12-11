#!/usr/bin/env python3
"""CLI script to discover preregistration IDs from OSF API"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.osf.id_scraper import OSFIDScraper


def main():
    parser = argparse.ArgumentParser(
        description="Discover preregistration IDs from OSF registrations endpoint (Phase 0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover all preregistration IDs
  python scripts/discover_ids.py
  
  # Limit to first 100 IDs
  python scripts/discover_ids.py --max-results 100
  
  # Save to custom file
  python scripts/discover_ids.py --output data/osf_ids.txt
  
  # Get all registrations (not just preregistrations)
  python scripts/discover_ids.py --no-filter
  
  # Start from a specific page (e.g., resume from page 187)
  python scripts/discover_ids.py --start-page 187
  
  # Use API token for authenticated requests
  python scripts/discover_ids.py --token YOUR_TOKEN
  # Or set OSF_API_TOKEN environment variable
        """
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/osf_ids.txt"),
        help="Output file for OSF IDs (default: data/osf_ids.txt)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Maximum number of IDs to discover (default: all)"
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Don't filter for preregistrations (get all registrations)"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="OSF API token (optional, can also use OSF_API_TOKEN env var)"
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=0,
        help="Page number to start collecting IDs from (default: 0). Pages before this will be skipped."
    )
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = OSFIDScraper(api_token=args.token)
    
    print("="*60)
    print("OSF Preregistration ID Discovery (Phase 0)")
    print("="*60)
    print(f"Filter for preregistrations: {not args.no_filter}")
    if args.max_results:
        print(f"Maximum results: {args.max_results}")
    if args.start_page > 0:
        print(f"Starting from page: {args.start_page}")
    print()
    
    # Discover IDs
    ids = scraper.discover_preregistration_ids(
        max_results=args.max_results,
        filter_category=not args.no_filter,
        start_page=args.start_page
    )
    
    # Save IDs
    scraper.save_ids(ids, args.output)
    
    print(f"\n{'='*60}")
    print(f"Discovery complete!")
    print(f"Total IDs found: {len(ids)}")
    print(f"Output file: {args.output}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

