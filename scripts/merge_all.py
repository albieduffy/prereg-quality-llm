#!/usr/bin/env python3
"""Script to merge all datasets into final analysis dataset"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.merge.merge_datasets import merge_all_datasets
from src.utils.logging import setup_logging

logger = setup_logging()


def main():
    parser = argparse.ArgumentParser(
        description="Merge prereg metadata, LLM scores, and human scores"
    )
    parser.add_argument(
        "--raw",
        type=Path,
        default=Path("data/raw"),
        help="Directory with raw OSF JSON files (default: data/raw)"
    )
    parser.add_argument(
        "--llm-scores",
        type=Path,
        default=Path("data/scores_llm"),
        help="Directory with LLM score JSON files (default: data/scores_llm)"
    )
    parser.add_argument(
        "--human-scores",
        type=Path,
        default=Path("data/scores_human"),
        help="Directory with human score files (default: data/scores_human)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/merged/analysis_dataset.csv"),
        help="Output path for merged dataset (default: data/merged/analysis_dataset.csv)"
    )
    
    args = parser.parse_args()
    
    # Merge datasets
    merged_df = merge_all_datasets(
        raw_dir=args.raw,
        llm_scores_dir=args.llm_scores,
        human_scores_dir=args.human_scores if args.human_scores.exists() else None,
        output_path=args.output
    )
    
    logger.info(f"Merged dataset saved to {args.output}")
    logger.info(f"Dataset shape: {merged_df.shape}")


if __name__ == "__main__":
    main()

