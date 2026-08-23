from pathlib import Path
from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.schemas.common import APIResponse
from app.schemas.report import ReportResponse
from app.services.report_service import ReportService

router = APIRouter(tags=["Reports"])


@router.get(
    "/{inspection_id}",
    summary="Download or view inspection compliance PDF report",
    description="Retrieves and streams the official Legal Metrology Compliance Inspection PDF report.",
    response_class=FileResponse,
)
async def get_report_pdf(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Download or view PDF compliance report."""
    report_file: Path = await ReportService.get_report_file(db, inspection_id)

    return FileResponse(
        path=str(report_file),
        media_type="application/pdf",
        filename=f"Nirikshak_Compliance_Report_{inspection_id}.pdf",
        headers={
            "Content-Disposition": f"inline; filename=Nirikshak_Compliance_Report_{inspection_id}.pdf"
        },
    )


@router.post(
    "/{inspection_id}/generate",
    response_model=APIResponse[ReportResponse],
    summary="Trigger PDF report generation",
    description="Forces generation of the official Legal Metrology PDF report for an inspection.",
)
async def generate_report(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.INSPECTOR)),
) -> APIResponse[ReportResponse]:
    """Generate or re-generate PDF report."""
    report = await ReportService.generate_inspection_pdf(db, inspection_id)
    return APIResponse(
        success=True,
        data=ReportResponse.model_validate(report),
        message="Compliance report generated successfully",
    )
