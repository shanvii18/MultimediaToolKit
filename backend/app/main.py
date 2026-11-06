import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.migrations import upgrade_database
from app.api.routes.health import router as health_router
from app.api.v1.router import router as api_v1_router
from app.api.v1.auth import router as auth_router

logger = logging.getLogger(__name__)

# Bring the database schema to the latest Alembic revision before serving requests.
upgrade_database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker = None
    if settings.EMBEDDED_WORKER:
        # Single-service deployments (local dev, Render Free): run the durable job worker
        # in a background thread of the API process. Jobs live in the database, so a
        # restart only pauses them; stale ones are recovered automatically.
        from app.worker.runner import JobWorker, default_worker_id

        worker = JobWorker(default_worker_id("embedded"))
        worker.start_in_background()
    try:
        yield
    finally:
        if worker:
            worker.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="MultimediaToolKit — AI-First Multimedia Transformation Platform",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

@app.middleware("http")
async def unhandled_errors_as_json(request: Request, call_next):
    """Turn unexpected exceptions into a JSON 500 *inside* the CORS middleware.

    Starlette's default handler answers outside CORSMiddleware, so the browser hides the real
    status behind a generic "Failed to fetch". With this, the frontend sees a proper 500.
    """
    try:
        return await call_next(request)
    except Exception:  # noqa: BLE001
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error. Please try again.",
                                                      "error_code": "SERVER_ERROR"})


# Configure CORS. Authentication uses the Authorization header (no cookies), so
# credentialed cross-origin requests are never needed or allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX or None,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Access-Key", "Idempotency-Key"],
    expose_headers=["Content-Disposition"],
)

# Register routes
app.include_router(health_router)
app.include_router(api_v1_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "documentation": "/docs",
        "health": "/health",
        "api_v1": "/api/v1",
    }
