from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db
from app.routers import scan


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Nirikshak AI Backend",
    description="Legal Metrology Packaged Commodities compliance checker API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware configuration for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount scan API router
app.include_router(scan.router, prefix="/api")

# TODO (Phase 8): Mount health router here once routers/health.py is implemented
# app.include_router(health.router, prefix="/api")
