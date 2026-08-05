import time
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.api.router import api_router
from app.routers.health import router as health_router

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("MicroFlow backend starting — environment: %s", settings.ENVIRONMENT)
    from app.db.session import engine
    from app.db.base import Base
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("MicroFlow backend shutting down")


def create_application() -> FastAPI:
    application = FastAPI(
        title="MicroFlow",
        description="ML Experimentation Platform for Computational Biology Workflows",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health_router)
    application.include_router(api_router)

    return application


app = create_application()


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: object) -> Response:
    start = time.perf_counter()
    response: Response = await call_next(request)  # type: ignore[operator]
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "method=%s path=%s status=%d duration=%.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
