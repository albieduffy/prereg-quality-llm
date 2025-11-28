"""Prompt builder for LLM scoring"""

import json
from pathlib import Path
from typing import Dict

from ..utils.io import load_json


def load_rubric(rubric_path: Path) -> Dict:
    """
    Load rubric from JSON file.
    
    Args:
        rubric_path: Path to rubric.json file.
    
    Returns:
        Dictionary containing rubric content.
    """
    return load_json(rubric_path)


def format_rubric_text(rubric: Dict) -> str:
    """
    Format rubric dictionary into readable text for prompt.
    
    Args:
        rubric: Rubric dictionary.
    
    Returns:
        Formatted rubric text.
    """
    lines = ["# Preregistration Quality Rubric\n"]
    
    for criterion, scores in rubric.items():
        # Convert snake_case to title case
        criterion_name = criterion.replace("_", " ").title()
        lines.append(f"## {criterion_name}\n")
        
        for score, description in scores.items():
            lines.append(f"  Score {score}: {description}")
        
        lines.append("")  # Empty line between criteria
    
    return "\n".join(lines)


def build_system_prompt(rubric_path: Path) -> str:
    """
    Build system prompt for LLM scoring.
    
    Args:
        rubric_path: Path to rubric.json file.
    
    Returns:
        System prompt string.
    """
    rubric = load_rubric(rubric_path)
    rubric_text = format_rubric_text(rubric)
    
    prompt = f"""You are an expert evaluator of research preregistrations. Your task is to score preregistration documents according to the following rubric.

{rubric_text}

## Instructions:
1. Read the preregistration document carefully.
2. For each criterion, assign a score based on the rubric.
3. Provide a brief justification (1-2 sentences) for each score.
4. Return your evaluation as a JSON object matching the required schema.

Be thorough, objective, and consistent in your evaluations."""
    
    return prompt


def build_user_prompt(prereg_text: str) -> str:
    """
    Build user prompt with preregistration text.
    
    Args:
        prereg_text: Full text of the preregistration document.
    
    Returns:
        User prompt string.
    """
    return f"""Please evaluate the following preregistration document according to the rubric:

{prereg_text}

Provide your evaluation as a JSON object with the following structure:
- hypothesis_clarity_score (integer, 1-5)
- hypothesis_clarity_justification (string)
- method_specificity_score (integer, 1-5)
- method_specificity_justification (string)
- analysis_detail_score (integer, 1-5)
- analysis_detail_justification (string)
- power_analysis_score (integer, 0-1)
- power_analysis_justification (string)
- completeness_score (integer, 1-5)
- completeness_justification (string)"""

