"""
Main FastAPI Application Entrypoint.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.exceptions.handlers import register_exception_handlers


def create_app() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title="Legal Metrology Compliance Rule Engine API",
        description="Production-Ready Rule Engine API based on the Legal Metrology (Packaged Commodities) Rules, 2011.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS Configuration
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Exception Handlers
    register_exception_handlers(app)

    # Register API Routes
    app.include_router(router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5002))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

