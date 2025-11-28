#!/usr/bin/env python3
"""Script to clean preregistration text files"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cleaning.clean_text import clean_all_osf_files
from src.utils.logging import setup_logging

logger = setup_logging()


def main():
    parser = argparse.ArgumentParser(
        description="Clean preregistration text from raw OSF JSON files"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw"),
        help="Input directory with raw OSF JSON files (default: data/raw)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed"),
        help="Output directory for cleaned text files (default: data/processed)"
    )
    parser.add_argument(
        "--text-key",
        type=str,
        default="full_text",
        help="Key in JSON containing text to clean (default: full_text)"
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input directory does not exist: {args.input}")
        sys.exit(1)
    
    # Clean all files
    clean_all_osf_files(
        input_dir=args.input,
        output_dir=args.output,
        text_key=args.text_key
    )
    
    logger.info("Text cleaning complete")


if __name__ == "__main__":
    main()

