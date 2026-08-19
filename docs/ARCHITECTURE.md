# MicroFlow Architecture

This document describes the structural design of MicroFlow.

The architecture enforces strict separation of concerns to guarantee reproducibility and maintainability.

---

# Separation of Concerns

MicroFlow separates

- the platform UI (React)
- the REST API (FastAPI)
- the database (PostgreSQL + pgvector)
- the training logic (Scikit-learn / XGBoost)
- the AI logic (Gemini API)

This separation allows future scaling without redesigning the platform.

---

# High Level Architecture

```
                        React Frontend
                               ",
                               -
                        FastAPI REST API
                               ",
        "O"?"?"?"?"?"?"?"?"?"?"?"?"?"?""?"?"?"?"?"?"?"?"?"?"?"?"?"?""?"?"?"?"?"?"?"?"?"?"?"?"?"?""?"?"?"?"?"?"?"?"?"?"?"?"?"?"?""?"?"?"?"?"?"?"?"?"?"?"?"?"?"?""?"?"?"?"?"?"?"?
        -              -              -              -              -              -
 Dataset Manager Experiment Manager  Run Manager   Artifact Registry  Explainability      AI Suite
                               ",
                               -
                      Training Engine
                               ",
                               -
                      Metrics Engine
                               ",
                               -
                  PostgreSQL Database (+ pgvector)  <------> Google Gemini API
```

---

# Ask MicroFlow / Hybrid RAG Retrieval Flow

The platform provides a zero-hallucination conversational interface.

```
User Question
      ",
Intent Detection
      ",
      "o"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?
      -                               -
Structured Retrieval          Semantic Retrieval
(SQL Repositories)            (pgvector / text-embedding)
      ",                               ",
      """?"?"?"?"?"?"?"?"?"?"?"?"?"?"?""?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"~
                      -
               Context Builder
                      ",
                 Gemini (LLM)
                      ",
        Grounded Answer + Sources Used
```

---

# Layered Architecture

The backend follows a layered architecture.

```
Client
+"
Router Layer
+"
Service Layer
+"
Repository Layer
+"
Database
```

Each layer has exactly one responsibility.

---

# Backend Architecture

```
backend/

app/
"o"?"? ai/              (Gemini integration, caching, RAGAS)
",
"o"?"? api/             (API registration, lifespan)
",
"o"?"? core/            (Config, logging)
",
"o"?"? db/              (Session, base)
",
"o"?"? explainability/  (SHAP, feature importance)
",
"o"?"? models/          (SQLAlchemy models)
",
"o"?"? repositories/    (Database queries)
",
"o"?"? routers/         (HTTP endpoints)
",
"o"?"? schemas/         (Pydantic schemas)
",
"o"?"? services/        (Business logic, AI services)
",
"o"?"? training/        (Model training, evaluation)
",
"o"?"? utils/           (Shared utilities)
",
"""?"? main.py
```

---

## routers/

Responsible only for request validation, response serialization, and HTTP status codes. Routers must never contain business logic.

---

## services/

Contains business logic.

Examples: DatasetService, ExperimentService, RunService, TrainingService, AIQueryService.

Services communicate with repositories. Services never write SQL.

---

## repositories/

Responsible for database access. Only repositories communicate with SQLAlchemy.

---

## training/

Contains machine learning logic. Responsibilities: preprocessing, training, evaluation. Knows nothing about HTTP.

---

## explainability/

Calculates global feature importance using SHAP after a model completes training, outputting visualization artifacts.

---

## ai/

Handles direct interaction with the Google Gemini API, including deterministic caching (SHA-256), resilience patterns (exponential backoff, multi-model fallback), and LLM-as-a-judge evaluation (RAGAS style).

---

# Database Architecture

Primary entities managed by PostgreSQL:

```
Dataset
+"
Experiment (Problem Definition)
+"
Run (Individual Execution)
+"
Artifact
```

*Note on pgvector: Unstructured engineering narratives and cached AI queries are stored with vector embeddings for semantic search.*

---

# Dependency Rules

Allowed:
Router +" Service +" Repository +" Database

Forbidden:
Router +' Database
Router +' SQLAlchemy
Page +' fetch()
Training +' HTTP
Repository +' Service

---

# Request Lifecycle

```
User +" HTTP Request +" Router +" Service +" Repository +" Database +" Service +" Response +" Frontend
```

---

# Training Lifecycle

```
Load Dataset +" Preprocess +" Split Dataset +" Train Model +" Evaluate +" Explainability (SHAP) +" Generate Artifacts +" Store Results
```

*Technical Debt Note: The intended architecture is for this lifecycle to execute asynchronously. The current implementation runs synchronously, blocking the FastAPI worker, and relies on frontend API timeouts.*

---

# Artifact Lifecycle

```
Training Complete +" Generate Files +" Register Artifact +" Store Metadata +" Available for Comparison
```

---

# Error Handling

Every API returns: `success`, `message`, `data`, `errors`.

---

# Scalability Strategy

Current: Single FastAPI instance
Future: Background Workers +" Cloud Storage +" GPU Training

Architecture should support this transition without redesign.

---

# Future Extensions

The architecture allows adding Neural Networks, Feature Stores, Experiment Schedulers, and Cloud Object Storage without changing existing modules.

---

# Architecture Principles

Single Responsibility, Dependency Inversion, Composition over inheritance, Strong typing, Modular services, Stateless APIs, Reproducibility, Extensibility.

---

End of Architecture
