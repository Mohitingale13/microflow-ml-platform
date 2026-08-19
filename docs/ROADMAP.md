# MicroFlow Development Roadmap

Version: 1.0

Status: Frozen

---

# Overview

This roadmap defines the implementation order for MicroFlow.

Each milestone is independently testable and deployable.
Every milestone ends with a working application.

AI agents must implement only one milestone at a time.

---

# Completed Milestones

## Milestone 0: Foundation
**Objective:** Establish a production-ready project foundation.
**Deliverables:** Monorepo, React, FastAPI, PostgreSQL, Docker, Base Layout.

## Milestone 1: Dataset Management
**Objective:** Build the complete dataset lifecycle.
**Deliverables:** CSV Upload, Validation, Metadata Storage, Preview.

## Milestone 2: Experiment & Run Management
**Objective:** Allow engineers to define ML experiments and execute multiple reproducible runs under each experiment.
**Deliverables:** Experiment Creation, Parameter Config, Status Tracking.

## Milestone 3: Training Engine
**Objective:** Build the ML execution layer.
**Deliverables:** Dataset Loader, Preprocessing, Train/Test Split, Random Forest, XGBoost, Logistic Regression.

## Milestone 4: Metrics Engine
**Objective:** Generate reproducible experiment metrics.
**Deliverables:** Accuracy, Precision, Recall, F1, ROC, Confusion Matrix, Feature Importance.

## Milestone 5: Artifact Registry
**Objective:** Track every output generated during experiments.
**Deliverables:** Model Storage, Metrics JSON, ROC Image, Feature Importance, Training Config.

## Milestone 6: Dashboard
**Objective:** Provide a unified engineering overview.
**Deliverables:** Statistics, Recent Experiments, Training Status.

## Milestone 7: Experiment Comparison
**Objective:** Compare multiple experiments.
**Deliverables:** Comparison Table, Metric Comparison, Charts.

## Milestone 8: Pipeline Visualization
**Objective:** Visualize ML workflow.
**Deliverables:** Pipeline Graph, Dataset Flow, Training Flow.

## Milestone 9: Polish & AI Integration
**Objective:** Prepare project for production showcase and integrate LLMs.
**Deliverables:** Gemini AI Engineering Suite (Hybrid RAG, Run Review, Dataset Intel), SHAP Explainability, Documentation, Demo.

---

# Known Technical Debt (To Be Addressed)

These issues exist in the current codebase and should be fixed in upcoming refactoring cycles:

- **Synchronous Training Execution:** Model training blocks the FastAPI thread synchronously. This needs to be migrated to asynchronous background tasks to prevent timeouts on large datasets.
- **AI Evaluation Retry Loop:** The `ai_evaluation_service.py` batch processor swallows Gemini API exceptions without marking queries as `failed`, risking infinite retry loops on poison pill queries.
- **Database Migrations:** The project relies on `Base.metadata.create_all` for database initialization. Alembic must be introduced to manage future schema changes.

---

# Testing Strategy

Every milestone must include Unit Testing, Manual Testing, API Testing, UI Testing, Regression Testing.

---

# Code Review Checklist

Before every commit: Project builds, No warnings, No unused code, Strong typing, Clean folder structure.

---

# AI Agent Rules

Before starting any milestone:
Read PROJECT_SPEC.md, ARCHITECTURE.md, ROADMAP.md
Do not modify architecture unless explicitly requested.
Only complete the requested milestone.

---

# Definition of Project Completion

MicroFlow is complete when: Datasets can be uploaded, Experiments can be created, Models can be trained, Metrics can be evaluated, Artifacts can be stored, Experiments can be compared, AI can provide engineering assistance, and Project is fully documented.

---

End of Roadmap
