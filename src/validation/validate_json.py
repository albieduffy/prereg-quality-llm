"""JSON schema validation utilities"""

import json
from pathlib import Path
from typing import Dict

import jsonschema
from jsonschema import validate, ValidationError

from ..utils.io import load_json
from ..utils.logging import setup_logging

logger = setup_logging()


def validate_score_json(data: Dict, schema: Dict) -> bool:
    """
    Validate a score JSON against a schema.
    
    Args:
        data: Dictionary containing scores to validate.
        schema: JSON schema dictionary.
    
    Returns:
        True if valid, raises ValidationError if invalid.
    
    Raises:
        ValidationError: If data does not match schema.
    """
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        logger.error(f"Failed path: {'.'.join(str(p) for p in e.absolute_path)}")
        raise


def validate_file(file_path: Path, schema_path: Path) -> bool:
    """
    Validate a JSON file against a schema file.
    
    Args:
        file_path: Path to JSON file to validate.
        schema_path: Path to JSON schema file.
    
    Returns:
        True if valid, raises ValidationError if invalid.
    """
    data = load_json(file_path)
    schema = load_json(schema_path)
    
    return validate_score_json(data, schema)


def validate_directory(
    input_dir: Path,
    schema_path: Path,
    pattern: str = "*.json"
) -> Dict[str, bool]:
    """
    Validate all JSON files in a directory.
    
    Args:
        input_dir: Directory containing JSON files.
        schema_path: Path to JSON schema file.
        pattern: Glob pattern for files to validate.
    
    Returns:
        Dictionary mapping file paths to validation status (True/False).
    """
    input_dir = Path(input_dir)
    schema = load_json(schema_path)
    
    json_files = list(input_dir.glob(pattern))
    results = {}
    
    for json_file in json_files:
        try:
            data = load_json(json_file)
            validate_score_json(data, schema)
            results[str(json_file)] = True
            logger.info(f"✓ {json_file.name} is valid")
        except ValidationError as e:
            results[str(json_file)] = False
            logger.error(f"✗ {json_file.name} is invalid: {e.message}")
        except Exception as e:
            results[str(json_file)] = False
            logger.error(f"✗ {json_file.name} error: {e}")
    
    valid_count = sum(1 for v in results.values() if v)
    logger.info(f"Validation complete: {valid_count}/{len(results)} files valid")
    
    return results

