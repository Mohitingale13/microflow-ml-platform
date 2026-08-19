import logging
import shap  # type: ignore
import numpy as np
from typing import Any
from .explainer_factory import get_explainer
from .summary_generator import generate_summary
from .plot_generator import generate_plots
from .types import ExplainabilitySummary

logger = logging.getLogger(__name__)

def run_explainability(
    estimator: Any,
    X_test: Any,
    feature_names: list[str],
    random_state: int = 42
) -> tuple[ExplainabilitySummary, Any, Any, Any, Any]:
    """
    Run SHAP explainability on a trained estimator.
    Returns: (summary, shap_values, fig_summary, fig_bar, fig_dependence)
    """
    # Deterministic sampling for large datasets to maintain performance
    MAX_SAMPLES = 500
    if len(X_test) > MAX_SAMPLES:
        logger.info(f"Sampling {MAX_SAMPLES} from {len(X_test)} samples for SHAP background (random_state={random_state}).")
        if hasattr(X_test, "sample"):
            X_bg = X_test.sample(n=MAX_SAMPLES, random_state=random_state)
        else:
            np.random.seed(random_state)
            indices = np.random.choice(len(X_test), MAX_SAMPLES, replace=False)
            X_bg = X_test[indices]
    else:
        X_bg = X_test

    logger.info("Initializing SHAP Explainer...")
    explainer = get_explainer(estimator, X_bg)
    
    logger.info("Calculating SHAP values...")
    shap_values = explainer(X_bg)

    # FIX: For binary classification models (like Random Forest) that output 3D SHAP values [samples, features, classes],
    # slice the Explanation object to only use the positive class (class 1) for plotting and summary.
    if len(shap_values.shape) == 3 and shap_values.shape[-1] == 2:
        logger.info("Binary classification detected in SHAP values. Selecting positive class for explainability.")
        shap_values = shap_values[..., 1]

    model_family = type(estimator).__name__
    
    logger.info("Generating Explainability Summary...")
    summary = generate_summary(shap_values, feature_names, model_family)
    
    top_feature = summary["top_features"][0] if summary["top_features"] else feature_names[0]
    
    logger.info(f"Generating SHAP Plots (Dependence plot for top feature: {top_feature})...")
    fig_summary, fig_bar, fig_dependence = generate_plots(shap_values, top_feature)
    
    return summary, shap_values, fig_summary, fig_bar, fig_dependence
