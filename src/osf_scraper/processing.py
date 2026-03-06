"""Post-processing utilities for scraped OSF registration data."""

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def process_registrations(input_file: Path, output_file: Path) -> None:
    """
    Flatten raw JSONL registrations into a normalised JSONL file.

    Each nested JSON object is flattened using ``pd.json_normalize`` so that
    nested keys become dot-separated column names.

    Args:
        input_file: Path to the raw JSONL input (one JSON object per line).
        output_file: Path to write the flattened JSONL output.
    """
    with open(input_file, "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f if line.strip()]

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df = pd.json_normalize(data)
    df.to_json(output_file, orient="records", lines=True)
    logger.info("Processed %d registrations → %s", len(data), output_file)


def analyse_registrations(input_file: Path, output_file: Path) -> None:
    """
    Extract column names from a processed JSONL file and save them as JSON.

    Streams through the file line-by-line so that only column names (not the
    full dataset) are held in memory.

    Args:
        input_file: Path to the processed JSONL file.
        output_file: Path to write the JSON list of column names.
    """
    columns: list[str] = []
    seen: set[str] = set()
    count = 0

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            for key in record:
                if key not in seen:
                    seen.add(key)
                    columns.append(key)
            count += 1

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(columns, f, indent=4)

    logger.info("Analysed %d registrations", count)
    logger.info("Columns: %d", len(columns))
    logger.info("Saved column names to %s", output_file)
