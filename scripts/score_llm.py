#!/usr/bin/env python3
"""Script to score preregistrations using LLM"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scoring.llm_scorer import LLMScorer, create_scorer_from_config
from src.utils.logging import setup_logging

logger = setup_logging()


def main():
    parser = argparse.ArgumentParser(
        description="Score preregistrations using LLM"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed"),
        help="Input directory with cleaned text files (default: data/processed)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/scores_llm"),
        help="Output directory for LLM scores (default: data/scores_llm)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/model_config.yaml"),
        help="Path to model config YAML (default: config/model_config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Create scorer from config
    project_root = Path(__file__).parent.parent
    scorer = create_scorer_from_config(args.config, project_root=project_root)
    
    # Score all files
    scorer.score_all(args.input, args.output)
    
    logger.info("LLM scoring complete")


if __name__ == "__main__":
    main()

