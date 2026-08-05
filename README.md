<div align="center">

# MicroFlow

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6?style=flat&logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-AI_Engine-4285F4?style=flat&logo=google&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat&logo=docker&logoColor=white)
<br>
![Vercel](https://img.shields.io/badge/Vercel-Frontend_Deployed-000000?style=flat&logo=vercel&logoColor=white)
![Render](https://img.shields.io/badge/Render-Backend_Deployed-46E3B7?style=flat&logo=render&logoColor=white)
![Neon](https://img.shields.io/badge/Neon-Database_Live-00E599?style=flat&logo=neon&logoColor=white)
![MIT License](https://img.shields.io/badge/License-MIT-green.svg)
![Tests](https://img.shields.io/badge/Tests-264%2B%20Passing-success)
![Version](https://img.shields.io/badge/Version-1.0.0-blueviolet)

<br>

<h3><a href="https://microflow-ml-platform.vercel.app">🌟 View Live Demo: microflow-ml-platform.vercel.app 🌟</a></h3>

</div>

![Demo Video](images/demo_video.webp)

**A full-stack ML experimentation and observability platform with an integrated AI engineering co-pilot.**

### Platform Features
- ✔ Dataset Management with AI Insights
- ✔ Experiment Tracking with AI Strategy Co-Pilot
- ✔ Run Tracking with AI Peer Review & Comparison
- ✔ Ask MicroFlow — Natural Language Query Assistant
- ✔ Training Engine (Random Forest, XGBoost, Logistic Regression)
- ✔ Paginated Artifact Registry (50 items/page, sorted by latest)
- ✔ Metrics Dashboard
- ✔ Pipeline Visualization & Lineage Graph
- ✔ Interactive Engineering Dashboard
- ✔ Platform Health Monitor

---

## Overview

Running one model once is easy. Running hundreds of experiments over several datasets, comparing results across model configurations, and reproducing a specific run six months later — that is the actual problem.

MicroFlow is a full-stack ML platform designed to solve exactly that. It handles the infrastructure layer of machine learning: dataset versioning, experiment definition, run tracking, artifact persistence, and metrics aggregation — all backed by an AI engineering co-pilot powered by Google Gemini that operates strictly on authentic experiment telemetry without hallucination.

The platform is aimed at ML engineers, data scientists, and research engineers who need an organised, auditable, and AI-assisted workflow.

---

## Highlights
- ✔ Full-stack ML platform — FastAPI + React + PostgreSQL
- ✔ 264+ automated backend tests, all passing
- ✔ Dockerized, three-container deployment (Nginx + FastAPI + PostgreSQL)
- ✔ Complete AI Engineering Suite powered by Google Gemini 1.5 Flash
- ✔ Automatic exponential backoff & multi-model fallback for AI resilience
- ✔ SHA-256 deterministic caching for all AI responses
- ✔ Paginated Artifact Registry with latest-first ordering
- ✔ Uniform refresh UX with 500 ms minimum spinner + confirmation badge
- ✔ Interactive Metrics Dashboard & Pipeline Visualization

---

## Screenshots

### Dashboard
![Dashboard](images/dashboard.png)

### Ask MicroFlow — Natural Language Assistant
![Assistant](images/assistant.png)

### Training Runs
![Training Page](images/training.png)

### Artifact Registry (Paginated)
![Artifact Registry](images/artifacts.png)

### AI Strategy Co-Pilot (per Experiment)
![AI Strategy](images/ai_strategy.png)

### Pipeline Visualization
![Pipeline Flow Graph](images/pipeline_flow_graph.png)
![Pipeline Timeline](images/pipeline_timeline.png)
![Pipeline Lineage](images/pipeline.png)

### Metrics Dashboard
![Metrics Dashboard](images/metrics.png)

---

## Why I built this

Modern ML projects quickly become difficult to reproduce as datasets, models, configurations, and evaluation results grow. MicroFlow was built to explore how an experiment tracking platform can be engineered from scratch using a clean layered architecture, and to answer: *what does it look like when AI is integrated not as a chatbot wrapper but as a grounded, zero-hallucination engineering co-pilot operating strictly on authenticated telemetry?*

---

## Why MicroFlow?

When ML projects move beyond a single experiment, three problems surface reliably:

**You lose track of what you ran.** Without a structured system, experiments accumulate in notebooks. Parameters get changed and forgotten. Results become disconnected from the code that produced them.

**You can't reproduce results.** If the preprocessing pipeline isn't captured alongside the model, retraining on the same data produces a different result. MicroFlow snapshots training configuration and preprocessing metadata with every run.

**Comparison becomes manual work.** Comparing five model configurations across two datasets requires a proper query layer, not a spreadsheet. MicroFlow's Metrics Dashboard provides aggregated, queryable analytics across all runs.

---

## Deployment Architecture

```mermaid
graph TD
    Browser[Browser]
    Nginx[Nginx]
    FastAPI[FastAPI]
    Gemini[Google Gemini API]
    PostgreSQL[(PostgreSQL)]
    Storage[(Local Storage)]

    Browser -->|HTTP| Nginx
    Nginx -->|Proxy| FastAPI
    FastAPI -->|SQLAlchemy| PostgreSQL
    FastAPI -->|Read/Write Artifacts| Storage
    FastAPI -->|AI Requests| Gemini
```

---

## Key Features

### Dataset Management
- Upload CSV datasets through the UI or API
- Automatic schema analysis: row count, column count, data types, missing value detection
- Dataset preview (first N rows) and per-column statistics
- SHA-256 deduplication — the same file will not be stored twice
- Datasets are versioned and protected from deletion if experiments depend on them
- **AI Insights tab** — automated pre-training dataset intelligence (see AI section below)

### Experiment Management
- Experiments define the ML problem: name, objective, linked dataset, and default training configuration
- Multiple runs can be grouped under a single experiment
- Experiment status lifecycle: `draft → active → archived`
- Per-experiment analytics showing best run, accuracy range, and model breakdown
- **AI Strategy tab** — live ML co-pilot generating evidence-driven next-experiment recommendations

### Run Management
- Each run is an individual training execution with its own model type and hyperparameter overrides
- Run status lifecycle: `draft → queued → running → completed / failed`
- Full audit trail: created timestamp, started timestamp, completed timestamp, execution duration
- Run notes and configuration stored as a snapshot for reproducibility
- **AI Run Review** — on-demand peer review generated for any completed run
- **AI Run Comparison** — deep side-by-side analysis of any two runs within an experiment

### AI Engineering Suite (Google Gemini)

All five AI capabilities share a common architecture: **zero hallucination by design**. Gemini never writes SQL, never accesses PostgreSQL directly, and only reasons over structured data objects fetched by the secure repository layer. Every response is cached with a SHA-256 deterministic key.

#### AI Resilience Layer
- Automatic **exponential backoff** with two retry attempts (1.5 s → 3 s) on 503/429 errors
- **Multi-model fallback** chain: `gemini-1.5-flash` → `gemini-1.5-flash-8b` → `gemini-1.0-pro`
- Errors are surfaced to the frontend with full API status context

#### 1. Ask MicroFlow (Natural Language Assistant)
Query your experiment telemetry in plain English from a dedicated assistant page:
- *"Which experiment has the best accuracy?"*
- *"Why did run 4 fail?"*
- *"Compare all XGBoost models"*

Every response delivers four structured fields:
| Field | Description |
|---|---|
| **Analysis & Findings** | The direct, engineering-grade answer |
| **Reasoning** | How the AI reached its conclusion |
| **Telemetry Evidence** | The raw experiment data backing the answer |
| **Suggested Next Step** | The single recommended action to take |

Session context carries forward across queries within the same page visit.

#### 2. AI Experiment Strategy
Integrated as a `✨ AI Strategy` tab inside each experiment. Operates as an authoritative ML co-pilot:
- Synthesizes dataset quality metrics, metric variance, chronological run trajectories, speed comparisons, and parameter space coverage
- Maps unexplored model families and unvisited hyperparameter regions
- Identifies metric saturation and plateau conditions
- Recommends the single best next experiment with concrete algorithm families and parameter bounds

#### 3. AI Dataset Intelligence
Integrated as a `✨ AI Insights` tab inside each dataset. Runs automated pre-training auditing:
- Deterministic quality score (0–100) grounded in actual missing value ratios, volume adequacy, and feature completeness
- Optimal target variable and feature suggestions from column schema analysis
- Algorithm suitability ratings (Random Forest, XGBoost, Logistic Regression)
- Step-by-step preprocessing roadmap

#### 4. AI Run Review
On-demand peer review for any completed run:
- Overall assessment, identified strengths and weaknesses
- Comparison against the current best run in the experiment
- Concrete next steps for improving performance

#### 5. AI Run Comparison
Deep analysis comparing any two completed runs within an experiment:
- Configuration attribution — which hyperparameter changes drove metric differences
- Explicit trade-off analysis (accuracy vs. speed vs. generalization)
- Actionable improvement strategies with specific parameter suggestions

### Training Engine
- Supports three model families: **Random Forest**, **Logistic Regression**, **XGBoost**
- Preprocessing pipeline: missing value imputation (median/mode), one-hot encoding, stratified train/test split
- Model Factory pattern — adding a new estimator requires changes in one file only
- All training logic is HTTP-free; the engine communicates through plain Python interfaces

### Artifact Registry
- Every completed run generates six artifact files automatically:
  - Trained model (serialised)
  - Metrics JSON, Evaluation JSON, Confusion Matrix JSON
  - Preprocessing Summary JSON, Training Configuration Snapshot JSON
- **Paginated display**: 50 artifacts per page, sorted latest-first, with Previous/Next controls
- SHA-256 checksum stored with every artifact for integrity verification
- Artifacts can be downloaded directly from the UI or API

### Metrics Dashboard
- System-wide overview: total runs, success rate, average accuracy, average F1, average ROC AUC
- Model leaderboard: best accuracy and average accuracy grouped by model family
- Experiment performance table: best run, accuracy range, model breakdown per experiment
- Dataset performance analytics: which datasets produce the best models
- Side-by-side run comparison: select any N runs and compare configurations and metrics

### Pipeline Visualization
- Per-run execution graph showing all eight pipeline stages
- Each node shows status, timestamps, and duration
- Chronological timeline view for a selected run
- Global lineage view: Dataset → Experiments → Runs → Artifacts, rendered as a collapsible tree

### Engineering Dashboard
- Platform-wide overview: 8 live stat cards
- Recent activity feed showing the last 5 platform events across all modules
- Recent runs table with status badges, model labels, accuracy, and clickable links
- Best performing assets: best model family, best experiment, most-used dataset, latest artifact
- **Platform Health Monitor** — live service status with version indicator (v1.0.0)

### UX & Reliability
- **Uniform refresh UX**: all refresh buttons across the platform feature a 500 ms minimum spinner and an emerald "Updated!" / "Checked!" confirmation badge
- **Spacious count bars**: all "Showing X of Y" result count bars use structured flex layouts with clean spacing between words and numbers
- **Developer-first copy**: concise, engineering-grade UI language throughout (no chatbot filler text)
- **Mobile-first layouts**: all changes are responsive and mobile-compatible

---

## System Architecture

```mermaid
graph TD
    Browser["React Frontend\n(TypeScript, TanStack Query)"]
    API["FastAPI REST API\n/api/v1"]
    Routers["Router Layer\n(Request validation, response serialisation)"]
    Services["Service Layer\n(Business logic)"]
    Repos["Repository Layer\n(SQLAlchemy ORM)"]
    DB["PostgreSQL"]
    Storage["Local File Storage\n/storage"]
    Training["Training Engine\n(scikit-learn, XGBoost)"]
    AILayer["AI Layer\n(GeminiService, PromptBuilder, ResponseParser)"]
    Gemini["Google Gemini API\n(gemini-1.5-flash + fallback chain)"]

    Browser -->|HTTP/JSON| API
    API --> Routers
    Routers --> Services
    Services --> Repos
    Services --> Training
    Services --> AILayer
    Repos --> DB
    Training --> Storage
    Repos --> Storage
    AILayer --> Gemini
```

Each layer has exactly one responsibility. Routers never touch the database. Services never call HTTP directly. Repositories never contain business logic. The training engine has no knowledge of FastAPI or SQLAlchemy. The AI layer never writes SQL or accesses the database — it only receives pre-fetched, structured data objects.

---

## ML Workflow

```mermaid
graph TD
    D["Upload Dataset\n(CSV, validated on upload)"]
    AI_D["AI Insights\n(quality score, feature suggestions)"]
    E["Create Experiment\n(define objective, link dataset)"]
    AI_E["AI Strategy\n(evidence-driven next-experiment plan)"]
    R["Create Run\n(select model, set hyperparameters)"]
    T["Execute Training\n(POST /runs/{run_id}/execute)"]
    P["Preprocessing\n(impute, encode, split)"]
    M["Train & Evaluate\n(accuracy, precision, recall, F1, ROC AUC)"]
    AI_R["AI Run Review\n(peer review + comparison)"]
    A["Artifact Generation\n(model, metrics, config snapshots)"]
    DB["Persist Results\n(RunResult + Artifacts in PostgreSQL)"]
    Dash["View on Dashboard\n(Metrics, Pipeline, Artifacts, Ask MicroFlow)"]

    D --> AI_D --> E --> AI_E --> R --> T --> P --> M --> AI_R --> A --> DB --> Dash
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite |
| **Styling** | Tailwind CSS v4 |
| **Data Fetching** | TanStack Query (React Query) |
| **Routing** | React Router v6 |
| **Charts** | Recharts |
| **Backend** | FastAPI, Python 3.11 |
| **ORM** | SQLAlchemy 2.0 (mapped columns) |
| **Validation** | Pydantic v2 |
| **Database** | PostgreSQL 16 |
| **AI Engine** | Google Gemini 1.5 Flash (with fallback chain) |
| **ML** | scikit-learn, XGBoost, pandas, NumPy |
| **Infrastructure** | Docker, Docker Compose, Nginx |
| **Testing** | pytest, SQLite in-memory (StaticPool) |

---

## Project Structure

```
MicroFlow/
├── backend/
│   ├── app/
│   │   ├── ai/             # AI layer: GeminiService, PromptBuilder, ResponseParser
│   │   ├── api/            # Router registration
│   │   ├── core/           # Config, logging
│   │   ├── db/             # Session management, base model
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── repositories/   # Database access layer (incl. AI cache repos)
│   │   ├── routers/        # FastAPI route handlers
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/       # Business logic (incl. AI services)
│   │   ├── training/       # ML pipeline (loader, preprocessor, factory, trainer, evaluator)
│   │   └── main.py
│   ├── tests/
│   │   ├── services/       # Service unit tests
│   │   ├── training/       # Training engine unit tests
│   │   ├── test_ai_review.py
│   │   ├── test_ai_dataset_insights.py
│   │   ├── test_run_comparison.py
│   │   ├── test_dashboard.py
│   │   ├── test_metrics.py
│   │   └── test_pipeline.py
│   └── alembic/            # Database migrations
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ai/         # AIReviewCard
│       │   ├── dashboard/  # PlatformHealth, RecentRuns, etc.
│       │   ├── datasets/   # AIInsightsTab, PreviewTable
│       │   └── experiments/# AIStrategyTab, CompareRunsDialog
│       ├── hooks/          # TanStack Query hooks
│       ├── layouts/        # AppLayout, Sidebar, Navbar
│       ├── pages/          # One page per feature
│       ├── services/       # API client functions
│       ├── types/          # TypeScript interfaces
│       └── utils/          # Shared helpers
├── docker/
│   └── postgres/           # DB init scripts
├── docs/
│   ├── PROJECT_SPEC.md
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── images/                 # README screenshots
├── storage/                # Artifact file storage (volume-mounted)
└── docker-compose.yml
```

---

## Core Modules

### Dataset Management
Handles CSV ingestion and analysis. On upload, the service reads the file, computes a SHA-256 hash to prevent duplicates, parses column names and data types, and records row count, column count, and per-column missing value percentages. The file is stored on disk and metadata is persisted in PostgreSQL. A preview endpoint returns the first 50 rows. A statistics endpoint returns per-column descriptive statistics. The AI Insights tab delivers a zero-hallucination quality audit grounded entirely in authentic schema metadata.

### Experiment Management
Experiments sit between datasets and runs. An experiment defines the ML problem: what dataset to use, what the objective is, and what the default training configuration looks like. Multiple runs can be created under one experiment with different model types or hyperparameter overrides. The AI Strategy tab surfaces an evidence-driven co-pilot that synthesizes run history, metric variance, and parameter space coverage into a single, actionable next-experiment recommendation.

### Run Management
A run is a single training execution. It carries its own model type, hyperparameter overrides (stored as JSON), and status. The status transitions (`draft → queued → running → completed/failed`) are enforced by the service layer. Nothing in the run record is mutable after execution. AI Run Review generates a structured peer review for completed runs; AI Run Comparison performs deep side-by-side attribution analysis for any two runs in the same experiment.

### AI Layer (`backend/app/ai/`)
Three files, each with a single job:
- **`gemini_service.py`** — wraps the Google Generative AI SDK with exponential backoff retry logic (1.5 s, 3 s) and a three-model fallback chain (`gemini-1.5-flash` → `gemini-1.5-flash-8b` → `gemini-1.0-pro`). Raises a descriptive `HTTPException` with full API status on exhaustion.
- **`prompt_builder.py`** — constructs fully grounded prompts from pre-fetched repository data. Never constructs SQL. Never invents values. All numeric fields are drawn directly from `RunResult` objects.
- **`response_parser.py`** — strips markdown fences, extracts embedded JSON, validates required fields, and raises `ValueError` on malformed responses.

The AI services (`AIReviewService`, `AIDatasetInsightsService`, `RunComparisonService`, `AssistantService`) implement a **SHA-256 deterministic cache** — identical inputs always produce a cache hit without redundant Gemini API calls.

### Training Engine
Five isolated files, each with a single job:
- **loader.py** — reads a CSV from disk into a pandas DataFrame
- **preprocessing.py** — imputes missing values, one-hot encodes categoricals, performs a stratified train/test split
- **model_factory.py** — maps a model type string to a configured scikit-learn or XGBoost estimator
- **trainer.py** — calls `fit()` and returns the trained estimator
- **evaluation.py** — computes accuracy, precision, recall, F1, ROC AUC, and confusion matrix

### Artifact Registry
Every completed run automatically produces six artifact files. The `ArtifactService` writes each file to disk, computes its SHA-256 checksum, records file size and MIME type, and persists the metadata in the `artifacts` table. The registry UI displays 50 artifacts per page sorted latest-first with Previous/Next pagination controls.

### Metrics Dashboard
A read-only analytics layer that runs SQL aggregations over persisted `RunResult` records. It does not recompute metrics — it reads what was stored during training.

### Pipeline Visualization
A read-only module that reconstructs the execution graph for any run. It queries the `Run`, `RunResult`, and `Artifact` tables and maps the data onto an eight-stage pipeline representation. The lineage view walks the full Dataset → Experiment → Run → Artifact hierarchy.

### Engineering Dashboard
An aggregation layer with four dedicated endpoints that pull data from existing repositories without duplicating SQL logic. The Platform Health endpoint reports live service status and the platform version (v1.0.0).

---

## API Overview

All endpoints are prefixed with `/api/v1`.

### Datasets
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/datasets` | List all datasets |
| `POST` | `/datasets` | Upload a CSV dataset |
| `GET` | `/datasets/{id}` | Dataset metadata |
| `GET` | `/datasets/{id}/preview` | First 50 rows |
| `GET` | `/datasets/{id}/statistics` | Per-column statistics |
| `DELETE` | `/datasets/{id}` | Delete dataset (blocked if experiments exist) |
| `POST` | `/datasets/{id}/ai-insights` | Generate AI dataset quality audit |

### Experiments & Runs
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/experiments` | List all experiments |
| `POST` | `/experiments` | Create experiment |
| `GET` | `/experiments/{id}` | Experiment detail |
| `GET` | `/runs` | List all runs |
| `POST` | `/runs` | Create run |
| `GET` | `/runs/{id}` | Run detail |
| `POST` | `/runs/{id}/execute` | Execute training for a queued run |
| `GET` | `/runs/{id}/result` | Persisted evaluation metrics |
| `GET` | `/runs/{id}/artifacts` | Artifacts generated by a run |
| `POST` | `/runs/{id}/ai-review` | Generate AI peer review |
| `GET` | `/runs/compare` | AI deep comparison of two runs |

### Artifacts
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/artifacts` | List all artifacts |
| `GET` | `/artifacts/stats` | Registry statistics |
| `GET` | `/artifacts/{id}` | Artifact metadata |
| `GET` | `/artifacts/{id}/download` | Download artifact file |

### AI Assistant
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/assistant/query` | Natural language query against experiment telemetry |
| `GET` | `/assistant/recent` | Recent platform-wide questions and answers |

### Metrics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/metrics/overview` | System-wide aggregated metrics |
| `GET` | `/metrics/models` | Model leaderboard |
| `GET` | `/metrics/experiments` | Experiment performance analytics |
| `GET` | `/metrics/datasets` | Dataset performance analytics |
| `GET` | `/metrics/runs/compare` | Side-by-side run comparison |

### Pipeline
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/pipeline/overview` | Global execution statistics |
| `GET` | `/pipeline/runs` | All runs with filters |
| `GET` | `/pipeline/lineage` | Full Dataset → Artifacts lineage tree |
| `GET` | `/pipeline/{run_id}` | Execution graph and timeline for a run |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/dashboard/overview` | Platform-wide stat summary |
| `GET` | `/dashboard/activity` | Unified recent activity feed |
| `GET` | `/dashboard/recent-runs` | Last N runs with context |
| `GET` | `/dashboard/quick-stats` | Best model, experiment, dataset, artifact |
| `GET` | `/health` | Platform health and version (v1.0.0) |

---

## Database Design

Five core tables. Every primary key is a UUID string. Every table carries `created_at` and `updated_at` timestamps.

```mermaid
erDiagram
    DATASETS {
        string id PK
        string name
        string original_filename
        string file_hash UK
        int file_size_bytes
        int row_count
        int column_count
        json column_names
        json dtypes
        json missing_values
        string status
        string storage_path
        datetime created_at
    }

    EXPERIMENTS {
        string id PK
        string name
        string dataset_id FK
        string objective
        json default_configuration
        json tags
        string status
        datetime created_at
        datetime updated_at
    }

    RUNS {
        string id PK
        string experiment_id FK
        int run_number
        string model_type
        json training_configuration
        string status
        string notes
        datetime created_at
        datetime updated_at
    }

    RUN_RESULTS {
        string id PK
        string run_id FK
        float accuracy
        float precision
        float recall
        float f1_score
        float roc_auc
        json confusion_matrix
        float execution_time_seconds
        datetime started_at
        datetime completed_at
        string model_type
        string dataset_id
        json training_config_snapshot
        json preprocessing_summary
    }

    ARTIFACTS {
        string id PK
        string run_id FK
        string experiment_id
        string dataset_id
        string artifact_type
        string filename
        string mime_type
        string storage_path
        int file_size_bytes
        string sha256_checksum
        datetime created_at
    }

    AI_REVIEW_CACHE {
        string id PK
        string run_id FK
        string prompt_hash UK
        string answer
        string reasoning
        string supporting_data
        string recommendation
        string confidence
        datetime generated_at
    }

    DATASETS ||--o{ EXPERIMENTS : "used by"
    EXPERIMENTS ||--o{ RUNS : "contains"
    RUNS ||--o| RUN_RESULTS : "produces"
    RUNS ||--o{ ARTIFACTS : "generates"
    RUNS ||--o{ AI_REVIEW_CACHE : "cached by"
```

---

## Training Pipeline

When `POST /api/v1/runs/{run_id}/execute` is called, the `TrainingService` orchestrates the following sequence:

1. **Validate** — confirm the run exists and its status is `queued`. Reject anything else with HTTP 422.
2. **Transition** — set run status to `running`, persist the timestamp.
3. **Load** — `loader.py` reads the CSV from disk into a pandas DataFrame. File not found raises immediately, marking the run as `failed`.
4. **Preprocess** — `preprocessing.py` validates the target column, imputes missing values, one-hot encodes categoricals, and performs a stratified 80/20 train/test split.
5. **Build estimator** — `model_factory.py` maps the run's `model_type` to a configured estimator. Unknown types fall back to Random Forest.
6. **Train** — `trainer.py` calls `estimator.fit(X_train, y_train)`.
7. **Evaluate** — `evaluation.py` computes accuracy, precision, recall, F1, confusion matrix, and ROC AUC.
8. **Persist result** — a `RunResult` record is written with all numeric metrics, timestamps, and configuration snapshot.
9. **Generate artifacts** — six files are written to `/storage/{experiment_id}/{run_id}/`. Each is registered with its SHA-256 checksum.
10. **Transition** — run status moves to `completed`. On any exception in steps 3-9, status moves to `failed`.

---

## Running Locally

### Requirements

- Docker and Docker Compose
- A Google Gemini API key (for AI features)
- No local Python or Node.js installation required

### Start with Docker Compose

```bash
git clone https://github.com/Mohitingale13/microflow-ml-platform.git
cd microflow-ml-platform
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

### Environment Variables

Copy `.env.example` to `.env` and configure:

```
POSTGRES_USER=microflow
POSTGRES_PASSWORD=microflow_secret
POSTGRES_DB=microflow
LOG_LEVEL=INFO
ENVIRONMENT=development
GEMINI_API_KEY=your_google_gemini_api_key_here
```

> The `GEMINI_API_KEY` is required for all AI features (Ask MicroFlow, AI Strategy, AI Insights, AI Run Review, AI Run Comparison). Without it, AI endpoints will return a descriptive 503 error while all other platform features remain fully functional.

### Running Tests

```bash
docker compose exec backend pytest -v
```

The test suite uses SQLite in-memory databases with SQLAlchemy's `StaticPool` — no external PostgreSQL connection required. **264 tests** currently pass across all modules.

### Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
GEMINI_API_KEY=your_key uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Engineering Decisions

**Repository Pattern**
Every database table has a dedicated repository class. Services call repositories; they never write SQLAlchemy queries directly. This makes services testable in isolation by substituting a mock repository without touching a database.

**Service Layer**
All business logic lives in services. Routers handle HTTP concerns only. The AI services follow the same pattern — they receive pre-fetched data objects from the repository layer and pass structured prompts to the AI layer.

**AI Zero-Hallucination Architecture**
Gemini is never given access to the database. The `AssistantService` fetches all relevant data through authenticated repository methods, injects it as structured context into the prompt, and asks Gemini to reason over it. There is no SQL generation, no tool calling, and no external data access. Every claim Gemini makes is traceable to a specific database record fetched before the prompt was constructed.

**AI Deterministic Caching**
All AI responses are cached by a SHA-256 hash of the input prompt. Identical queries (same run, same data state) return instantly from the cache without calling Gemini. The cache is persisted in PostgreSQL so it survives restarts.

**AI Resilience Layer**
The `GeminiService` wraps every API call with exponential backoff retry logic (1.5 s → 3 s) and a three-model fallback chain. If the primary model (`gemini-1.5-flash`) returns 503 or 429, the service automatically retries with `gemini-1.5-flash-8b`, then `gemini-1.0-pro`, before raising an `HTTPException` with the full API error context.

**Run vs Experiment separation**
An experiment defines the problem. A run is one attempt at solving it. This separation allows multiple model configurations and hyperparameter sweeps to be grouped meaningfully under a single experiment.

**Artifact persistence**
Artifacts are written to disk as real files and registered in the database with checksums. This means they can be downloaded, re-used, and verified for integrity independently of the application.

**Why metrics are persisted**
Metrics are stored in `RunResult` as typed database columns, not as JSON blobs. This allows the metrics repository to run SQL aggregations without deserialising data in application code.

**Why Docker**
The project runs as three containers: PostgreSQL, the FastAPI backend, and a Nginx-served React frontend. Docker Compose with health checks ensures services start in the correct order.

**Why TanStack Query**
All server state on the frontend is managed by TanStack Query. This provides automatic caching, background refetching, and a clean separation between server state and local UI state.

---

## Future Improvements

- **Authentication and multi-user support** — JWT-based auth with role-based access control
- **Background training jobs** — move to a task queue (Celery, ARQ) for async training with real-time status polling
- **Cloud object storage** — swap artifact storage backend for S3-compatible storage (requires only `ArtifactService` changes)
- **Additional model families** — the Model Factory accepts new estimators by adding a single builder function
- **Experiment scheduling** — queue a batch of runs with different hyperparameter combinations (grid search, random search)
- **Streaming AI responses** — stream Gemini tokens to the frontend for a real-time reasoning experience
- **AI-powered anomaly detection** — proactively flag metric regressions or unexpected training behaviour across runs

---

## Contributing

Issues and pull requests are welcome.

**Before opening a PR:**
- Run `pytest -v` and ensure all tests pass
- Follow the existing layer conventions: routers call services, services call repositories
- Do not add business logic to routers
- Do not add HTTP calls to the training engine
- Do not add database access to the AI layer — pass pre-fetched data objects
- Add tests for any new service or repository method

---

## License

MIT

---

## Acknowledgements

Inspired by the engineering principles behind [MLflow](https://mlflow.org), [Weights & Biases](https://wandb.ai), and [Kubeflow](https://kubeflow.org). AI powered by [Google Gemini](https://deepmind.google/technologies/gemini/). MicroFlow is not affiliated with any of these projects.
