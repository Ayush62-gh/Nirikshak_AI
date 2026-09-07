import io
from PIL import Image
from fastapi import APIRouter, File, UploadFile, Query, status, Depends
from fastapi.responses import JSONResponse
from app.services.scan_service import process_scan
from app.db.session import get_scan, list_scans, count_scans
from app.schemas.scan_schemas import ScanResponse, ScanListResponse, ErrorResponse
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(tags=["scans"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
CHUNK_SIZE = 64 * 1024  # 64KB


async def read_and_validate_image_file(image: UploadFile, max_size: int = MAX_FILE_SIZE) -> tuple[bytes | None, JSONResponse | None]:
    """
    Reads an uploaded file stream in 64KB chunks up to max_size.
    Enforces size limit during stream reading to prevent loading oversized files into RAM.
    Validates actual image content bytes signature using Pillow.
    Returns (image_bytes, None) on success or (None, JSONResponse) on error.
    """
    image_bytes = bytearray()

    while True:
        chunk = await image.read(CHUNK_SIZE)
        if not chunk:
            break
        image_bytes.extend(chunk)
        if len(image_bytes) > max_size:
            return None, JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    error="file_too_large",
                    detail="File size exceeds 10MB limit.",
                ).model_dump(),
            )

    if len(image_bytes) == 0:
        return None, JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="invalid_image",
                detail="Uploaded file is empty.",
            ).model_dump(),
        )

    bytes_data = bytes(image_bytes)

    try:
        with Image.open(io.BytesIO(bytes_data)) as img:
            img.verify()
            fmt = (img.format or "").upper()
    except Exception:
        return None, JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="invalid_image",
                detail="Invalid image file or corrupted image data.",
            ).model_dump(),
        )

    if fmt not in {"JPEG", "PNG"}:
        return None, JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="invalid_image",
                detail=f"Unsupported image format: '{fmt}'. Only JPEG and PNG images are supported.",
            ).model_dump(),
        )

    return bytes_data, None


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
    image_bytes, error_response = await read_and_validate_image_file(image)
    if error_response:
        return error_response

    filename = image.filename or "scan.jpg"
    return await process_scan(image_bytes, filename, user_id=current_user.id)


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
    rows = list_scans(user_id=current_user.id, page=page, limit=limit)
    scans = [ScanResponse.from_db_row(row) for row in rows]
    total_count = count_scans(user_id=current_user.id)
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
    row = get_scan(scan_id, user_id=current_user.id)
    if not row:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                error="Not Found",
                detail=f"Scan with ID '{scan_id}' not found",
            ).model_dump(),
        )
    return ScanResponse.from_db_row(row)

