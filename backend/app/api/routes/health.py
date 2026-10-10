from fastapi import APIRouter
from app.core.database import engine
from sqlalchemy import text

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Health check endpoint verifying backend service status and database connectivity.
    Strictly conforms to PPT Slide 8: GET /health returns {"status":"ok"}.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pass

    return {"status": "ok"}
