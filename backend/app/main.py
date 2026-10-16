from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.v1.router import router as api_v1_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="MultimediaToolKit — AI-First Multimedia Transformation Platform",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(api_v1_router)


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "documentation": "/docs",
        "health": "/health",
        "api_v1": "/api/v1",
    }
