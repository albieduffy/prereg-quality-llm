#!/usr/bin/env python3
"""Script to run statistical analyses on merged dataset"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.models import run_all_analyses
from src.utils.io import load_table
from src.utils.logging import setup_logging

logger = setup_logging()


def main():
    parser = argparse.ArgumentParser(
        description="Run statistical analyses on merged dataset"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/merged/analysis_dataset.csv"),
        help="Path to merged dataset CSV (default: data/merged/analysis_dataset.csv)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/merged/analysis_results"),
        help="Output directory for analysis results (default: data/merged/analysis_results)"
    )
    parser.add_argument(
        "--publication",
        action="store_true",
        help="Run logistic regression for publication outcome"
    )
    parser.add_argument(
        "--time-to-pub",
        action="store_true",
        help="Run Cox survival model for time-to-publication"
    )
    parser.add_argument(
        "--citations",
        action="store_true",
        help="Run negative binomial model for citations"
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input file does not exist: {args.input}")
        sys.exit(1)
    
    # Load dataset
    logger.info(f"Loading dataset from {args.input}")
    df = load_table(args.input)
    
    # Determine which analyses to run
    has_publication = args.publication or "published" in df.columns
    has_time_to_pub = args.time_to_pub or "time_to_publication" in df.columns
    has_citations = args.citations or "citations" in df.columns
    
    # Run analyses
    results = run_all_analyses(
        df=df,
        output_dir=args.output,
        has_publication=has_publication,
        has_time_to_pub=has_time_to_pub,
        has_citations=has_citations
    )
    
    logger.info(f"Analysis complete. Results saved to {args.output}")


if __name__ == "__main__":
    main()

