from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.inspection import ComplianceResultStatus
from app.models.violation import ViolationSeverity, ViolationStatus
from app.schemas.violation import ViolationResponse


class RuleResultSchema(BaseModel):
    rule_id: str
    rule_number: Optional[str] = None
    name: str
    category: str
    status: str
    severity: str
    weight: int
    message: str
    detected_value: Optional[str] = None
    expected_value: Optional[str] = None
    legal_reference: Optional[str] = None
    evidence_image: Optional[str] = None


class ComplianceScoreSchema(BaseModel):
    score: float
    max_score: float
    percentage: float
    status: ComplianceResultStatus
    total_rules: int
    passed: int
    warnings: int
    failed: int
    not_applicable: int
    critical_failures: int
    high_failures: int


class ComplianceResultResponse(BaseModel):
    score: ComplianceScoreSchema
    rule_results: List[RuleResultSchema]
    violations: List[ViolationResponse] = []
