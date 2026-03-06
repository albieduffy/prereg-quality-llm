"""Utility helpers for the OSF scraper package."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def compute_remaining_ids(
    all_ids_file: Path,
    successful_ids_file: Path,
    output_file: Path,
) -> set[str]:
    """
    Compute the set of IDs that have not yet been successfully scraped.

    The result is written to *output_file* (one ID per line) and also returned
    as a set.

    Args:
        all_ids_file: Path to the file containing all known OSF IDs.
        successful_ids_file: Path to the file containing already-processed IDs.
        output_file: Path to write the remaining (unprocessed) IDs.

    Returns:
        The set of remaining IDs.

    Raises:
        FileNotFoundError: If either input file does not exist.
    """
    with open(all_ids_file, "r", encoding="utf-8") as f:
        all_ids = {line.strip() for line in f if line.strip()}

    with open(successful_ids_file, "r", encoding="utf-8") as f:
        successful_ids = {line.strip() for line in f if line.strip()}

    remaining_ids = all_ids - successful_ids

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for osf_id in remaining_ids:
            f.write(osf_id + "\n")

    logger.info("Remaining IDs: %d", len(remaining_ids))
    return remaining_ids
