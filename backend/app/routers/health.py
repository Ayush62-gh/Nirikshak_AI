from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check endpoint")
async def health_check():
    """
    Returns server status without depending on DB or external services.
    """
    return {"status": "ok"}
