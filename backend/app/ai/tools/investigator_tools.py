"""
ai/tools/investigator_tools.py — Five locked read-only tools for the Experiment Investigator.

Wraps existing MicroFlow services:
1. get_experiment_runs -> RunService.get_by_experiment
2. get_run_config -> RunService.get_by_id
3. get_run_metrics -> RunResultService.get_by_run_id
4. compare_runs -> MetricsService.compare_runs
5. get_feature_importance -> RunResultService.get_by_run_id
"""

from __future__ import annotations

import logging
from typing import Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.metrics_service import MetricsService
from app.services.run_result_service import RunResultService
from app.services.run_service import RunService

logger = logging.getLogger(__name__)

ALLOWED_TOOL_NAMES = frozenset({
    "get_experiment_runs",
    "get_run_config",
    "get_run_metrics",
    "compare_runs",
    "get_feature_importance",
})


# ─── Tool 1: get_experiment_runs ─────────────────────────────────────────────

def get_experiment_runs(
    experiment_id: str,
    db: Session,
    run_service: RunService,
) -> dict[str, Any]:
    """Retrieve all runs associated with an experiment."""
    if not experiment_id or not isinstance(experiment_id, str) or not experiment_id.strip():
        return {
            "success": False,
            "error_type": "InvalidInput",
            "message": "experiment_id must be a non-empty string.",
        }

    try:
        runs = run_service.get_by_experiment(experiment_id.strip(), db)
        formatted_runs = [
            {
                "run_id": r.id,
                "run_number": r.run_number,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "model_type": r.model_type,
                "notes": r.notes,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in runs
        ]
        return {
            "success": True,
            "data": {
                "experiment_id": experiment_id,
                "total_runs": len(formatted_runs),
                "runs": formatted_runs,
            },
        }
    except HTTPException as exc:
        return {
            "success": False,
            "error_type": "NotFound" if exc.status_code == 404 else "HttpError",
            "message": str(exc.detail),
        }
    except Exception as exc:
        logger.exception("Error executing get_experiment_runs for '%s'", experiment_id)
        return {
            "success": False,
            "error_type": "ExecutionError",
            "message": str(exc),
        }


# ─── Tool 2: get_run_config ──────────────────────────────────────────────────

def get_run_config(
    run_id: str,
    db: Session,
    run_service: RunService,
) -> dict[str, Any]:
    """Retrieve hyperparameters, configuration, and status for a specific run."""
    if not run_id or not isinstance(run_id, str) or not run_id.strip():
        return {
            "success": False,
            "error_type": "InvalidInput",
            "message": "run_id must be a non-empty string.",
        }

    try:
        run = run_service.get_by_id(run_id.strip(), db)
        return {
            "success": True,
            "data": {
                "run_id": run.id,
                "run_number": run.run_number,
                "experiment_id": run.experiment_id,
                "model_type": run.model_type,
                "status": run.status.value if hasattr(run.status, "value") else str(run.status),
                "training_configuration": run.training_configuration or {},
                "notes": run.notes,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            },
        }
    except HTTPException as exc:
        return {
            "success": False,
            "error_type": "NotFound" if exc.status_code == 404 else "HttpError",
            "message": str(exc.detail),
        }
    except Exception as exc:
        logger.exception("Error executing get_run_config for '%s'", run_id)
        return {
            "success": False,
            "error_type": "ExecutionError",
            "message": str(exc),
        }


# ─── Tool 3: get_run_metrics ─────────────────────────────────────────────────

def get_run_metrics(
    run_id: str,
    db: Session,
    run_result_service: RunResultService,
) -> dict[str, Any]:
    """Retrieve quantitative performance metrics for a specific completed run."""
    if not run_id or not isinstance(run_id, str) or not run_id.strip():
        return {
            "success": False,
            "error_type": "InvalidInput",
            "message": "run_id must be a non-empty string.",
        }

    try:
        result = run_result_service.get_by_run_id(run_id.strip(), db)
        if not result:
            return {
                "success": False,
                "error_type": "NoMetricsAvailable",
                "message": f"Run '{run_id}' has no recorded evaluation metrics. The run might not have completed successfully or is still pending.",
            }

        return {
            "success": True,
            "data": {
                "run_id": run_id.strip(),
                "model_type": result.model_type,
                "metrics": {
                    "accuracy": round(float(result.accuracy), 4) if result.accuracy is not None else None,
                    "precision": round(float(result.precision), 4) if result.precision is not None else None,
                    "recall": round(float(result.recall), 4) if result.recall is not None else None,
                    "f1_score": round(float(result.f1_score), 4) if result.f1_score is not None else None,
                    "roc_auc": round(float(result.roc_auc), 4) if result.roc_auc is not None else None,
                    "execution_time_seconds": round(float(result.execution_time_seconds), 2) if result.execution_time_seconds is not None else None,
                },
                "started_at": result.started_at.isoformat() if result.started_at else None,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            },
        }
    except Exception as exc:
        logger.exception("Error executing get_run_metrics for '%s'", run_id)
        return {
            "success": False,
            "error_type": "ExecutionError",
            "message": str(exc),
        }


# ─── Tool 4: compare_runs ────────────────────────────────────────────────────

def compare_runs(
    run_ids: list[str] | str,
    db: Session,
    metrics_service: MetricsService,
) -> dict[str, Any]:
    """Compare performance metrics and configurations side-by-side across multiple runs."""
    if isinstance(run_ids, str):
        cleaned_ids = [r.strip() for r in run_ids.split(",") if r.strip()]
    elif isinstance(run_ids, list):
        cleaned_ids = [str(r).strip() for r in run_ids if str(r).strip()]
    else:
        return {
            "success": False,
            "error_type": "InvalidInput",
            "message": "run_ids must be a list of string run IDs or a comma-separated string.",
        }

    if not cleaned_ids:
        return {
            "success": False,
            "error_type": "InvalidInput",
            "message": "At least one run_id must be provided to compare.",
        }

    try:
        comparison = metrics_service.compare_runs(cleaned_ids, db)
        if not comparison:
            return {
                "success": False,
                "error_type": "ComparisonEmpty",
                "message": f"None of the requested runs ({cleaned_ids}) have recorded metrics for comparison.",
            }

        return {
            "success": True,
            "data": {
                "compared_runs_count": len(comparison),
                "runs": comparison,
            },
        }
    except Exception as exc:
        logger.exception("Error executing compare_runs for '%s'", cleaned_ids)
        return {
            "success": False,
            "error_type": "ExecutionError",
            "message": str(exc),
        }


# ─── Tool 5: get_feature_importance ─────────────────────────────────────────

def get_feature_importance(
    run_id: str,
    db: Session,
    run_result_service: RunResultService,
) -> dict[str, Any]:
    """Retrieve pre-calculated SHAP feature importance and explainability summary for a run."""
    if not run_id or not isinstance(run_id, str) or not run_id.strip():
        return {
            "success": False,
            "error_type": "InvalidInput",
            "message": "run_id must be a non-empty string.",
        }

    try:
        result = run_result_service.get_by_run_id(run_id.strip(), db)
        if not result:
            return {
                "success": False,
                "error_type": "NotFound",
                "message": f"Run result for run '{run_id}' not found.",
            }

        status = result.explainability_status or "not_generated"
        return {
            "success": True,
            "data": {
                "run_id": run_id.strip(),
                "explainability_status": status,
                "explainability_summary": result.explainability_summary,
                "explainability_error": result.explainability_error,
            },
        }
    except Exception as exc:
        logger.exception("Error executing get_feature_importance for '%s'", run_id)
        return {
            "success": False,
            "error_type": "ExecutionError",
            "message": str(exc),
        }


# ─── Dispatcher ──────────────────────────────────────────────────────────────

def dispatch_tool(
    name: str,
    arguments: dict[str, Any],
    db: Session,
    run_service: RunService,
    run_result_service: RunResultService,
    metrics_service: MetricsService,
) -> dict[str, Any]:
    """
    Safely dispatch a tool call from Gemini to the matching Python tool wrapper.
    Guarantees structured error handling and strict allowlist enforcement.
    """
    if name not in ALLOWED_TOOL_NAMES:
        return {
            "success": False,
            "error_type": "DisallowedTool",
            "message": f"Tool '{name}' is not in the allowlist of permitted investigator tools.",
        }

    try:
        if name == "get_experiment_runs":
            experiment_id = arguments.get("experiment_id")
            return get_experiment_runs(experiment_id, db, run_service)

        elif name == "get_run_config":
            run_id = arguments.get("run_id")
            return get_run_config(run_id, db, run_service)

        elif name == "get_run_metrics":
            run_id = arguments.get("run_id")
            return get_run_metrics(run_id, db, run_result_service)

        elif name == "compare_runs":
            run_ids = arguments.get("run_ids")
            return compare_runs(run_ids, db, metrics_service)

        elif name == "get_feature_importance":
            run_id = arguments.get("run_id")
            return get_feature_importance(run_id, db, run_result_service)

        else:
            return {
                "success": False,
                "error_type": "UnknownTool",
                "message": f"Unhandled tool '{name}'",
            }
    except Exception as exc:
        logger.exception("Unexpected exception in tool dispatcher for '%s'", name)
        return {
            "success": False,
            "error_type": "DispatcherError",
            "message": f"Failed to execute '{name}': {exc}",
        }


# ─── Gemini Tool Definitions ─────────────────────────────────────────────────

INVESTIGATOR_TOOL_DECLARATIONS = [
    {
        "name": "get_experiment_runs",
        "description": "Retrieve all runs belonging to a specific experiment, including run IDs, run numbers, statuses, model types, and timestamps. Always call this first when you need to discover what runs exist in the experiment.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "experiment_id": {
                    "type": "STRING",
                    "description": "The unique ID of the experiment to inspect.",
                }
            },
            "required": ["experiment_id"],
        },
    },
    {
        "name": "get_run_config",
        "description": "Retrieve the exact hyperparameters, configuration overrides, dataset settings, and model type used for a specific run ID.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "run_id": {
                    "type": "STRING",
                    "description": "The unique ID of the run to inspect.",
                }
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "get_run_metrics",
        "description": "Retrieve the quantitative evaluation metrics (accuracy, precision, recall, f1_score, roc_auc, execution time) for a completed run ID.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "run_id": {
                    "type": "STRING",
                    "description": "The unique ID of the completed run.",
                }
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "compare_runs",
        "description": "Perform a side-by-side comparison of metrics and training configurations across two or more run IDs. Useful for diagnosing performance differences.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "run_ids": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "List of run IDs to compare side-by-side.",
                }
            },
            "required": ["run_ids"],
        },
    },
    {
        "name": "get_feature_importance",
        "description": "Retrieve the pre-calculated SHAP explainability summary for a run ID, indicating the top influential features and their impact direction on model predictions.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "run_id": {
                    "type": "STRING",
                    "description": "The unique ID of the run.",
                }
            },
            "required": ["run_id"],
        },
    },
]
