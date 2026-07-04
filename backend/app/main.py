import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()

settings = get_settings()

app = FastAPI(
    title="Citadel Marketing Platform",
    description="Self-hosted marketing automation for Citadel Cloud Management",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"success": False, "error": "Resource not found"})


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error("internal_server_error", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"success": False, "error": "Internal server error"})


@app.on_event("startup")
async def startup():
    from app.database import init_db
    await init_db()
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info("citadel_marketing_platform_started", env=settings.APP_ENV, db=settings.DATABASE_URL.split("///")[0])


@app.on_event("shutdown")
async def shutdown():
    from app.database import engine
    await engine.dispose()
    logger.info("shutdown_complete")


# --- Routers ---
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.campaigns import router as campaigns_router
from app.api.contacts import router as contacts_router
from app.api.imports import router as imports_router
from app.api.segments import router as segments_router
from app.api.unsubscribe import router as unsubscribe_router
from app.api.webhooks import router as webhooks_router
from app.api.tracking import router as tracking_router
from app.api.workflows import router as workflows_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(contacts_router, prefix="/api/v1")
app.include_router(campaigns_router, prefix="/api/v1")
app.include_router(segments_router, prefix="/api/v1")
app.include_router(imports_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(unsubscribe_router, prefix="/api/v1")
app.include_router(tracking_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "citadel-marketing-platform"}
