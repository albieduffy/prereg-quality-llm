"""I/O utilities for JSON, text, and table files"""

import json
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load JSON file.
    
    Args:
        file_path: Path to JSON file.
    
    Returns:
        Dictionary containing JSON data.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Save dictionary to JSON file.
    
    Args:
        data: Dictionary to save.
        file_path: Output file path.
        indent: JSON indentation level.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def read_text(file_path: Union[str, Path]) -> str:
    """
    Read text file.
    
    Args:
        file_path: Path to text file.
    
    Returns:
        File contents as string.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_text(text: str, file_path: Union[str, Path]) -> None:
    """
    Write text to file.
    
    Args:
        text: Text content to write.
        file_path: Output file path.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)


def load_table(
    file_path: Union[str, Path],
    file_type: Optional[str] = None
) -> pd.DataFrame:
    """
    Load table file (CSV or Parquet).
    
    Args:
        file_path: Path to table file.
        file_type: File type ('csv' or 'parquet'). If None, inferred from extension.
    
    Returns:
        DataFrame containing table data.
    """
    file_path = Path(file_path)
    
    if file_type is None:
        file_type = file_path.suffix.lower().lstrip('.')
    
    if file_type == 'csv':
        return pd.read_csv(file_path)
    elif file_type == 'parquet':
        return pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def save_table(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    file_type: Optional[str] = None,
    **kwargs
) -> None:
    """
    Save DataFrame to table file (CSV or Parquet).
    
    Args:
        df: DataFrame to save.
        file_path: Output file path.
        file_type: File type ('csv' or 'parquet'). If None, inferred from extension.
        **kwargs: Additional arguments passed to pandas save functions.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if file_type is None:
        file_type = file_path.suffix.lower().lstrip('.')
    
    if file_type == 'csv':
        df.to_csv(file_path, index=False, **kwargs)
    elif file_type == 'parquet':
        df.to_parquet(file_path, index=False, **kwargs)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

