from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.api import health, soil, recommendation, weather, chat, auth, reports
from app.db.session import init_db

from contextlib import asynccontextmanager

settings = get_settings()
setup_logging(debug=settings.debug)
logger = get_logger("agrimind.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database schema and verify RAG index on startup
    try:
        init_db()
    except Exception as exc:
        logger.warning("Database initialization deferred or failed: %s", exc)

    try:
        from app.rag.index_knowledge import ensure_indexed
        indexed_count = ensure_indexed()
        logger.info("RAG vector index verified (%s chunks active)", indexed_count)
    except Exception as exc:
        logger.warning("RAG knowledge index verification deferred or failed: %s", exc)
    yield


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware with dynamic and local origin configuration
allowed_origins = settings.get_cors_origins()
logger.info("Configuring CORS for origins: %s", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?:\/\/.*\.vercel\.app$|^https?:\/\/localhost(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router)
app.include_router(soil.router)
app.include_router(recommendation.router)
app.include_router(weather.router)
app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(reports.router)


# Global Exception Handlers (no leaking stack traces or secrets)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "error_type": "HTTPException",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Create clear, concise messages for each field
    details = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        details.append(f"{loc}: {msg}" if loc else msg)

    return JSONResponse(
        status_code=422,
        content={
            "detail": "; ".join(details) or "Request validation failed.",
            "status_code": 422,
            "error_type": "ValidationError",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error processing %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred while processing your request. Please try again or verify input parameters.",
            "status_code": 500,
            "error_type": "InternalServerError",
        },
    )


# Root Endpoints
@app.get("/", tags=["root"])
async def root():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health",
        "info": "/api/info",
    }


@app.get("/health", tags=["root"])
async def root_health():
    """Alias for /api/health for standard container liveness probes."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
