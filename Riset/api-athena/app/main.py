from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Request

from app.config import get_settings
from app.database import init_db
from app.logging_config import configure_logging
from app.routers import athena


configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    logger.info(
        "app_start app=%s version=%s log_file=%s",
        settings.app_name,
        settings.app_version,
        settings.log_path,
    )
    yield
    logger.info("app_shutdown app=%s", settings.app_name)


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Local API adapter for Athena OHDSI vocabulary search.",
    lifespan=lifespan,
)

app.include_router(athena.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = int((perf_counter() - start) * 1000)
        logger.exception(
            "request_error method=%s path=%s duration_ms=%s",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = int((perf_counter() - start) * 1000)
    logger.info(
        "request_complete method=%s path=%s status_code=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health", tags=["system"])
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }
