import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core import database

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Health check verifying backend service status and database connectivity.
    Healthy: 200 {"status":"ok"} (PPT Slide 8 contract).
    Database unreachable: 503 so load balancers / uptime monitors see the real state.
    """
    try:
        with database.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:  # noqa: BLE001
        logger.error("Health check: database unreachable (%s)", type(e).__name__)
        return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})

    return {"status": "ok"}
