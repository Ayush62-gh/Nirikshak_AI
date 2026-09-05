from fastapi import APIRouter, File, UploadFile, Query, status, Depends
from fastapi.responses import JSONResponse
from app.services.scan_service import process_scan
from app.db.session import get_scan, list_scans, count_scans
from app.schemas.scan_schemas import ScanResponse, ScanListResponse, ErrorResponse
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(tags=["scans"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}


@router.post(
    "/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
    summary="Upload package label image for compliance scan",
)
async def create_scan(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="invalid_image",
                detail="Invalid image content-type. Only image/jpeg and image/png are supported.",
            ).model_dump(),
        )

    image_bytes = await image.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="file_too_large",
                detail="File size exceeds 10MB limit.",
            ).model_dump(),
        )

    filename = image.filename or "scan.jpg"
    return await process_scan(image_bytes, filename)


@router.get(
    "/scans",
    response_model=ScanListResponse,
    summary="List scan history",
)
async def get_scans(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    rows = list_scans(page=page, limit=limit)
    scans = [ScanResponse.from_db_row(row) for row in rows]
    total_count = count_scans()
    return ScanListResponse(
        scans=scans,
        page=page,
        limit=limit,
        total=total_count,
    )


@router.get(
    "/scans/{scan_id}",
    response_model=ScanResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get scan by ID",
)
async def get_scan_by_id(
    scan_id: str,
    current_user: User = Depends(get_current_user),
):
    row = get_scan(scan_id)
    if not row:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                error="Not Found",
                detail=f"Scan with ID '{scan_id}' not found",
            ).model_dump(),
        )
    return ScanResponse.from_db_row(row)

