# pyrefly: ignore [missing-import]
import shap
from typing import Any

def get_explainer(estimator: Any, X_background: Any) -> Any:
    """
    Returns the most appropriate SHAP explainer for the estimator.
    """
    model_type = type(estimator).__name__
    
    if "LogisticRegression" in model_type:
        return shap.LinearExplainer(estimator, X_background)
    elif "RandomForest" in model_type or "XGB" in model_type:
        return shap.TreeExplainer(estimator)
    else:
        # Fallback for unexpected models
        return shap.Explainer(estimator, X_background)
