"""LLM scoring module for preregistration quality evaluation"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

import yaml
from openai import OpenAI

from ..utils.io import load_json, save_json, read_text
from ..utils.logging import setup_logging
from .build_prompt import build_system_prompt, build_user_prompt
from ..validation.validate_json import validate_score_json

logger = setup_logging()


class LLMScorer:
    """Scorer using OpenAI API to evaluate preregistration quality."""
    
    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0,
        max_tokens: int = 600,
        schema_path: Optional[Path] = None,
        rubric_path: Optional[Path] = None
    ):
        """
        Initialize LLM scorer.
        
        Args:
            model: OpenAI model name (default: gpt-4o, fallback if gpt-4.1 not available).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            schema_path: Path to JSON schema file.
            rubric_path: Path to rubric JSON file.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Load schema and rubric
        if schema_path:
            self.schema = load_json(schema_path)
        else:
            self.schema = None
        
        if rubric_path:
            self.rubric_path = Path(rubric_path)
            self.system_prompt = build_system_prompt(self.rubric_path)
        else:
            self.rubric_path = None
            self.system_prompt = None
    
    def score_preregistration(
        self,
        prereg_text: str,
        osf_id: Optional[str] = None,
        validate: bool = True
    ) -> Dict:
        """
        Score a single preregistration document.
        
        Args:
            prereg_text: Full text of the preregistration.
            osf_id: Optional OSF ID for logging.
            validate: Whether to validate response against schema.
        
        Returns:
            Dictionary containing scores and justifications.
        """
        if not self.system_prompt:
            raise ValueError("System prompt not initialized. Provide rubric_path.")
        
        user_prompt = build_user_prompt(prereg_text)
        
        # Prepare function calling parameters if schema is available
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info(f"Scoring preregistration {osf_id or 'unknown'}")
        
        try:
            # Use structured outputs if schema is available (OpenAI API v1.0+)
            if self.schema:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                scores = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                # Use balanced brace matching to handle curly braces in justification text
                import re
                # First, try to find code block boundaries
                code_block_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
                if code_block_match:
                    code_content = code_block_match.group(1).strip()
                    # Try parsing the code block content directly
                    try:
                        scores = json.loads(code_content)
                    except json.JSONDecodeError:
                        # If that fails, find JSON object by matching balanced braces
                        # Find the first { and then match balanced braces
                        brace_start = code_content.find('{')
                        if brace_start != -1:
                            brace_count = 0
                            brace_end = -1
                            for i in range(brace_start, len(code_content)):
                                if code_content[i] == '{':
                                    brace_count += 1
                                elif code_content[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        brace_end = i + 1
                                        break
                            if brace_end > brace_start:
                                json_str = code_content[brace_start:brace_end]
                                scores = json.loads(json_str)
                            else:
                                raise ValueError(f"Unbalanced braces in JSON: {content[:200]}")
                        else:
                            raise ValueError(f"No JSON object found in code block: {content[:200]}")
                else:
                    raise ValueError(f"Could not parse JSON from response: {content[:200]}")
            
            # Validate against schema if requested
            if validate and self.schema:
                validate_score_json(scores, self.schema)
            
            # Add metadata
            scores["_metadata"] = {
                "model": self.model,
                "osf_id": osf_id,
                "timestamp": response.created
            }
            
            return scores
            
        except Exception as e:
            logger.error(f"Error scoring preregistration {osf_id or 'unknown'}: {e}")
            raise
    
    def score_file(
        self,
        input_path: Path,
        output_path: Path,
        osf_id: Optional[str] = None
    ) -> None:
        """
        Score a preregistration from a text file.
        
        Args:
            input_path: Path to cleaned text file.
            output_path: Path to save scores JSON.
            osf_id: Optional OSF ID (inferred from filename if not provided).
        """
        if osf_id is None:
            osf_id = input_path.stem
        
        prereg_text = read_text(input_path)
        scores = self.score_preregistration(prereg_text, osf_id=osf_id)
        
        save_json(scores, output_path)
        logger.info(f"Saved scores to {output_path}")
    
    def score_all(
        self,
        input_dir: Path,
        output_dir: Path
    ) -> None:
        """
        Score all preregistration text files in a directory.
        
        Args:
            input_dir: Directory containing cleaned text files.
            output_dir: Directory to save score JSON files.
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        text_files = list(input_dir.glob("*.txt"))
        
        if not text_files:
            logger.warning(f"No text files found in {input_dir}")
            return
        
        logger.info(f"Scoring {len(text_files)} preregistrations")
        
        for text_file in text_files:
            output_file = output_dir / f"{text_file.stem}.json"
            try:
                self.score_file(text_file, output_file)
            except Exception as e:
                logger.error(f"Failed to score {text_file}: {e}")


def load_config(config_path: Path) -> Dict:
    """
    Load model configuration from YAML file.
    
    Args:
        config_path: Path to model_config.yaml.
    
    Returns:
        Dictionary containing configuration.
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def create_scorer_from_config(config_path: Path, project_root: Optional[Path] = None) -> LLMScorer:
    """
    Create LLMScorer instance from configuration file.
    
    Args:
        config_path: Path to model_config.yaml.
        project_root: Optional project root directory for resolving relative paths.
    
    Returns:
        Configured LLMScorer instance.
    """
    config = load_config(config_path)
    
    if project_root is None:
        project_root = Path(config_path).parent.parent
    
    schema_path = project_root / config.get("schema_path", "config/schema.json")
    rubric_path = project_root / config.get("rubric_path", "config/rubric.json")
    
    # Handle model name (gpt-4.1 may not exist, use gpt-4o as fallback)
    model = config.get("model", "gpt-4o")
    if model == "gpt-4.1":
        model = "gpt-4o"  # Fallback to available model
        logger.warning("gpt-4.1 not available, using gpt-4o instead")
    
    return LLMScorer(
        model=model,
        temperature=config.get("temperature", 0),
        max_tokens=config.get("max_tokens", 600),
        schema_path=schema_path if schema_path.exists() else None,
        rubric_path=rubric_path if rubric_path.exists() else None
    )

