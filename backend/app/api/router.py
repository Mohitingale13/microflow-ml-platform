from fastapi import APIRouter

from app.routers import artifacts, dashboard, datasets, experiments, health, metrics, pipeline, runs, training, ai, assistant

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(datasets.router)
api_router.include_router(experiments.router)
api_router.include_router(runs.router)
api_router.include_router(training.router)
api_router.include_router(artifacts.router)
api_router.include_router(metrics.router)
api_router.include_router(pipeline.router)
api_router.include_router(ai.router)
api_router.include_router(assistant.router)

