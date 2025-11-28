"""Dataset merging utilities"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from ..utils.io import load_json, save_table, read_text
from ..utils.logging import setup_logging

logger = setup_logging()


def load_prereg_metadata(raw_dir: Path) -> pd.DataFrame:
    """
    Load preregistration metadata from raw OSF JSON files.
    
    Args:
        raw_dir: Directory containing raw OSF JSON files.
    
    Returns:
        DataFrame with metadata columns.
    """
    raw_dir = Path(raw_dir)
    json_files = list(raw_dir.glob("*.json"))
    
    records = []
    
    for json_file in json_files:
        try:
            data = load_json(json_file)
            osf_id = data.get("osf_id", json_file.stem)
            metadata = data.get("metadata", {})
            attrs = metadata.get("attributes", {})
            
            record = {
                "osf_id": osf_id,
                "title": attrs.get("title", ""),
                "date_created": attrs.get("date_created", ""),
                "date_registered": attrs.get("date_registered", ""),
                "category": attrs.get("category", ""),
                "description": attrs.get("description", ""),
            }
            records.append(record)
        except Exception as e:
            logger.warning(f"Failed to load metadata from {json_file}: {e}")
    
    return pd.DataFrame(records)


def load_llm_scores(scores_dir: Path) -> pd.DataFrame:
    """
    Load LLM scores from JSON files.
    
    Args:
        scores_dir: Directory containing LLM score JSON files.
    
    Returns:
        DataFrame with score columns.
    """
    scores_dir = Path(scores_dir)
    json_files = list(scores_dir.glob("*.json"))
    
    records = []
    
    for json_file in json_files:
        try:
            data = load_json(json_file)
            osf_id = data.get("_metadata", {}).get("osf_id", json_file.stem)
            
            # Extract scores (excluding metadata)
            record = {"osf_id": osf_id}
            for key, value in data.items():
                if key != "_metadata":
                    record[key] = value
            
            records.append(record)
        except Exception as e:
            logger.warning(f"Failed to load scores from {json_file}: {e}")
    
    return pd.DataFrame(records)


def load_human_scores(scores_dir: Path, file_format: str = "csv") -> pd.DataFrame:
    """
    Load human scores from files.
    
    Args:
        scores_dir: Directory containing human score files.
        file_format: File format ('csv' or 'json').
    
    Returns:
        DataFrame with human score columns.
    """
    scores_dir = Path(scores_dir)
    
    if file_format == "csv":
        # Look for a single CSV file or multiple CSVs
        csv_files = list(scores_dir.glob("*.csv"))
        if len(csv_files) == 1:
            df = pd.read_csv(csv_files[0])
        elif len(csv_files) > 1:
            # Concatenate multiple CSVs
            dfs = [pd.read_csv(f) for f in csv_files]
            df = pd.concat(dfs, ignore_index=True)
        else:
            logger.warning(f"No CSV files found in {scores_dir}")
            return pd.DataFrame()
        
        # Ensure osf_id column exists
        if "osf_id" not in df.columns:
            logger.warning("Human scores CSV missing 'osf_id' column")
        
        return df
    
    elif file_format == "json":
        json_files = list(scores_dir.glob("*.json"))
        records = []
        
        for json_file in json_files:
            try:
                data = load_json(json_file)
                records.append(data)
            except Exception as e:
                logger.warning(f"Failed to load {json_file}: {e}")
        
        return pd.DataFrame(records)
    
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


def merge_all_datasets(
    raw_dir: Path,
    llm_scores_dir: Path,
    human_scores_dir: Optional[Path] = None,
    output_path: Path = None
) -> pd.DataFrame:
    """
    Merge prereg metadata, LLM scores, and human scores into final dataset.
    
    Args:
        raw_dir: Directory containing raw OSF JSON files.
        llm_scores_dir: Directory containing LLM score JSON files.
        human_scores_dir: Optional directory containing human score files.
        output_path: Optional path to save merged dataset.
    
    Returns:
        Merged DataFrame.
    """
    logger.info("Loading metadata...")
    metadata_df = load_prereg_metadata(raw_dir)
    
    logger.info("Loading LLM scores...")
    llm_df = load_llm_scores(llm_scores_dir)
    
    # Merge metadata and LLM scores
    merged = metadata_df.merge(
        llm_df,
        on="osf_id",
        how="outer",
        suffixes=("", "_llm")
    )
    
    # Add human scores if available
    if human_scores_dir and Path(human_scores_dir).exists():
        logger.info("Loading human scores...")
        human_df = load_human_scores(human_scores_dir)
        
        if not human_df.empty and "osf_id" in human_df.columns:
            merged = merged.merge(
                human_df,
                on="osf_id",
                how="left",
                suffixes=("", "_human")
            )
        else:
            logger.warning("Human scores not available or missing osf_id column")
    
    # Save if output path provided
    if output_path:
        save_table(merged, output_path)
        logger.info(f"Merged dataset saved to {output_path}")
    
    logger.info(f"Merged dataset contains {len(merged)} records")
    
    return merged

