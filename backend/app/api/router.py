from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.products import router as products_router
from app.api.scans import router as inspections_router
from app.api.reports import router as reports_router
from app.api.dashboard import router as dashboard_router

api_v1_router = APIRouter()

# Register sub-routers
api_v1_router.include_router(health_router, prefix="", tags=["Health"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(products_router, prefix="/products", tags=["Products"])
api_v1_router.include_router(inspections_router, prefix="/inspections", tags=["Inspections & Scans"])
api_v1_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_v1_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard & Analytics"])
