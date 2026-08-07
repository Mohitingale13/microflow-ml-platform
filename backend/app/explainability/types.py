from typing import TypedDict

class ExplainabilitySummary(TypedDict):
    feature_count: int
    sample_size: int
    top_features: list[str]
    mean_absolute_shap: dict[str, float]
    positive_contributors: list[str]
    negative_contributors: list[str]
    model_family: str
