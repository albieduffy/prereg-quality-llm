#!/usr/bin/env python3
"""Script to validate LLM score JSON files against schema"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.validate_json import validate_directory
from src.utils.logging import setup_logging

logger = setup_logging()


def main():
    parser = argparse.ArgumentParser(
        description="Validate LLM score JSON files against schema"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/scores_llm"),
        help="Input directory with score JSON files (default: data/scores_llm)"
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("config/schema.json"),
        help="Path to JSON schema file (default: config/schema.json)"
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input directory does not exist: {args.input}")
        sys.exit(1)
    
    if not args.schema.exists():
        logger.error(f"Schema file does not exist: {args.schema}")
        sys.exit(1)
    
    # Validate all files
    results = validate_directory(args.input, args.schema)
    
    # Exit with error code if any files are invalid
    invalid_count = sum(1 for v in results.values() if not v)
    if invalid_count > 0:
        logger.error(f"{invalid_count} files failed validation")
        sys.exit(1)
    else:
        logger.info("All files passed validation")


if __name__ == "__main__":
    main()

