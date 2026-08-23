from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.violation import ViolationSeverity, ViolationStatus


class ViolationBase(BaseModel):
    rule_id: str = Field(..., description="Unique legal metrology rule identifier (e.g. LM-PC-001)")
    violation_type: str = Field(..., description="Classification category of the violation")
    description: str = Field(..., description="Detailed explanation of the non-compliance")
    severity: ViolationSeverity = Field(default=ViolationSeverity.HIGH, description="Severity grade")
    evidence_image: Optional[str] = Field(default=None, description="Path to crop/evidence image")
    detected_value: Optional[str] = Field(default=None, description="Value found on label")
    expected_value: Optional[str] = Field(default=None, description="Legally required declaration standard")
    status: ViolationStatus = Field(default=ViolationStatus.OPEN, description="Resolution status")


class ViolationCreate(ViolationBase):
    inspection_id: int


class ViolationResponse(ViolationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    created_at: datetime
