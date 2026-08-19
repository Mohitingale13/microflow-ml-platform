# MicroFlow
## AI Experimentation Platform for Computational Biology Workflows

Version: 1.0
Status: Frozen
Owner: Mohit Ingale

---

# Vision

MicroFlow is a production-grade machine learning experimentation platform designed to simplify the engineering workflows behind computational biology and AI research.

Rather than focusing on biological modeling itself, MicroFlow focuses on the software engineering infrastructure required to build reliable, reproducible and scalable machine learning systems.

The platform enables engineering teams to manage datasets, configure experiments, train models, compare results, track artifacts and maintain reproducible ML pipelines through a unified interface.

The project is inspired by the engineering principles behind modern ML platforms such as MLflow, Weights & Biases and Kubeflow while remaining lightweight enough to demonstrate end-to-end implementation.

---

# Problem Statement

Modern AI teams rarely train just one model.

Instead they continuously iterate over

- datasets
- preprocessing strategies
- feature engineering
- hyperparameters
- model architectures
- evaluation metrics

Without proper tooling, experiments become difficult to reproduce, compare and deploy.

Computational biology introduces an additional challenge:

Large biological datasets often require hundreds of experiments before an acceptable model is discovered.

Engineering teams therefore require infrastructure that enables experimentation instead of manually managing notebooks and CSV files.

MicroFlow addresses this engineering problem.

---

# Goal

Build an internal ML experimentation platform that allows engineering teams to

- upload datasets
- manage datasets
- configure experiments
- launch model training
- compare experiment runs
- register artifacts
- visualize performance
- reproduce previous runs
- leverage AI for experiment strategy, code-reviews, and natural language queries

This project intentionally focuses on engineering infrastructure rather than scientific research.

---

# Target Users

Primary

- ML Engineers
- AI Engineers
- Data Scientists
- Backend Engineers

Secondary

- Computational Biology Teams
- Research Engineers
- Startup Founders

---

# Core Principles

MicroFlow follows six engineering principles.

## 1. Reproducibility

Every run should be reproducible.

No hidden parameters.

Everything should be versioned.

---

## 2. Modularity

Each component should have a single responsibility.

Examples

Dataset Management

Experiment Management

Training Engine

Artifact Registry

Metrics Service

Visualization

AI Engineering Suite

must remain independent modules.

---

## 3. Scalability

Although this MVP runs locally,

the architecture should allow future migration toward

- distributed workers
- cloud storage
- GPU jobs
- Kubernetes

without redesigning the system.

---

## 4. Traceability

Every model must be traceable back to

- dataset
- preprocessing
- hyperparameters
- metrics
- artifacts

---

## 5. Developer Experience

The platform should feel like an internal engineering tool.

Simple.

Fast.

Professional.

---

## 6. Production Mindset

No tutorial code.

No demo code.

Everything should follow production-quality organization.

---

# Project Scope

Included

o. Dataset Upload

o. Dataset Versioning

o. Dataset Preview

o. Experiment Creation

o. Run Tracking

o. Model Training

o. Metrics Calculation

o. Artifact Storage

o. Run Comparison

o. Dashboard

o. Pipeline Visualization

o. Explainability (SHAP)

o. Gemini AI Engineering Suite

---

Excluded

?O Authentication

?O User Accounts

?O Permissions

?O Notifications

?O Billing

?O Cloud Storage

?O Kubernetes

?O Distributed Training

?O Deep Learning

?O Biological Prediction Logic

---

# Functional Modules

## Dataset Manager

Responsibilities

- Upload CSV
- Validate schema
- Preview dataset
- Store metadata
- Dataset versioning

---

## Experiment Manager

Responsibilities

- Define the objective of an ML problem.
- Associate a dataset.
- Define default training configuration.
- Maintain experiment metadata.
- Group multiple runs under a single experiment.

## Run Manager

Responsibilities

- Execute one training run.
- Override experiment configuration.
- Track run status.
- Store metrics.
- Generate artifacts.
- Record execution timestamps.

Status

Queued

Running

Completed

Failed

---

## Training Engine

Responsibilities

- Load dataset
- Execute preprocessing
- Train model
- Evaluate model
- Store metrics

Initial Supported Models

- Logistic Regression
- Random Forest
- XGBoost

---

## Explainability Layer

Responsibilities

- Generate Global Feature Importance (SHAP)
- Output SHAP Summary plots and dependencies
- Run automatically post-training for tree and linear models

---

## AI Engineering Suite

Responsibilities

- **Ask MicroFlow (Hybrid RAG)**: Allow natural language querying over telemetry, experiments, and runs. Uses structured telemetry data + unstructured pgvector semantic retrieval.
- **AI Strategy**: Provide evidence-driven experiment recommendations.
- **AI Dataset Intelligence**: Automated dataset analysis and insights.
- **AI Run Review & Comparison**: On-demand peer reviews and deep comparisons of model runs.
- **Resilience**: Exponential backoff, multi-model fallback, deterministic SHA-256 caching.
- **Evaluation**: RAGAS-based LLM-as-a-judge (Context Relevance, Faithfulness, Answer Relevance).

---

## Artifact Registry

Stores every artifact generated by a run.

Examples

- trained model
- metrics.json
- feature importance
- confusion matrix
- ROC curve
- preprocessing pipeline
- training configuration

Artifacts are immutable.

---

## Metrics Engine

Responsible for calculating

- Accuracy
- Precision
- Recall
- F1 Score
- ROC AUC

Future metrics can be added without changing other modules.

---

## Dashboard

Displays

Datasets

Experiments

Training Status

Recent Runs

Performance Metrics

Artifact Count

---

## Pipeline Viewer

Visual representation of

Dataset

+"

Preprocessing

+"

Training

+"

Evaluation

+"

Explainability (SHAP)

+"

Artifacts

---

# Non Functional Requirements

Performance

Dataset upload under 3 seconds for medium datasets.

Training should execute asynchronously. (Note: Intended architecture. See Technical Debt).

Backend responses below 300ms where applicable.

---

Maintainability

Strict modular architecture.

Typed interfaces.

Reusable services.

---

Reliability

Graceful error handling.

Validation on every API.

Centralized logging.

---

Extensibility

Adding a new ML model should require changes only inside the Training Engine.

Adding a new metric should require changes only inside Metrics Engine.

---

# Technology Stack

Frontend

React

TypeScript

TailwindCSS

TanStack Query

React Router

Backend

FastAPI

SQLAlchemy

Pydantic

Database

PostgreSQL + pgvector

Machine Learning

Scikit-learn

XGBoost

SHAP

Visualization

Plotly

AI

Google Gemini 3.6 Flash (with Multi-model Fallback)

Deployment

Docker

---

# Technical Debt

These known issues reflect areas where the current code deviates from intended specifications:

- **Synchronous Training Execution:** The `training_service.execute()` method currently blocks the FastAPI thread synchronously. While the specification intends for asynchronous training, the current implementation relies on a hardcoded 2-minute API timeout from the frontend as a workaround.
- **AI Evaluation Retry Loop:** The `ai_evaluation_service.py` batch processor swallows Gemini API exceptions without marking queries as `failed`, potentially leading to an infinite retry loop on poison pill queries.
- **Lack of Schema Migrations:** Initialization uses `Base.metadata.create_all`. A proper migration tool (like Alembic) is needed.

---

# Coding Standards

Python

- Type hints everywhere
- Dependency Injection where appropriate
- Service Layer architecture
- No business logic inside routers

Frontend

- Functional Components
- Custom Hooks
- Strong TypeScript
- API abstraction layer
- Reusable UI components

Database

- UUID primary keys
- Created timestamps
- Updated timestamps
- Soft delete support where appropriate

---

# Folder Philosophy

Every folder must own exactly one responsibility.

No circular dependencies.

No shared global state.

Business logic belongs only inside services.

---

# AI Development Rules

Every AI implementation must follow these rules.

1.

Read this document before generating code.

2.

Do not redesign architecture.

3.

Do not rename modules.

4.

Do not introduce new frameworks.

5.

Implement only the requested phase.

6.

Do not generate placeholder implementations.

7.

Every phase must compile successfully.

8.

Follow existing project conventions.

---

# Definition of Success

A successful implementation should demonstrate the engineering infrastructure behind modern machine learning systems.

Someone reviewing the repository should immediately understand that the focus of the project is reproducible ML engineering rather than machine learning algorithms themselves.

The project should resemble an internal engineering platform rather than a tutorial application.

---

End of Specification
