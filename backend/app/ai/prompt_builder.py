"""
ai/prompt_builder.py — Constructs the structured Gemini prompt.

This module is pure Python. It does not call Gemini or touch the database.
It accepts already-fetched domain objects and returns a ready-to-send
prompt string.

Engineering style:
  - No markdown in prompt
  - No bullet spam instructions
  - JSON response format enforced via explicit field contract
  - Explicit instruction to state "unavailable" rather than hallucinate
"""

from __future__ import annotations
from typing import Any


def _fmt_metric(value: float | None, decimals: int = 4) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _fmt_config(config: dict[str, Any] | None) -> str:
    if not config:
        return "default configuration"
    parts = [f"{k}={v}" for k, v in config.items()]
    return ", ".join(parts) if parts else "default configuration"


def _format_explainability_summary(summary: dict[str, Any] | None) -> str:
    """Format the SHAP explainability summary into a readable block."""
    if not summary:
        return ""
    top_features = ", ".join(summary.get("top_features", [])[:5])
    return (
        f"SHAP EXPLAINABILITY SUMMARY:\n"
        f"- Top Predictive Features: {top_features}\n"
        f"- Positive Drivers Count: {len(summary.get('positive_contributors', []))}\n"
        f"- Negative Drivers Count: {len(summary.get('negative_contributors', []))}\n\n"
    )


def build_review_prompt(
    *,
    run: Any,
    experiment: Any,
    dataset: Any,
    run_result: Any,
    best_run: Any | None,
    best_result: Any | None,
) -> str:
    """
    Construct a fully structured prompt for Gemini 2.5 Flash.

    Parameters
    ----------
    run         : Run ORM object for the run being reviewed.
    experiment  : Experiment ORM object.
    dataset     : Dataset ORM object.
    run_result  : RunResult ORM object (evaluation metrics).
    best_run    : Run ORM object for the current best run in the experiment
                  (may be the same as run, or None if only one run exists).
    best_result : RunResult ORM object for best_run (may be None).

    Returns
    -------
    str
        A complete prompt string ready for the Gemini API.
    """

    # ── Current run metrics ───────────────────────────────────────────────────
    acc     = _fmt_metric(run_result.accuracy if run_result else None)
    prec    = _fmt_metric(run_result.precision if run_result else None)
    rec     = _fmt_metric(run_result.recall if run_result else None)
    f1      = _fmt_metric(run_result.f1_score if run_result else None)
    roc     = _fmt_metric(run_result.roc_auc if run_result else None)
    exec_t  = (
        f"{run_result.execution_time_seconds:.2f}s"
        if run_result and run_result.execution_time_seconds
        else "N/A"
    )

    # ── Best run metrics & deltas ─────────────────────────────────────────────
    is_best = best_run is None or (best_run and best_run.id == run.id)

    if best_result and best_run is not None and not is_best:
        b_acc   = _fmt_metric(best_result.accuracy)
        b_prec  = _fmt_metric(best_result.precision)
        b_f1    = _fmt_metric(best_result.f1_score)
        d_acc   = run_result.accuracy - best_result.accuracy if run_result else None
        delta   = (
            f"{d_acc:+.4f}" if d_acc is not None else "N/A"
        )
        best_section = (
            f"Best run in this experiment: Run #{best_run.run_number} "
            f"({best_result.model_type or 'unknown model'}) — "
            f"accuracy={b_acc}, precision={b_prec}, f1={b_f1}. "
            f"Accuracy delta for this run vs best: {delta}."
        )
    elif is_best:
        best_section = (
            "This run is currently the best-performing run in the experiment."
        )
    else:
        best_section = "No completed comparison run is available yet."

    # ── Dataset info ──────────────────────────────────────────────────────────
    dataset_info = "N/A"
    if dataset:
        dataset_info = (
            f"Name: {dataset.name}, "
            f"Rows: {dataset.row_count}, "
            f"Columns: {dataset.column_count}"
        )

    # ── Training config ───────────────────────────────────────────────────────
    config_str = _fmt_config(run.training_configuration)

    # ── Explainability info ───────────────────────────────────────────────────
    explainability_section = ""
    if run_result and getattr(run_result, "explainability_status", None) == "completed" and getattr(run_result, "explainability_summary", None):
        explainability_section = _format_explainability_summary(getattr(run_result, "explainability_summary", None))

    # ── Prompt ────────────────────────────────────────────────────────────────
    prompt = f"""You are a senior ML engineer conducting a written peer review of a training run.

Your review must be professional, precise, and written in clear engineering language.
Do not use markdown, bullet points, or code blocks. Write in full sentences and paragraphs only.
If any information is unavailable, state that explicitly. Never hallucinate or invent metrics.

CONTEXT
Experiment: {experiment.name}
Objective: {experiment.objective or "Not specified"}
Dataset: {dataset_info}

RUN UNDER REVIEW
Experiment: {experiment.name} — Run #{run.run_number}
Model: {run.model_type}
Configuration: {config_str}
Execution time: {exec_t}

METRICS FOR THIS RUN
Accuracy: {acc}
Precision: {prec}
Recall: {rec}
F1 Score: {f1}
ROC AUC: {roc}
{explainability_section}
EXPERIMENT CONTEXT
{best_section}

INSTRUCTIONS
Respond with a single JSON object. No preamble, no explanation outside JSON.
Required fields:
  "overall_assessment" — A 2-4 sentence engineering assessment of this run's outcome.
  "strengths"          — What performed well and why. Be specific about metrics.
  "weaknesses"         — What underperformed, was inconsistent, or warrants investigation.
  "comparison"         — How this run compares to the best run in the experiment. If this is the best, say so clearly with supporting numbers.
  "recommendation"     — One concrete, actionable next experiment to run. Name a specific parameter change or strategy.

Do not include any key other than these five. All values must be plain text strings."""

    return prompt


def _compute_delta(a: float | None, b: float | None) -> tuple[str, str]:
    """
    Return (formatted_delta, direction) for metric comparison.
    direction is one of: 'up', 'down', 'equal', 'unavailable'.
    """
    if a is None or b is None:
        return "N/A", "unavailable"
    diff = b - a
    if abs(diff) < 1e-6:
        return "0.0000", "equal"
    return f"{diff:+.4f}", "up" if diff > 0 else "down"


def build_comparison_prompt(
    *,
    run_a: Any,
    run_b: Any,
    experiment: Any,
    dataset: Any,
    result_a: Any,
    result_b: Any,
) -> str:
    """
    Construct a fully structured Gemini prompt for comparing two training runs.

    Parameters
    ----------
    run_a       : Run ORM object for the first (baseline) run.
    run_b       : Run ORM object for the second (challenger) run.
    experiment  : Experiment ORM object (shared by both runs).
    dataset     : Dataset ORM object.
    result_a    : RunResult ORM object for run_a.
    result_b    : RunResult ORM object for run_b.

    Returns
    -------
    str
        A complete prompt string ready for the Gemini API.
    """

    # ── Dataset info ──────────────────────────────────────────────────────────
    dataset_info = "N/A"
    if dataset:
        dataset_info = (
            f"Name: {dataset.name}, "
            f"Rows: {dataset.row_count}, "
            f"Columns: {dataset.column_count}"
        )

    # ── Run A metrics ─────────────────────────────────────────────────────────
    a_acc  = _fmt_metric(result_a.accuracy if result_a else None)
    a_prec = _fmt_metric(result_a.precision if result_a else None)
    a_rec  = _fmt_metric(result_a.recall if result_a else None)
    a_f1   = _fmt_metric(result_a.f1_score if result_a else None)
    a_roc  = _fmt_metric(result_a.roc_auc if result_a else None)
    a_time = (
        f"{result_a.execution_time_seconds:.2f}s"
        if result_a and result_a.execution_time_seconds
        else "N/A"
    )
    a_cfg = _fmt_config(run_a.training_configuration)

    # ── Run B metrics ─────────────────────────────────────────────────────────
    b_acc  = _fmt_metric(result_b.accuracy if result_b else None)
    b_prec = _fmt_metric(result_b.precision if result_b else None)
    b_rec  = _fmt_metric(result_b.recall if result_b else None)
    b_f1   = _fmt_metric(result_b.f1_score if result_b else None)
    b_roc  = _fmt_metric(result_b.roc_auc if result_b else None)
    b_time = (
        f"{result_b.execution_time_seconds:.2f}s"
        if result_b and result_b.execution_time_seconds
        else "N/A"
    )
    b_cfg = _fmt_config(run_b.training_configuration)

    # ── Explainability info ───────────────────────────────────────────────────
    explainability_section = ""
    def _format_explain(res):
        if res and getattr(res, "explainability_status", None) == "completed" and getattr(res, "explainability_summary", None):
            summary = res.explainability_summary
            top_feats = ", ".join(summary.get("top_features", [])[:5])
            pos_feats = ", ".join(summary.get("positive_contributors", [])[:3])
            neg_feats = ", ".join(summary.get("negative_contributors", [])[:3])
            return f"Top features: {top_feats} | Positive: {pos_feats} | Negative: {neg_feats}"
        return "N/A"
        
    a_explain = _format_explain(result_a)
    b_explain = _format_explain(result_b)
    
    if a_explain != "N/A" or b_explain != "N/A":
        explainability_section = (
            f"\nSHAP EXPLAINABILITY COMPARISON\n"
            f"Run A: {a_explain}\n"
            f"Run B: {b_explain}\n\n"
            f"IMPORTANT: Use these computed SHAP features to explain how the model's focus shifted between runs.\n"
        )

    # ── Deltas (B relative to A) ───────────────────────────────────────────────
    d_acc,  _ = _compute_delta(
        result_a.accuracy if result_a else None,
        result_b.accuracy if result_b else None,
    )
    d_prec, _ = _compute_delta(
        result_a.precision if result_a else None,
        result_b.precision if result_b else None,
    )
    d_rec,  _ = _compute_delta(
        result_a.recall if result_a else None,
        result_b.recall if result_b else None,
    )
    d_f1,   _ = _compute_delta(
        result_a.f1_score if result_a else None,
        result_b.f1_score if result_b else None,
    )
    d_roc,  _ = _compute_delta(
        result_a.roc_auc if result_a else None,
        result_b.roc_auc if result_b else None,
    )

    prompt = f"""You are a senior ML engineer conducting a detailed peer comparison of two training runs from the same experiment.

Your analysis must be professional, precise, and grounded entirely in the data supplied below.
Do not invent metrics, parameters, or observations. If data is unavailable, state that explicitly.
Do not use markdown, bullet points, or code blocks. Write in full sentences and paragraphs only.

CONTEXT
Experiment: {experiment.name}
Objective: {experiment.objective or "Not specified"}
Dataset: {dataset_info}

RUN A (baseline)
Experiment: {experiment.name} — Run #{run_a.run_number} ({run_a.model_type})
Model: {run_a.model_type or "N/A"}
Configuration: {a_cfg}
Accuracy: {a_acc}
Precision: {a_prec}
Recall: {a_rec}
F1 Score: {a_f1}
ROC AUC: {a_roc}
Execution time: {a_time}

RUN B (challenger)
Experiment: {experiment.name} — Run #{run_b.run_number} ({run_b.model_type})
Model: {run_b.model_type or "N/A"}
Configuration: {b_cfg}
Accuracy: {b_acc}
Precision: {b_prec}
Recall: {b_rec}
F1 Score: {b_f1}
ROC AUC: {b_roc}
Execution time: {b_time}

METRIC DELTAS (Run B minus Run A)
Accuracy delta: {d_acc}
Precision delta: {d_prec}
Recall delta: {d_rec}
F1 Score delta: {d_f1}
ROC AUC delta: {d_roc}
{explainability_section}
INSTRUCTIONS
Respond with a single JSON object only. No preamble, no explanation outside JSON.
Required fields:
  "overall_summary"        — 2-4 sentence engineering summary of the comparison outcome. Name specific metrics.
  "better_run"             — State exactly which run is objectively better and why, referencing specific metric values.
  "key_improvements"       — What measurably improved in Run B vs Run A. Reference specific deltas. If Run A is better, state that.
  "tradeoffs"              — Any metrics that worsened, remained flat, or show a precision-recall tradeoff. Be specific.
  "configuration_analysis" — Identify which specific configuration differences (hyperparameters, model type, etc.) most likely caused the observed metric differences. If configurations are identical, state that explicitly.
  "next_recommendation"    — One concrete, actionable next experiment. Name a specific parameter change or strategy based only on this data.

Do not include any key other than these six. All values must be plain text strings."""

    return prompt


# ── Ask MicroFlow (Natural Language Assistant) Prompts ─────────────────────────


def build_intent_prompt(question: str, context: list[dict[str, str]] | None = None) -> str:
    """
    Construct a prompt for Gemini to extract domain intent and search filters
    from a user's natural language question.

    The intent MUST be one of the explicitly whitelisted values or 'unsupported'.
    """
    history_lines = []
    if context:
        for msg in context[-6:]:  # Keep lightweight session memory (up to last 3 turns)
            role = msg.get("role", "user").upper()
            content = msg.get("content", "").strip()
            history_lines.append(f"{role}: {content}")
    history_str = "\n".join(history_lines) if history_lines else "No previous conversational context."

    prompt = f"""You are an intent classification engine for an ML engineering platform named MicroFlow.
Your only task is to analyze the user's natural language question (and brief conversation context) and classify it into an explicit domain intent with relevant filtering constraints.

SUPPORTED INTENTS (Whitelist):
  - "datasets": questions regarding dataset properties, upload status, rows, columns, versions.
  - "experiments": questions regarding experiment goals, descriptions, active or draft experiments.
  - "runs": questions regarding run status, failed runs, completed runs, run counts, or specific run numbers.
  - "metrics": questions regarding evaluation numbers (accuracy, f1, precision, recall, roc auc, execution time).
  - "artifacts": questions regarding generated output files, registered models, plots, confusion matrices.
  - "models": questions focusing on ML algorithm types (Random Forest, XGBoost, Logistic Regression) or configurations.
  - "explainability": questions regarding feature importance, SHAP values, top predictive features, influential variables, or model interpretation.
  - "training_history": historical trends, timeline of experiments, general execution activity.
  - "ai_reviews": inquiries about automated AI peer reviews of specific training runs.
  - "run_comparisons": comparing multiple runs or identifying differences between executions.
  - "performance_summaries": aggregations such as average accuracy across datasets or ranking overall experiments.
  - "next_recommendation": guidance on what hyperparameters or experiment configurations to test next.
  - "best_performing": queries identifying top performers (e.g. "Which experiment has the best accuracy?", "Which Random Forest run performed best?").
  - "unsupported": MUST be assigned if the user asks general programming questions (e.g. writing Python/SQL code), general trivia, internet lookups, or any topic unrelated to this specific machine learning platform.

RECENT CONVERSATION CONTEXT:
{history_str}

USER QUESTION:
{question}

INSTRUCTIONS:
Respond with a single strict JSON object only. No explanatory text, no markdown outside the JSON structure.
Required format:
{{
  "intent": "<one of the exact strings from SUPPORTED INTENTS>",
  "filters": {{
    "model_type": "<e.g., random_forest, xgboost, logistic_regression, or null if unspecified>",
    "status": "<e.g., completed, failed, active, draft, queued, running, or null if unspecified>",
    "metric_sort": "<e.g., accuracy, f1_score, precision, recall, roc_auc, execution_time_seconds, or null if unspecified>"
  }},
  "reasoning_required": true
}}"""
    return prompt


def build_assistant_prompt(
    question: str,
    intent: str,
    structured_data: str,
    context: list[dict[str, str]] | None = None,
    semantic_documents: list[dict[str, Any]] | None = None,
) -> str:
    """
    Construct a prompt for Gemini to synthesize a professional engineering response
    combining structured SQL database records with semantically retrieved pgvector documents.
    """
    history_lines = []
    if context:
        for msg in context[-6:]:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "").strip()
            history_lines.append(f"{role}: {content}")
    history_str = "\n".join(history_lines) if history_lines else "No previous conversational context."

    doc_blocks = []
    if semantic_documents:
        for idx, doc in enumerate(semantic_documents, start=1):
            title = doc.get("title", f"Document #{idx}")
            content = doc.get("content", "").strip()
            doc_blocks.append(f"--- Document #{idx}: [{title}] ---\n{content}")
    semantic_str = "\n\n".join(doc_blocks) if doc_blocks else "No relevant semantic knowledge documents were retrieved."

    prompt = f"""You are MicroFlow Assistant, a specialized machine learning platform AI answering engineering questions about ML experimentation data.

CRITICAL ENGINEERING CONSTRAINTS (HYBRID RAG):
1. Ground Truth: Your response must rely strictly and entirely on the AUTHENTIC DATABASE RESULTS (Structured SQL Telemetry) and the SEMANTIC KNOWLEDGE BASE (Retrieved pgvector Documents) provided below. Never invent runs, hallucinate metrics, or guess parameter values.
2. Conflict Resolution: If structured database metrics and retrieved semantic documents conflict, explicitly point out the conflict.
3. Insufficient Evidence: If data is missing or evidence is insufficient to answer the question, explicitly state so rather than guessing.
4. No Formatting Abuse: Never output markdown tables. Never output code blocks or raw SQL/Python code. Write in clear, concise, professional engineering full sentences and structured paragraphs.
5. Tone: Maintain a formal, analytical ML software engineering tone.

RECENT CONVERSATION CONTEXT:
{history_str}

USER QUESTION:
{question}

RESOLVED INTENT:
{intent}

AUTHENTIC DATABASE RESULTS (Structured Telemetry Source of Truth):
{structured_data}

SEMANTIC KNOWLEDGE BASE (Retrieved pgvector Narrative Documents):
{semantic_str}

INSTRUCTIONS:
Respond with a single strict JSON object only. No preamble or commentary outside the JSON structure.
Required format:
{{
  "answer": "A precise, direct engineering answer to the question in professional full sentences grounded in both structured data and retrieved semantic context.",
  "reasoning": "Clear analytical reasoning explaining why this outcome occurred or how the conclusion was derived directly from the provided structured results and semantic documents.",
  "supporting_data": "Key numerical metrics, run numbers, dataset counts, or hyperparameter details extracted from the database results supporting your answer.",
  "recommendation": "One concrete, actionable engineering recommendation for next steps (or 'No further action required' if not applicable)."
}}"""
    return prompt


def build_dataset_analysis_prompt(
    dataset: Any,
    statistics: dict[str, Any],
    preview_rows: list[dict[str, Any]],
    quality_score: int,
    quality_label: str,
) -> str:
    """
    Construct a deterministic prompt for Gemini to analyze a dataset and produce
    a comprehensive engineering report before training begins. Zero hallucinations.
    """
    col_summary_lines = []
    for col_name in (dataset.column_names or []):
        dtype = (dataset.dtypes or {}).get(col_name, "unknown")
        missing_cnt = (dataset.missing_values or {}).get(col_name, 0)
        col_stat = statistics.get(col_name, {})
        stat_str = ", ".join(f"{k}={v}" for k, v in col_stat.items() if v is not None)
        col_summary_lines.append(f"- Column '{col_name}' (type: {dtype}, missing: {missing_cnt}): {stat_str}")

    cols_block = "\n".join(col_summary_lines) if col_summary_lines else "No column schema recorded."

    preview_block_lines = []
    for idx, row in enumerate(preview_rows[:5], 1):
        row_str = ", ".join(f"{k}={v!r}" for k, v in row.items())
        preview_block_lines.append(f"Row #{idx}: {{{row_str}}}")
    preview_block = "\n".join(preview_block_lines) if preview_block_lines else "No preview rows available."

    prompt = f"""You are Antigravity, an advanced machine learning data scientist evaluating an uploaded dataset for MicroFlow before any training begins.

CRITICAL INSTRUCTIONS:
1. Ground Truth: Reason ONLY from the actual dataset metadata, statistics, column types, missing value counts, and preview rows provided below. Never hallucinate values, numbers, or features that are not explicitly present.
2. Target Detection: Examine column names and unique values to suggest the most logical target column for supervised ML. If no obvious target column exists, explain why clearly—never guess arbitrarily.
3. Preprocessing: Recommend preprocessing steps (encoding, missing value handling, normalization, scaling, balancing) only if justified by the statistics.
4. Model Recommendations: Recommend specific suitable models (e.g., Random Forest, Logistic Regression, XGBoost) with concise engineering justifications based on data volume and feature types.
5. Quality Assessment: The deterministic quality score for this dataset has already been calculated as {quality_score}/100 ({quality_label}). Incorporate this exact score and label into your evaluation.
6. Tone & Format: Maintain a formal, authoritative data engineering tone. Return a single strict JSON object only without code fences or surrounding commentary.

DATASET METADATA:
- Name: "{dataset.name}" (Version: {dataset.version})
- Description: "{dataset.description or 'None provided'}"
- Dimensions: {dataset.row_count} total rows, {dataset.column_count} total columns
- File Size: {dataset.file_size_bytes} bytes
- Pre-calculated Quality Score: {quality_score}/100 ({quality_label})

COLUMN SCHEMA & SUMMARY STATISTICS:
{cols_block}

SAMPLE PREVIEW ROWS:
{preview_block}

REQUIRED JSON SCHEMA (Return exactly these 10 keys):
{{
  "overall_summary": "A cohesive 2-3 sentence executive summary of the dataset structure and analytical readiness.",
  "recommended_target": "Name of the optimal target column and a brief explanation of why (or why none is suitable).",
  "dataset_quality": {{"score": {quality_score}, "label": "{quality_label}", "explanation": "Brief rationale citing missing value ratios and feature completeness."}},
  "strengths": ["List of distinct data strengths, such as complete columns, rich categorical features, or adequate sample size."],
  "potential_issues": ["List of identified risks, such as missing values, class imbalance, potential leakage, or high dimensionality."],
  "recommended_preprocessing": ["Ordered list of justified preprocessing steps before model ingestion."],
  "recommended_models": [
    {{"model": "Random Forest | Logistic Regression | XGBoost | etc.", "suitability": "High | Medium | Low", "reasoning": "Why this algorithm works well for this specific data structure."}}
  ],
  "feature_observations": [
    {{"feature": "Column name", "observation": "Concise analytical note on distribution, scaling needs, or cardinality."}}
  ],
  "risk_assessment": "Summary assessment of potential operational or training hazards (e.g., overfitting on small samples, null handling failures).",
  "next_steps": ["Concrete, numbered action items for an engineer ready to configure their first experiment."]
}}"""
    return prompt


# ── AI Experiment Strategy Prompts ──────────────────────────────────────────────


def build_experiment_strategy_prompt(
    experiment: Any,
    dataset: Any,
    evidence: dict[str, Any],
) -> str:
    """
    Construct a deterministic prompt for Gemini to act as an evidence-driven
    engineering strategist for an experiment. Zero hallucinations or guessing.
    """
    import json

    evidence_json_str = json.dumps(evidence, indent=2, default=str)

    prompt = f"""You are Antigravity, an advanced machine learning engineering strategist analyzing experiment runs and dataset evidence for MicroFlow.
Your objective is to evaluate the history of this experiment and recommend the most valuable NEXT experiment configuration, or explicitly advise terminating experimentation if metrics have plateaued.

CRITICAL INSTRUCTIONS (EVIDENCE-DRIVEN STRATEGY):
1. ZERO HALLUCINATIONS: All evaluations, parameter observations, and recommendations MUST be derived exclusively from the actual experiment history, metric trends, and dataset evidence provided below. Never invent facts, hyperparameter values, or historical runs.
2. NO SPECULATION OR GENERATIVE GUESSING: You are NOT an automated AutoML trial generator throwing arbitrary guesses. If evidence is insufficient to justify a specific hyperparameter change or architectural switch, explicitly state that evidence is insufficient rather than guessing.
3. PLATEAU DETECTION & STOPPING CRITERIA: Carefully inspect the metric improvement trends and plateau flags in the evidence. If metrics have plateaued, or if observed improvements over recent runs are statistically insignificant or within variance bounds, you MUST recommend ending further algorithm/hyperparameter tuning. Instead, suggest concrete alternatives such as feature engineering, better data collection, cleaning noisy samples, or addressing data imbalances.
4. CONFIDENCE RATING: Every recommendation MUST specify an explicit confidence level: exactly one of "High", "Medium", or "Low", backed directly by sample sizes, consistency of metric gains, and search space coverage.
5. TONE & FORMAT: Maintain a rigorous, quantitative engineering tone. Return a single strict JSON object only without code fences or surrounding commentary.

EXPERIMENT CONTEXT:
- Experiment ID: "{experiment.id}"
- Experiment Name: "{experiment.name}"
- Objective & Description: "{experiment.objective or 'Not specified'}" | "{experiment.description or 'No description'}"
- Dataset Name: "{dataset.name}" (Rows: {dataset.row_count}, Columns: {dataset.column_count}, Quality: {evidence.get('dataset_summary', {}).get('quality_label', 'Unknown')} - {evidence.get('dataset_summary', {}).get('quality_score', 'N/A')}/100)

COMPUTED QUANTITATIVE EVIDENCE (Historical Runs, Trends, Variance, Search Space, and Plateaus):
{evidence_json_str}

REQUIRED JSON SCHEMA (Return exactly these 11 keys):
{{
  "overall_assessment": "A concise 2-3 sentence executive evaluation of what has been accomplished in this experiment so far.",
  "current_experiment_status": "Status category (e.g. 'Early Exploration', 'Active Optimization', 'Plateaued / Diminishing Returns', 'No Runs Executed').",
  "observed_trends": ["Chronological list of data-driven performance trajectories, parameter sensitivities, and metric correlations observed across runs."],
  "strongest_model": "Exact model family and configuration producing the best objective metrics (or 'N/A if no completed runs').",
  "most_stable_model": "Model configuration showing consistent performance with low variance or highly reliable execution.",
  "what_has_been_learned": ["Concrete, empirical engineering findings established from past completed and failed runs."],
  "remaining_search_space": ["Unexplored supported algorithm families (Random Forest, XGBoost, Logistic Regression) or unvisited hyperparameter regions."],
  "recommended_next_experiment": {{"action": "Specific next training configuration OR explicit advice to stop tuning", "model_type": "Suggested model family or N/A", "hyperparameters": {{"key": "value or reasoning"}}, "rationale": "Empirical justification based on historical deltas and search space."}},
  "confidence": "High | Medium | Low",
  "evidence_used": ["List of exact metric values, run comparisons, variance figures, or dataset traits supporting this strategy."],
  "potential_risks": ["Identified operational hazards (e.g. overfitting small samples, computational waste on saturated search space, precision-recall tradeoffs)."]
}}"""
    return prompt

