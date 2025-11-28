"""Statistical analysis models for preregistration quality research"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
from pathlib import Path

import statsmodels.api as sm
from statsmodels.discrete.discrete_model import Logit
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import NegativeBinomial
from lifelines import CoxPHFitter

from ..utils.logging import setup_logging

logger = setup_logging()


def logistic_publication_model(
    df: pd.DataFrame,
    outcome_col: str = "published",
    predictor_cols: Optional[list] = None,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Fit logistic regression model for publication outcome.
    
    Args:
        df: DataFrame with outcome and predictors.
        outcome_col: Name of binary outcome column (0/1).
        predictor_cols: List of predictor column names. If None, uses all score columns.
        output_path: Optional path to save model summary.
    
    Returns:
        Dictionary containing model results and summary.
    """
    if predictor_cols is None:
        # Auto-detect score columns
        predictor_cols = [col for col in df.columns if col.endswith("_score")]
    
    # Prepare data (ensure rows are complete for both predictors and outcome)
    model_data = df[[outcome_col] + predictor_cols].dropna()
    y = model_data[outcome_col]
    X = model_data[predictor_cols]
    
    # Add intercept
    X = sm.add_constant(X)
    
    # Fit model
    model = Logit(y, X)
    result = model.fit()
    
    logger.info("Logistic regression model fitted")
    logger.info(f"AIC: {result.aic:.2f}")
    
    # Save summary if requested
    if output_path:
        with open(output_path, 'w') as f:
            f.write(result.summary().as_text())
        logger.info(f"Model summary saved to {output_path}")
    
    return {
        "model": result,
        "summary": result.summary(),
        "aic": result.aic,
        "predictors": predictor_cols
    }


def cox_survival_model(
    df: pd.DataFrame,
    duration_col: str = "time_to_publication",
    event_col: str = "published",
    predictor_cols: Optional[list] = None,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Fit Cox proportional hazards model for time-to-publication.
    
    Args:
        df: DataFrame with duration, event, and predictors.
        duration_col: Name of duration/time column.
        event_col: Name of event indicator column (0/1).
        predictor_cols: List of predictor column names. If None, uses all score columns.
        output_path: Optional path to save model summary.
    
    Returns:
        Dictionary containing model results and summary.
    """
    if predictor_cols is None:
        predictor_cols = [col for col in df.columns if col.endswith("_score")]
    
    # Prepare data
    model_data = df[[duration_col, event_col] + predictor_cols].dropna()
    
    # Fit Cox model
    cph = CoxPHFitter()
    cph.fit(model_data, duration_col=duration_col, event_col=event_col)
    
    logger.info("Cox survival model fitted")
    
    # Save summary if requested
    if output_path:
        cph.summary.to_csv(output_path)
        logger.info(f"Model summary saved to {output_path}")
    
    return {
        "model": cph,
        "summary": cph.summary,
        "predictors": predictor_cols
    }


def negative_binomial_citations_model(
    df: pd.DataFrame,
    outcome_col: str = "citations",
    predictor_cols: Optional[list] = None,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Fit negative binomial regression model for citation count.
    
    Args:
        df: DataFrame with outcome and predictors.
        outcome_col: Name of count outcome column.
        predictor_cols: List of predictor column names. If None, uses all score columns.
        output_path: Optional path to save model summary.
    
    Returns:
        Dictionary containing model results and summary.
    """
    if predictor_cols is None:
        predictor_cols = [col for col in df.columns if col.endswith("_score")]
    
    # Prepare data (ensure rows are complete for both predictors and outcome)
    model_data = df[[outcome_col] + predictor_cols].dropna()
    y = model_data[outcome_col]
    X = model_data[predictor_cols]
    
    # Add intercept
    X = sm.add_constant(X)
    
    # Fit negative binomial model
    model = GLM(y, X, family=NegativeBinomial())
    result = model.fit()
    
    logger.info("Negative binomial model fitted")
    logger.info(f"AIC: {result.aic:.2f}")
    
    # Save summary if requested
    if output_path:
        with open(output_path, 'w') as f:
            f.write(result.summary().as_text())
        logger.info(f"Model summary saved to {output_path}")
    
    return {
        "model": result,
        "summary": result.summary(),
        "aic": result.aic,
        "predictors": predictor_cols
    }


def run_all_analyses(
    df: pd.DataFrame,
    output_dir: Path,
    has_publication: bool = True,
    has_time_to_pub: bool = False,
    has_citations: bool = False
) -> Dict:
    """
    Run all available analyses based on data availability.
    
    Args:
        df: Merged analysis dataset.
        output_dir: Directory to save model outputs.
        has_publication: Whether publication outcome is available.
        has_time_to_pub: Whether time-to-publication data is available.
        has_citations: Whether citation data is available.
    
    Returns:
        Dictionary containing all model results.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    if has_publication and "published" in df.columns:
        logger.info("Running logistic regression for publication...")
        results["publication"] = logistic_publication_model(
            df,
            output_path=output_dir / "logistic_publication_summary.txt"
        )
    
    if has_time_to_pub and "time_to_publication" in df.columns:
        logger.info("Running Cox survival model for time-to-publication...")
        results["time_to_publication"] = cox_survival_model(
            df,
            output_path=output_dir / "cox_survival_summary.csv"
        )
    
    if has_citations and "citations" in df.columns:
        logger.info("Running negative binomial model for citations...")
        results["citations"] = negative_binomial_citations_model(
            df,
            output_path=output_dir / "negative_binomial_citations_summary.txt"
        )
    
    logger.info(f"Completed {len(results)} analyses")
    
    return results

