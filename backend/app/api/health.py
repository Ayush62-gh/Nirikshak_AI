from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.database.connection import check_database_connection
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Returns the health status of the application and its database connectivity.",
)
async def health_check() -> JSONResponse:
    """Check application and database health."""
    db_connected = await check_database_connection()
    db_status = "connected" if db_connected else "disconnected"
    overall_status = "healthy" if db_connected else "degraded"
    status_code = status.HTTP_200_OK if db_connected else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "database": db_status,
            "version": "1.0.0",
            "app_name": settings.APP_NAME,
        },
    )
