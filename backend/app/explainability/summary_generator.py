import numpy as np
from typing import Any
from .types import ExplainabilitySummary

def generate_summary(
    shap_values: Any,
    feature_names: list[str],
    model_family: str
) -> ExplainabilitySummary:
    """Generate lightweight metadata from raw SHAP values."""
    # Handle single output vs multi-output models
    if len(shap_values.values.shape) == 3:
        # (samples, features, classes) -> take class 1 for binary classification
        vals = shap_values.values[:, :, 1]
    else:
        vals = shap_values.values

    # Mean absolute SHAP values across all samples
    mean_abs_shap = np.abs(vals).mean(axis=0)
    
    # Pair with feature names and sort
    importance = sorted(zip(feature_names, mean_abs_shap), key=lambda x: x[1], reverse=True)
    top_features = [f[0] for f in importance[:10]]
    mean_abs_dict = {f: float(v) for f, v in importance}
    
    # Positive vs negative contributors
    data = shap_values.data
    positive_contributors = []
    negative_contributors = []
    
    for i, feature in enumerate(feature_names):
        feat_vals = data[:, i]
        if hasattr(feat_vals, "toarray"):
            feat_vals = feat_vals.toarray().flatten()
        else:
            feat_vals = np.array(feat_vals).flatten()
            
        # Cast to float to avoid numpy object dtype errors
        try:
            feat_vals = feat_vals.astype(float)
        except ValueError:
            # If feature is categorical and can't be cast to float, skip correlation
            continue
            
        s_vals = np.array(vals[:, i], dtype=float).flatten()
        
        # Calculate Pearson correlation
        if np.std(feat_vals) > 0 and np.std(s_vals) > 0:
            corr = np.corrcoef(feat_vals, s_vals)[0, 1]
            if corr > 0.1:
                positive_contributors.append(feature)
            elif corr < -0.1:
                negative_contributors.append(feature)
                
    # Sort them by overall importance
    pos_sorted = [f for f in top_features if f in positive_contributors]
    neg_sorted = [f for f in top_features if f in negative_contributors]

    return {
        "feature_count": len(feature_names),
        "sample_size": vals.shape[0],
        "top_features": top_features,
        "mean_absolute_shap": mean_abs_dict,
        "positive_contributors": pos_sorted,
        "negative_contributors": neg_sorted,
        "model_family": model_family
    }
