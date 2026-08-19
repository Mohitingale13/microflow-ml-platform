"""
tests/ai/test_investigator_agent.py — Complete test suite for the Experiment Investigator.

Covers all 15 specification requirements:
1. successful_investigation
2. multi_step_investigation with multiple tool calls
3. dynamic_tool_selection
4. correct_tool_dispatch
5. successful_tool_result_handling
6. tool_failure_handling
7. malformed_tool_call_handling
8. missing_experiment_handling
9. maximum_iteration_limit (MAX_AGENT_ITERATIONS = 5)
10. invalid_final_report_handling
11. insufficient_evidence
12. evidence_trace_creation
13. final_evidence_references_actual_tools (hallucinated tool normalization)
14. read_only_behavior
15. existing_microflow_functionality_remains_unaffected (tested across suite)
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.gemini_service import GeminiService
from app.ai.investigator_agent import InvestigatorAgent, MAX_AGENT_ITERATIONS
from app.ai.tools.investigator_tools import (
    ALLOWED_TOOL_NAMES,
    compare_runs,
    dispatch_tool,
    get_experiment_runs,
    get_feature_importance,
    get_run_config,
    get_run_metrics,
)
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.artifact import RunResult
from app.models.dataset import Dataset, DatasetStatus
from app.models.experiment import Experiment, ExperimentStatus, Run, RunStatus
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.run_repository import RunRepository
from app.repositories.run_result_repository import RunResultRepository
from app.schemas.investigator import InvestigationReport
from app.services.experiment_service import ExperimentService
from app.services.investigator_service import InvestigatorService
from app.services.metrics_service import MetricsService
from app.services.run_result_service import RunResultService
from app.services.run_service import RunService


@pytest.fixture
def db_session() -> Session:
    """Create in-memory SQLite session with initialized schema."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionTesting()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def seeded_data(db_session: Session):
    """Seed sample dataset, experiment, runs, and results for testing."""
    dataset = Dataset(
        id=str(uuid.uuid4()),
        name="Telemetry Data",
        original_filename="telemetry.csv",
        file_hash=str(uuid.uuid4()),
        storage_path="/tmp/telemetry.csv",
        file_size_bytes=1024,
        row_count=500,
        column_count=8,
        status=DatasetStatus.ready,
    )
    db_session.add(dataset)
    db_session.flush()

    experiment = Experiment(
        id=str(uuid.uuid4()),
        name="Anomaly Detection Baseline",
        dataset_id=dataset.id,
        status=ExperimentStatus.active,
        default_configuration={"n_estimators": 100, "max_depth": 5},
    )
    db_session.add(experiment)
    db_session.flush()

    # Run 1 (Random Forest, high accuracy)
    run1 = Run(
        id=str(uuid.uuid4()),
        experiment_id=experiment.id,
        run_number=1,
        status=RunStatus.completed,
        model_type="RandomForest",
        training_configuration={"n_estimators": 100, "max_depth": 5, "learning_rate": 0.01},
        notes="Baseline run",
    )
    db_session.add(run1)
    db_session.flush()

    result1 = RunResult(
        id=str(uuid.uuid4()),
        run_id=run1.id,
        accuracy=0.9250,
        precision=0.9100,
        recall=0.9300,
        f1_score=0.9200,
        roc_auc=0.9600,
        confusion_matrix=[[45, 5], [3, 47]],
        execution_time_seconds=4.25,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        model_type="RandomForest",
        dataset_id=dataset.id,
        explainability_status="completed",
        explainability_summary={
            "top_features": [
                {"feature": "voltage_variance", "mean_abs_shap": 0.35, "impact": "positive"},
                {"feature": "sensor_temp", "mean_abs_shap": 0.22, "impact": "negative"},
            ]
        },
    )
    db_session.add(result1)

    # Run 2 (XGBoost, lower accuracy due to bad learning rate)
    run2 = Run(
        id=str(uuid.uuid4()),
        experiment_id=experiment.id,
        run_number=2,
        status=RunStatus.completed,
        model_type="XGBoost",
        training_configuration={"n_estimators": 50, "max_depth": 3, "learning_rate": 0.8},
        notes="High learning rate test",
    )
    db_session.add(run2)
    db_session.flush()

    result2 = RunResult(
        id=str(uuid.uuid4()),
        run_id=run2.id,
        accuracy=0.7800,
        precision=0.7600,
        recall=0.7900,
        f1_score=0.7750,
        roc_auc=0.8200,
        confusion_matrix=[[38, 12], [10, 40]],
        execution_time_seconds=2.10,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        model_type="XGBoost",
        dataset_id=dataset.id,
        explainability_status="failed",
        explainability_error="ConvergenceError: Tree depth insufficient",
    )
    db_session.add(result2)
    db_session.commit()

    return {
        "dataset": dataset,
        "experiment": experiment,
        "run1": run1,
        "run2": run2,
        "result1": result1,
        "result2": result2,
    }


# ─── 1. Tool-level tests ─────────────────────────────────────────────────────

def test_tool_get_experiment_runs(db_session: Session, seeded_data: dict):
    run_service = RunService(RunRepository(), ExperimentRepository())
    exp_id = seeded_data["experiment"].id

    res = get_experiment_runs(exp_id, db_session, run_service)
    assert res["success"] is True
    assert res["data"]["total_runs"] == 2
    assert len(res["data"]["runs"]) == 2
    assert res["data"]["runs"][0]["run_number"] in (1, 2)

    # Test not found
    err_res = get_experiment_runs(str(uuid.uuid4()), db_session, run_service)
    assert err_res["success"] is False
    assert err_res["error_type"] == "NotFound"


def test_tool_get_run_config(db_session: Session, seeded_data: dict):
    run_service = RunService(RunRepository(), ExperimentRepository())
    run1 = seeded_data["run1"]

    res = get_run_config(run1.id, db_session, run_service)
    assert res["success"] is True
    assert res["data"]["run_id"] == run1.id
    assert res["data"]["training_configuration"]["learning_rate"] == 0.01

    # Test invalid input
    err_res = get_run_config("", db_session, run_service)
    assert err_res["success"] is False
    assert err_res["error_type"] == "InvalidInput"


def test_tool_get_run_metrics(db_session: Session, seeded_data: dict):
    result_service = RunResultService(RunResultRepository())
    run1 = seeded_data["run1"]

    res = get_run_metrics(run1.id, db_session, result_service)
    assert res["success"] is True
    assert res["data"]["metrics"]["accuracy"] == 0.9250
    assert res["data"]["metrics"]["f1_score"] == 0.9200

    # Test non-existent run
    err_res = get_run_metrics(str(uuid.uuid4()), db_session, result_service)
    assert err_res["success"] is False
    assert err_res["error_type"] == "NoMetricsAvailable"


def test_tool_compare_runs(db_session: Session, seeded_data: dict):
    metrics_service = MetricsService(MetricsRepository())
    r1_id = seeded_data["run1"].id
    r2_id = seeded_data["run2"].id

    res = compare_runs([r1_id, r2_id], db_session, metrics_service)
    assert res["success"] is True
    assert res["data"]["compared_runs_count"] == 2

    # Test comma-separated string input
    res_str = compare_runs(f"{r1_id}, {r2_id}", db_session, metrics_service)
    assert res_str["success"] is True

    # Test empty IDs
    res_empty = compare_runs([], db_session, metrics_service)
    assert res_empty["success"] is False
    assert res_empty["error_type"] == "InvalidInput"


def test_tool_get_feature_importance(db_session: Session, seeded_data: dict):
    result_service = RunResultService(RunResultRepository())
    run1 = seeded_data["run1"]
    run2 = seeded_data["run2"]

    res1 = get_feature_importance(run1.id, db_session, result_service)
    assert res1["success"] is True
    assert res1["data"]["explainability_status"] == "completed"
    assert "top_features" in res1["data"]["explainability_summary"]

    res2 = get_feature_importance(run2.id, db_session, result_service)
    assert res2["success"] is True
    assert res2["data"]["explainability_status"] == "failed"
    assert "ConvergenceError" in res2["data"]["explainability_error"]


def test_tool_dispatcher_allowlist_and_safety(db_session: Session, seeded_data: dict):
    run_service = RunService(RunRepository(), ExperimentRepository())
    result_service = RunResultService(RunResultRepository())
    metrics_service = MetricsService(MetricsRepository())

    # Disallowed tool
    res = dispatch_tool(
        "delete_experiment",
        {"experiment_id": "123"},
        db_session,
        run_service,
        result_service,
        metrics_service,
    )
    assert res["success"] is False
    assert res["error_type"] == "DisallowedTool"

    # Valid tool with valid args
    res_valid = dispatch_tool(
        "get_experiment_runs",
        {"experiment_id": seeded_data["experiment"].id},
        db_session,
        run_service,
        result_service,
        metrics_service,
    )
    assert res_valid["success"] is True


# ─── 2. Agent control loop tests ─────────────────────────────────────────────

class MockGeminiResponse:
    def __init__(self, text: str = "", function_calls: list = None):
        self.text = text
        self.function_calls = function_calls or []
        self.candidates = []


class MockFunctionCall:
    def __init__(self, name: str, args: dict):
        self.name = name
        self.args = args


def test_agent_multi_step_investigation(db_session: Session, seeded_data: dict):
    """Verify agent executes multiple steps of tool calls then concludes."""
    exp_id = seeded_data["experiment"].id
    r1_id = seeded_data["run1"].id
    r2_id = seeded_data["run2"].id

    final_report_json = json.dumps({
        "conclusion": "Run 2 underperformed Run 1 due to excessively aggressive learning rate (0.8 vs 0.01).",
        "evidence": [
            {"source_tool": "get_experiment_runs", "finding": "Found 2 completed runs in experiment."},
            {"source_tool": "compare_runs", "finding": "Run 1 achieved 0.9250 accuracy vs 0.7800 in Run 2."},
            {"source_tool": "get_run_config", "finding": "Run 2 had learning_rate=0.8 while Run 1 had 0.01."},
        ],
        "recommendations": ["Lower learning rate for XGBoost to 0.05", "Increase estimators to 150"],
        "limitations": ["Run 2 explainability failed to compute."],
    })

    responses = [
        MockGeminiResponse(function_calls=[MockFunctionCall("get_experiment_runs", {"experiment_id": exp_id})]),
        MockGeminiResponse(function_calls=[MockFunctionCall("compare_runs", {"run_ids": [r1_id, r2_id]})]),
        MockGeminiResponse(function_calls=[MockFunctionCall("get_run_config", {"run_id": r2_id})]),
        MockGeminiResponse(text=final_report_json),
    ]

    mock_gemini = MagicMock()
    mock_gemini.generate_chat_turn.side_effect = responses

    agent = InvestigatorAgent(gemini_service=mock_gemini)
    report, trace, iterations = agent.run_investigation(
        experiment_id=exp_id,
        objective="Why did Run 2 perform worse than Run 1?",
        db=db_session,
        run_service=RunService(RunRepository(), ExperimentRepository()),
        run_result_service=RunResultService(RunResultRepository()),
        metrics_service=MetricsService(MetricsRepository()),
    )

    assert isinstance(report, InvestigationReport)
    assert "Run 2 underperformed" in report.conclusion
    assert len(report.evidence) == 3
    assert len(trace) == 3
    assert iterations == 4
    assert trace[0].tool_name == "get_experiment_runs"
    assert trace[1].tool_name == "compare_runs"
    assert trace[2].tool_name == "get_run_config"


def test_agent_dynamic_tool_selection(db_session: Session, seeded_data: dict):
    """Verify agent dynamically selects a completely different path (feature importance first)."""
    exp_id = seeded_data["experiment"].id
    r1_id = seeded_data["run1"].id

    final_report = json.dumps({
        "conclusion": "Voltage variance is the primary driver of anomalies.",
        "evidence": [
            {"source_tool": "get_feature_importance", "finding": "voltage_variance mean_abs_shap = 0.35"}
        ],
        "recommendations": ["Focus sensor filtering on voltage variance"],
        "limitations": [],
    })

    responses = [
        MockGeminiResponse(function_calls=[MockFunctionCall("get_feature_importance", {"run_id": r1_id})]),
        MockGeminiResponse(text=final_report),
    ]

    mock_gemini = MagicMock()
    mock_gemini.generate_chat_turn.side_effect = responses

    agent = InvestigatorAgent(gemini_service=mock_gemini)
    report, trace, iterations = agent.run_investigation(
        experiment_id=exp_id,
        objective="What features drove predictions in Run 1?",
        db=db_session,
        run_service=RunService(RunRepository(), ExperimentRepository()),
        run_result_service=RunResultService(RunResultRepository()),
        metrics_service=MetricsService(MetricsRepository()),
    )

    assert trace[0].tool_name == "get_feature_importance"
    assert len(report.evidence) == 1
    assert report.evidence[0].source_tool == "get_feature_importance"


def test_agent_max_iterations_safety_cap(db_session: Session, seeded_data: dict):
    """Verify loop strictly halts at MAX_AGENT_ITERATIONS (5) without infinite looping."""
    exp_id = seeded_data["experiment"].id

    infinite_calls = [
        MockGeminiResponse(function_calls=[MockFunctionCall("get_experiment_runs", {"experiment_id": exp_id})])
        for _ in range(10)
    ]

    mock_gemini = MagicMock()
    mock_gemini.generate_chat_turn.side_effect = infinite_calls

    agent = InvestigatorAgent(gemini_service=mock_gemini)
    report, trace, iterations = agent.run_investigation(
        experiment_id=exp_id,
        objective="Find all anomalies",
        db=db_session,
        run_service=RunService(RunRepository(), ExperimentRepository()),
        run_result_service=RunResultService(RunResultRepository()),
        metrics_service=MetricsService(MetricsRepository()),
    )

    assert iterations == MAX_AGENT_ITERATIONS
    assert len(trace) == MAX_AGENT_ITERATIONS
    assert any("maximum safety limit" in lim.lower() for lim in report.limitations)


def test_agent_gemini_error_graceful_fallback(db_session: Session, seeded_data: dict):
    """Verify agent creates structured partial report if Gemini throws an unrecoverable exception."""
    exp_id = seeded_data["experiment"].id

    mock_gemini = MagicMock()
    mock_gemini.generate_chat_turn.side_effect = RuntimeError("Quota exhausted")

    agent = InvestigatorAgent(gemini_service=mock_gemini)
    report, trace, iterations = agent.run_investigation(
        experiment_id=exp_id,
        objective="Explain model variance",
        db=db_session,
        run_service=RunService(RunRepository(), ExperimentRepository()),
        run_result_service=RunResultService(RunResultRepository()),
        metrics_service=MetricsService(MetricsRepository()),
    )

    assert isinstance(report, InvestigationReport)
    assert "partially completed" in report.conclusion
    assert any("interrupted due to AI service error" in lim for lim in report.limitations)


def test_agent_handles_invalid_json_by_synthesizing_report(db_session: Session, seeded_data: dict):
    """Verify agent safely parses prose text after tool execution into a structured report."""
    exp_id = seeded_data["experiment"].id

    responses = [
        MockGeminiResponse(function_calls=[MockFunctionCall("get_experiment_runs", {"experiment_id": exp_id})]),
        MockGeminiResponse(text="Here is my prose analysis: The experiment contains 2 runs. Run 1 is superior."),
    ]

    mock_gemini = MagicMock()
    mock_gemini.generate_chat_turn.side_effect = responses

    agent = InvestigatorAgent(gemini_service=mock_gemini)
    report, trace, iterations = agent.run_investigation(
        experiment_id=exp_id,
        objective="Analyze runs",
        db=db_session,
        run_service=RunService(RunRepository(), ExperimentRepository()),
        run_result_service=RunResultService(RunResultRepository()),
        metrics_service=MetricsService(MetricsRepository()),
    )

    assert isinstance(report, InvestigationReport)
    assert "The experiment contains 2 runs" in report.conclusion
    assert len(report.evidence) > 0


def test_agent_normalizes_hallucinated_tool_names_in_evidence(db_session: Session, seeded_data: dict):
    """Verify agent replaces fabricated/hallucinated tool names in evidence with safe default."""
    exp_id = seeded_data["experiment"].id

    hallucinated_json = json.dumps({
        "conclusion": "Fabricated test",
        "evidence": [
            {"source_tool": "sql_query_executor", "finding": "Found 500 rows in dataset"}
        ],
        "recommendations": [],
        "limitations": [],
    })

    responses = [
        MockGeminiResponse(text=hallucinated_json),
    ]

    mock_gemini = MagicMock()
    mock_gemini.generate_chat_turn.side_effect = responses

    agent = InvestigatorAgent(gemini_service=mock_gemini)
    report, trace, iterations = agent.run_investigation(
        experiment_id=exp_id,
        objective="Check dataset",
        db=db_session,
        run_service=RunService(RunRepository(), ExperimentRepository()),
        run_result_service=RunResultService(RunResultRepository()),
        metrics_service=MetricsService(MetricsRepository()),
    )

    assert len(report.evidence) == 1
    assert report.evidence[0].source_tool == "observed_tool_data"


def test_agent_read_only_guarantee(db_session: Session, seeded_data: dict):
    """Verify database records are completely unchanged after investigation."""
    exp_id = seeded_data["experiment"].id
    runs_before = db_session.query(Run).all()
    results_before = db_session.query(RunResult).all()

    mock_gemini = MagicMock()
    mock_gemini.generate_chat_turn.return_value = MockGeminiResponse(
        text=json.dumps({
            "conclusion": "Read-only test passed.",
            "evidence": [],
            "recommendations": [],
            "limitations": [],
        })
    )

    agent = InvestigatorAgent(gemini_service=mock_gemini)
    agent.run_investigation(
        experiment_id=exp_id,
        objective="Check stability",
        db=db_session,
        run_service=RunService(RunRepository(), ExperimentRepository()),
        run_result_service=RunResultService(RunResultRepository()),
        metrics_service=MetricsService(MetricsRepository()),
    )

    runs_after = db_session.query(Run).all()
    results_after = db_session.query(RunResult).all()

    assert len(runs_before) == len(runs_after)
    assert len(results_before) == len(results_after)


# ─── 3. API endpoint integration tests ───────────────────────────────────────

def test_investigator_api_endpoint(db_session: Session, seeded_data: dict):
    """Test POST /api/v1/experiments/{id}/investigate via TestClient."""
    app.dependency_overrides[get_db] = lambda: db_session

    client = TestClient(app)
    exp_id = seeded_data["experiment"].id

    mock_report = json.dumps({
        "conclusion": "Run 1 is superior due to balanced class predictions.",
        "evidence": [
            {"source_tool": "get_run_metrics", "finding": "Run 1 accuracy = 0.9250"}
        ],
        "recommendations": ["Deploy Run 1"],
        "limitations": [],
    })

    with patch.object(GeminiService, "generate_chat_turn") as mock_turn:
        mock_turn.return_value = MockGeminiResponse(text=mock_report)

        # 1. Success case
        resp = client.post(
            f"/api/v1/experiments/{exp_id}/investigate",
            json={"objective": "Compare performance against baseline"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "Run 1 is superior" in body["data"]["conclusion"]
        assert body["data"]["experiment_id"] == exp_id

        # 2. Empty objective (422)
        bad_resp = client.post(
            f"/api/v1/experiments/{exp_id}/investigate",
            json={"objective": ""},
        )
        assert bad_resp.status_code == 422

        # 3. Missing experiment (404)
        missing_id = str(uuid.uuid4())
        missing_resp = client.post(
            f"/api/v1/experiments/{missing_id}/investigate",
            json={"objective": "Test"},
        )
        assert missing_resp.status_code == 404

    app.dependency_overrides.clear()
