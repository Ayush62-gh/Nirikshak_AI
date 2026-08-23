from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.health import health_check
from app.api.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import (
    NirikshakException,
    generic_exception_handler,
    http_exception_handler,
    nirikshak_exception_handler,
    validation_exception_handler,
)
from app.core.logging import logger
from app.database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for initialization and cleanup."""
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")

    # Ensure storage directories exist
    upload_dir = settings.upload_path
    report_dir = settings.report_path
    logger.info(f"Storage directories initialized: uploads={upload_dir}, reports={report_dir}")

    # Initialize database tables
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization error during startup: {e}")

    yield

    logger.info("Shutting down Nirikshak AI backend...")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-ready backend for verifying compliance of packaged commodities under "
        "the Legal Metrology (Packaged Commodities) Rules, 2011 via OCR and rule-based validation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [str(settings.CORS_ORIGINS)]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handlers
app.add_exception_handler(NirikshakException, nirikshak_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Direct root health check (as per specification GET /health)
app.add_api_route(
    "/health",
    health_check,
    methods=["GET"],
    tags=["Health"],
    summary="Root health check endpoint",
)

# Mount API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"], summary="API Root")
async def root():
    """API Root endpoint providing service information and links to documentation."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api_v1": settings.API_V1_STR,
    }
