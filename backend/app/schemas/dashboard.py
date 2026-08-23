from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.inspection import InspectionResponse


class SeverityBreakdown(BaseModel):
    CRITICAL: int = 0
    HIGH: int = 0
    MEDIUM: int = 0
    LOW: int = 0
    INFO: int = 0


class DashboardSummary(BaseModel):
    total_inspections: int
    compliant_products: int
    non_compliant_products: int
    warning_products: int
    average_compliance_score: float
    total_violations: int
    violations_by_severity: SeverityBreakdown
    recent_inspections: List[InspectionResponse]


class ViolationTrendItem(BaseModel):
    violation_type: str
    count: int


class CategoryComplianceItem(BaseModel):
    category: str
    inspections_count: int
    average_score: float


class DashboardTrends(BaseModel):
    top_violations: List[ViolationTrendItem]
    category_breakdown: List[CategoryComplianceItem]
