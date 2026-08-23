from typing import List, Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database.connection import get_db
from app.models.inspection import ComplianceResultStatus, InspectionStatus
from app.models.user import User, UserRole
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.inspection import (
    InspectionCreate,
    InspectionDetailResponse,
    InspectionImageResponse,
    InspectionResponse,
)
from app.schemas.violation import ViolationResponse
from app.services.inspection_service import InspectionService

router = APIRouter(tags=["Inspections & Scans"])


@router.post(
    "",
    response_model=APIResponse[InspectionDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new inspection",
    description="Initiates a new inspection session for an inspector.",
)
async def create_inspection(
    payload: InspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.INSPECTOR)),
) -> APIResponse[InspectionDetailResponse]:
    """Create a new inspection."""
    inspection = await InspectionService.create_inspection(
        db=db, inspector_id=current_user.id, payload=payload
    )
    return APIResponse(
        success=True,
        data=InspectionDetailResponse.model_validate(inspection),
        message="Inspection session created successfully",
    )


@router.post(
    "/{inspection_id}/images",
    response_model=APIResponse[List[InspectionImageResponse]],
    summary="Upload package images for inspection",
    description="Uploads one or multiple product/package label images for an inspection.",
)
async def upload_inspection_images(
    inspection_id: int,
    images: List[UploadFile] = File(..., description="Package label image files (JPEG, PNG, WEBP)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.INSPECTOR)),
) -> APIResponse[List[InspectionImageResponse]]:
    """Upload package label images for inspection."""
    saved_images = await InspectionService.add_inspection_images(
        db=db, inspection_id=inspection_id, files=images
    )
    return APIResponse(
        success=True,
        data=[InspectionImageResponse.model_validate(img) for img in saved_images],
        message=f"{len(saved_images)} image(s) uploaded successfully",
    )


@router.get(
    "/{inspection_id}",
    response_model=APIResponse[InspectionDetailResponse],
    summary="Get inspection details",
    description="Returns complete inspection details, including uploaded images, extracted declarations, and violations.",
)
async def get_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[InspectionDetailResponse]:
    """Get complete inspection information."""
    inspection = await InspectionService.get_inspection(db=db, inspection_id=inspection_id)
    return APIResponse(
        success=True,
        data=InspectionDetailResponse.model_validate(inspection),
        message="Inspection details retrieved successfully",
    )


@router.get(
    "",
    response_model=PaginatedResponse[InspectionResponse],
    summary="List inspections",
    description="Returns a paginated list of inspections with filtering and search.",
)
async def list_inspections(
    status: Optional[InspectionStatus] = Query(default=None, description="Filter by status"),
    overall_result: Optional[ComplianceResultStatus] = Query(default=None, description="Filter by compliance result"),
    product_id: Optional[int] = Query(default=None, description="Filter by product ID"),
    search: Optional[str] = Query(default=None, description="Search product name or barcode"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[InspectionResponse]:
    """List inspections with pagination and filters."""
    # If viewer or inspector, filter if appropriate (or allow viewing all inspections)
    inspector_filter = None
    if current_user.role == UserRole.INSPECTOR:
        # Inspectors can see all inspections or filter by their own if requested
        pass

    inspections, total_items = await InspectionService.list_inspections(
        db=db,
        inspector_id=inspector_filter,
        status=status,
        overall_result=overall_result,
        product_id=product_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0

    return PaginatedResponse(
        success=True,
        data=[InspectionResponse.model_validate(i) for i in inspections],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
        message="Inspections retrieved successfully",
    )


@router.get(
    "/{inspection_id}/violations",
    response_model=APIResponse[List[ViolationResponse]],
    summary="Get inspection violations",
    description="Returns all legal metrology rule violations detected during the inspection.",
)
async def get_inspection_violations(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[List[ViolationResponse]]:
    """Retrieve violations for a specific inspection."""
    violations = await InspectionService.get_inspection_violations(
        db=db, inspection_id=inspection_id
    )
    return APIResponse(
        success=True,
        data=[ViolationResponse.model_validate(v) for v in violations],
        message="Violations retrieved successfully",
    )


@router.post(
    "/{inspection_id}/scan",
    response_model=APIResponse[InspectionDetailResponse],
    summary="Trigger scanning and compliance analysis pipeline",
    description="Runs OCR extraction and legal metrology rule compliance checks on uploaded inspection images.",
)
async def run_scan_pipeline(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.INSPECTOR)),
) -> APIResponse[InspectionDetailResponse]:
    """
    Run full scanning and compliance pipeline on inspection images.
    """
    from app.services.compliance_service import ComplianceService
    completed_inspection = await ComplianceService.run_full_pipeline(
        db=db, inspection_id=inspection_id
    )
    return APIResponse(
        success=True,
        data=InspectionDetailResponse.model_validate(completed_inspection),
        message=f"Scan and compliance evaluation completed with status: {completed_inspection.overall_result.value}",
    )
