"""Text cleaning utilities for preregistration documents"""

import re
import unicodedata
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from ..utils.io import read_text, write_text, load_json
from ..utils.logging import setup_logging

logger = setup_logging()


def clean_text(
    text: str,
    strip_html: bool = True,
    normalize_unicode: bool = True,
    collapse_whitespace: bool = True
) -> str:
    """
    Clean text from preregistration documents.
    
    Args:
        text: Raw text to clean.
        strip_html: Whether to remove HTML tags.
        normalize_unicode: Whether to normalize Unicode characters.
        collapse_whitespace: Whether to collapse multiple whitespace into single spaces.
    
    Returns:
        Cleaned text.
    """
    cleaned = text
    
    # Strip HTML if present
    if strip_html:
        soup = BeautifulSoup(cleaned, 'html.parser')
        cleaned = soup.get_text(separator=' ')
    
    # Normalize Unicode (e.g., convert smart quotes to regular quotes)
    if normalize_unicode:
        cleaned = unicodedata.normalize('NFKD', cleaned)
    
    # Collapse whitespace
    if collapse_whitespace:
        # Replace multiple spaces, tabs, newlines with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
    
    return cleaned


def clean_osf_file(
    input_path: Path,
    output_path: Path,
    text_key: str = "full_text"
) -> None:
    """
    Clean text from a single OSF JSON file.
    
    Args:
        input_path: Path to raw OSF JSON file.
        output_path: Path to save cleaned text file.
        text_key: Key in JSON containing the text to clean.
    """
    data = load_json(input_path)
    raw_text = data.get(text_key, "")
    
    if not raw_text:
        logger.warning(f"No text found in {input_path} under key '{text_key}'")
        return
    
    cleaned = clean_text(raw_text)
    write_text(cleaned, output_path)
    logger.info(f"Cleaned text saved to {output_path}")


def clean_all_osf_files(
    input_dir: Path,
    output_dir: Path,
    text_key: str = "full_text"
) -> None:
    """
    Clean all OSF JSON files in a directory.
    
    Args:
        input_dir: Directory containing raw OSF JSON files.
        output_dir: Directory to save cleaned text files.
        text_key: Key in JSON containing the text to clean.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_files = list(input_dir.glob("*.json"))
    
    if not json_files:
        logger.warning(f"No JSON files found in {input_dir}")
        return
    
    for json_file in json_files:
        output_file = output_dir / f"{json_file.stem}.txt"
        try:
            clean_osf_file(json_file, output_file, text_key)
        except Exception as e:
            logger.error(f"Failed to clean {json_file}: {e}")
    
    logger.info(f"Cleaned {len(json_files)} files")

