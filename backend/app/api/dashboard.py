from typing import Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.inspection import (
    ComplianceResultStatus,
    Inspection,
)
from app.models.product import Product
from app.models.user import User
from app.models.violation import Violation, ViolationSeverity
from app.schemas.common import APIResponse
from app.schemas.dashboard import (
    CategoryComplianceItem,
    DashboardSummary,
    DashboardTrends,
    SeverityBreakdown,
    ViolationTrendItem,
)
from app.schemas.inspection import InspectionResponse

router = APIRouter(tags=["Dashboard & Analytics"])


@router.get(
    "/summary",
    response_model=APIResponse[DashboardSummary],
    summary="Get overall compliance dashboard summary statistics",
    description="Returns aggregate metrics including total inspections, pass/fail counts, average score, and violation counts.",
)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[DashboardSummary]:
    """Retrieve compliance summary statistics for dashboard."""
    # 1. Total Inspections
    total_insp_res = await db.execute(select(func.count(Inspection.id)))
    total_inspections = total_insp_res.scalar_one() or 0

    # 2. Result Breakdown
    result_breakdown_res = await db.execute(
        select(Inspection.overall_result, func.count(Inspection.id)).group_by(
            Inspection.overall_result
        )
    )
    result_counts: Dict[str, int] = {
        row[0].value if hasattr(row[0], "value") else str(row[0]): row[1]
        for row in result_breakdown_res.all()
    }

    compliant_count = result_counts.get(ComplianceResultStatus.COMPLIANT.value, 0)
    non_compliant_count = result_counts.get(ComplianceResultStatus.NON_COMPLIANT.value, 0)
    warning_count = result_counts.get(ComplianceResultStatus.WARNING.value, 0)

    # 3. Average Compliance Score
    avg_score_res = await db.execute(
        select(func.avg(Inspection.compliance_score)).where(
            Inspection.compliance_score.isnot(None)
        )
    )
    raw_avg = avg_score_res.scalar_one()
    avg_score = round(float(raw_avg), 1) if raw_avg is not None else 0.0

    # 4. Total Violations & Severity Breakdown
    total_viol_res = await db.execute(select(func.count(Violation.id)))
    total_violations = total_viol_res.scalar_one() or 0

    sev_res = await db.execute(
        select(Violation.severity, func.count(Violation.id)).group_by(
            Violation.severity
        )
    )
    sev_counts: Dict[str, int] = {
        row[0].value if hasattr(row[0], "value") else str(row[0]): row[1]
        for row in sev_res.all()
    }

    severity_breakdown = SeverityBreakdown(
        CRITICAL=sev_counts.get(ViolationSeverity.CRITICAL.value, 0),
        HIGH=sev_counts.get(ViolationSeverity.HIGH.value, 0),
        MEDIUM=sev_counts.get(ViolationSeverity.MEDIUM.value, 0),
        LOW=sev_counts.get(ViolationSeverity.LOW.value, 0),
        INFO=sev_counts.get(ViolationSeverity.INFO.value, 0),
    )

    # 5. Recent Inspections
    recent_res = await db.execute(
        select(Inspection)
        .options(selectinload(Inspection.product))
        .order_by(Inspection.id.desc())
        .limit(5)
    )
    recent_inspections = [
        InspectionResponse.model_validate(i) for i in recent_res.scalars().all()
    ]

    summary = DashboardSummary(
        total_inspections=total_inspections,
        compliant_products=compliant_count,
        non_compliant_products=non_compliant_count,
        warning_products=warning_count,
        average_compliance_score=avg_score,
        total_violations=total_violations,
        violations_by_severity=severity_breakdown,
        recent_inspections=recent_inspections,
    )

    return APIResponse(
        success=True,
        data=summary,
        message="Dashboard summary retrieved successfully",
    )


@router.get(
    "/trends",
    response_model=APIResponse[DashboardTrends],
    summary="Get compliance trends and top violation categories",
    description="Returns top detected violation types and product category compliance averages.",
)
async def get_dashboard_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[DashboardTrends]:
    """Retrieve compliance trends."""
    # Top 5 Violation Types
    top_viol_res = await db.execute(
        select(Violation.violation_type, func.count(Violation.id))
        .group_by(Violation.violation_type)
        .order_by(func.count(Violation.id).desc())
        .limit(5)
    )
    top_violations = [
        ViolationTrendItem(violation_type=row[0], count=row[1])
        for row in top_viol_res.all()
    ]

    # Category Breakdown
    cat_res = await db.execute(
        select(
            Product.category,
            func.count(Inspection.id),
            func.avg(Inspection.compliance_score),
        )
        .join(Inspection, Product.id == Inspection.product_id)
        .where(Product.category.isnot(None))
        .group_by(Product.category)
        .limit(10)
    )
    category_breakdown = [
        CategoryComplianceItem(
            category=row[0] or "General",
            inspections_count=row[1],
            average_score=round(float(row[2]), 1) if row[2] is not None else 0.0,
        )
        for row in cat_res.all()
    ]

    return APIResponse(
        success=True,
        data=DashboardTrends(
            top_violations=top_violations,
            category_breakdown=category_breakdown,
        ),
        message="Dashboard trends retrieved successfully",
    )
