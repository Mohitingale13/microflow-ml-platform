import matplotlib
matplotlib.use('Agg') # Ensure non-interactive backend
import matplotlib.pyplot as plt
import shap  # type: ignore
from typing import Any

def generate_plots(shap_values: Any, top_feature: str) -> tuple[Any, Any, Any]:
    """
    Generate Matplotlib figures for SHAP.
    Returns (summary_fig, bar_fig, dependence_fig)
    """
    # Create Summary Plot (Beeswarm)
    fig_summary = plt.figure(figsize=(10, 6))
    shap.plots.beeswarm(shap_values, show=False)
    plt.tight_layout()
    plt.close(fig_summary) # Close to prevent memory leaks

    # Create Bar Plot
    fig_bar = plt.figure(figsize=(10, 6))
    shap.plots.bar(shap_values, show=False)
    plt.tight_layout()
    plt.close(fig_bar)

    # Create Dependence Plot for the top feature
    fig_dependence = plt.figure(figsize=(10, 6))
    ax = fig_dependence.add_subplot(111)
    shap.plots.scatter(shap_values[:, top_feature], color=shap_values, show=False, ax=ax)
    plt.tight_layout()
    plt.close(fig_dependence)

    return fig_summary, fig_bar, fig_dependence
