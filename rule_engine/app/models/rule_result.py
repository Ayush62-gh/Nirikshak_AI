"""
Individual Rule Result DTOs.
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RuleStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    COMPLIANT = "COMPLIANT"          # Alias for PASS
    NON_COMPLIANT = "NON_COMPLIANT"  # Alias for FAIL
    ERROR = "ERROR"


class RuleSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class EvidenceSource(str, Enum):
    STRUCTURED_INPUT = "STRUCTURED_INPUT"
    OCR = "OCR"
    IMAGE_ANALYSIS = "IMAGE_ANALYSIS"
    USER_INPUT = "USER_INPUT"
    UNKNOWN = "UNKNOWN"


class RuleEvidence(BaseModel):
    """Structured provenance evidence describing the source, raw value, and confidence of extracted input data."""
    field: str = Field(..., description="Product request field associated with this evidence")
    value: Optional[Any] = Field(None, description="Raw detected value or text snippet")
    source: EvidenceSource = Field(EvidenceSource.STRUCTURED_INPUT, description="Provenance source: STRUCTURED_INPUT, OCR, IMAGE_ANALYSIS, USER_INPUT, UNKNOWN")
    confidence: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Extraction/detection confidence score (0.0 to 1.0)")
    rawAnnotation: Optional[str] = Field(None, description="Optional raw label snippet or visual bounding context")


class IndividualRuleResult(BaseModel):
    """Specific individual rule execution result adhering to API contract."""
    ruleId: str = Field(..., description="Unique rule ID (e.g. LM-RULE-MRP-001)")
    ruleName: str = Field(..., description="Human-readable rule name")
    status: RuleStatus = Field(..., description="Evaluation status: PASS, FAIL, MANUAL_REVIEW, NOT_APPLICABLE")
    severity: RuleSeverity = Field(RuleSeverity.MEDIUM, description="Rule severity level: CRITICAL, HIGH, MEDIUM, LOW, INFO")
    message: str = Field(..., description="Explanatory message describing rule outcome")
    field: Optional[str] = Field(None, description="Product request input field evaluated by this rule")
    evidence: Optional[RuleEvidence] = Field(None, description="Structured provenance evidence used for evaluation")


class ViolationDetail(BaseModel):
    """Detailed summary of a rule violation or item requiring review."""
    ruleId: str = Field(..., description="ID of rule that failed or requires manual review")
    ruleName: str = Field(..., description="Name of rule")
    severity: RuleSeverity = Field(..., description="Severity of violation")
    message: str = Field(..., description="Violation message")
    field: Optional[str] = Field(None, description="Target field associated with violation")
    remediation: Optional[str] = Field(None, description="Suggested corrective action")
    evidence: Optional[RuleEvidence] = Field(None, description="Associated evidence metadata")




class RuleResult(BaseModel):
    """Result returned by an individual rule execution (internal legacy compatibility)."""
    rule_id: str = Field(..., description="Unique identifier for the rule")
    rule_name: str = Field(..., description="Human-readable rule name")
    category: str = Field(..., description="Legal metrology clause or category")
    status: RuleStatus = Field(..., description="Evaluation outcome status")
    message: str = Field(..., description="Explanatory message of evaluation result")
    remediation: Optional[str] = Field(None, description="Suggested corrective action if non-compliant")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional context or raw findings")

