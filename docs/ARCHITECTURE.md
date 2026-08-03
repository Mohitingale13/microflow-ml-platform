# MicroFlow Architecture

Version: 1.0

Status: Frozen

---

# Overview

MicroFlow follows a modular layered architecture inspired by modern ML infrastructure platforms such as MLflow and Weights & Biases.

The architecture is intentionally designed around engineering workflows instead of machine learning algorithms.

The system separates concerns into independent modules responsible for data management, experiment execution, model training, artifact tracking and visualization.

This separation allows future scaling without redesigning the platform.

---

# High Level Architecture

```
                        React Frontend
                               │
                               ▼
                        FastAPI REST API
                               │
        ┌──────────────┬──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
 Dataset Manager Experiment Manager  Run Manager   Artifact Registry
                               │
                               ▼
                      Training Engine
                               │
                               ▼
                      Metrics Engine
                               │
                               ▼
                        PostgreSQL Database
```

---

# Layered Architecture

The backend follows a layered architecture.

```
Client

↓

Router Layer

↓

Service Layer

↓

Repository Layer

↓

Database
```

Each layer has exactly one responsibility.

---

# Backend Architecture

```
backend/

app/

├── api/
│
├── core/
│
├── db/
│
├── models/
│
├── repositories/
│
├── routers/
│
├── schemas/
│
├── services/
│
├── training/
│
├── utils/
│
└── main.py
```

---

## api/

Contains API registration and application initialization.

No business logic.

---

## routers/

Responsible only for

- request validation
- response serialization
- HTTP status codes

Routers must never contain business logic.

---

## services/

Contains business logic.

Examples

DatasetService

ExperimentService

RunService

TrainingService

ArtifactService

MetricsService

Services communicate with repositories.

Services never call HTTP endpoints.

---

## repositories/

Responsible for database access.

Only repositories communicate with SQLAlchemy.

Services never write SQL.

---

## models/

Database models.

No business logic.

---

## schemas/

Pydantic request and response models.

Used for

validation

serialization

documentation

---

## training/

Contains machine learning logic.

Responsibilities

- preprocessing
- feature engineering
- model selection
- training
- evaluation

The training module knows nothing about HTTP.

---

## utils/

Shared utilities.

Examples

logging

file handling

helpers

validators

---

# Frontend Architecture

```
frontend/

src/

├── components/
│
├── hooks/
│
├── layouts/
│
├── pages/
│
├── services/
│
├── types/
│
├── utils/
│
└── App.tsx
```

---

## components/

Reusable UI.

Examples

Card

Table

Button

MetricCard

StatusBadge

Chart

---

## pages/

Each page represents one feature.

Dashboard

Datasets

Experiments

Training

Artifacts

Metrics

Pipeline

---

## services/

Frontend API layer.

No page directly calls fetch().

Everything goes through services.

---

## hooks/

Reusable business hooks.

Examples

useDatasets()

useExperiments()

useTraining()

---

## types/

Shared TypeScript interfaces.

---

# Database Architecture

Three primary entities.

```
Dataset
↓

Experiment

(Problem Definition)

↓

Run

(Individual Execution)

↓

Artifact
```

Every Experiment belongs to one Dataset.

Every Artifact belongs to one Run.

---

## Dataset

Stores

- metadata
- row count
- column count
- upload time

Never stores ML results.

---

## Experiment

Stores

objective definition.

Examples

name

description

dataset association

default configuration

creation metadata

Experiments do not execute training.

---

## Run

Stores

execution details.

Examples

model

hyperparameters

random seed

status

timestamps

Multiple runs belong to one experiment.

---

## Artifact

Stores generated outputs.

Examples

trained model

metrics

ROC curve

feature importance

confusion matrix

training logs

pipeline configuration

Artifacts are immutable.

---

# Dependency Rules

Allowed

Router

↓

Service

↓

Repository

↓

Database

Forbidden

Router → Database

Router → SQLAlchemy

Page → fetch()

Training → HTTP

Repository → Service

Model → Repository

No circular dependencies.

---

# Request Lifecycle

```
User

↓

HTTP Request

↓

Router

↓

Validation

↓

Service

↓

Repository

↓

Database

↓

Service

↓

Response

↓

Frontend
```

Every request follows this path.

No shortcuts.

---

# Dataset Lifecycle

```
Upload CSV

↓

Validate

↓

Store Metadata

↓

Preview

↓

Available for Experiments
```

---

# Run Lifecycle

```
Create

↓

Queued

↓

Running

↓

Completed

↓

Artifacts Generated

↓

Visible on Dashboard
```

Failed runs remain visible.

Nothing is deleted automatically.

---

# Training Lifecycle

```
Load Dataset

↓

Preprocess

↓

Split Dataset

↓

Train Model

↓

Evaluate

↓

Generate Metrics

↓

Generate Artifacts

↓

Store Results
```

---

# Artifact Lifecycle

```
Training Complete

↓

Generate Files

↓

Register Artifact

↓

Store Metadata

↓

Available for Comparison
```

Artifacts are read-only.

Creating a new run generates new artifacts.

---

# API Philosophy

Every endpoint has one responsibility.

Examples

```
POST /datasets

GET /datasets

POST /experiments

GET /experiments

POST /runs

GET /runs

POST /training/start

GET /training/status

GET /artifacts

GET /metrics
```

REST only.

No GraphQL.

---

# Error Handling

Every API returns

```
success

message

data

errors
```

Consistent response structure across the platform.

---

# Logging

Centralized logging.

Every request logs

timestamp

endpoint

status

duration

Errors include stack traces during development.

---

# Configuration

Environment variables only.

Never hardcode

database URLs

ports

paths

API keys

---

# Scalability Strategy

Current

Single FastAPI instance

↓

Future

Multiple API instances

↓

Background Workers

↓

Cloud Storage

↓

GPU Training

↓

Distributed Training

Architecture should support this transition without redesign.

---

# Future Extensions

The architecture allows adding

Neural Networks

PyTorch

LightGBM

CatBoost

Feature Store

Experiment Scheduler

Cloud Object Storage

User Authentication

Team Workspaces

without changing existing modules.

---

# Architecture Principles

Single Responsibility

Dependency Inversion

Composition over inheritance

Strong typing

Modular services

Stateless APIs

Reproducibility

Extensibility

---

# Success Criteria

The architecture should allow any engineer to understand

where code belongs,

how modules communicate,

how runs flow through the system,

and how future features can be added without breaking existing functionality.

---

End of Architecture