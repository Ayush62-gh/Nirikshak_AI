"""
Compliance Summary DTOs.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict
from app.models.rule_result import RuleResult, IndividualRuleResult, ViolationDetail, RuleStatus


class ComplianceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    PARTIAL = "PARTIAL"


class EvaluateComplianceResponse(BaseModel):
    """
    API Contract Response payload returned to Teammates' Backend / Upstream Services.
    Contains overall compliance status, rule counts, individual rule results, and violations.
    """
    productId: str = Field(..., description="Unique product identifier SKU")
    overallStatus: RuleStatus = Field(..., description="Overall compliance result: PASS, FAIL, or MANUAL_REVIEW")
    totalRules: int = Field(..., ge=0, description="Total rules evaluated")
    passedRules: int = Field(..., ge=0, description="Number of passed rules")
    failedRules: int = Field(..., ge=0, description="Number of failed rules")
    manualReviewRules: int = Field(0, ge=0, description="Number of rules flagged for manual review")
    notApplicableRules: int = Field(0, ge=0, description="Number of rules that were not applicable")
    decisionTrace: Optional[Dict[str, Any]] = Field(None, description="Summary decision trace breakdown containing rule counts and evidence sources")
    individualRuleResults: List[IndividualRuleResult] = Field(default_factory=list, description="Array of individual rule execution results")
    violations: List[ViolationDetail] = Field(default_factory=list, description="Structured list of violations or manual review items")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "productId": "PROD-88210",
                "overallStatus": "FAIL",
                "totalRules": 4,
                "passedRules": 2,
                "failedRules": 1,
                "manualReviewRules": 1,
                "individualRuleResults": [
                    {
                        "ruleId": "LM-RULE-MRP-001",
                        "ruleName": "MRP Declaration Presence & Format Check",
                        "status": "PASS",
                        "severity": "CRITICAL",
                        "message": "MRP declaration is present with statutory tax inclusion clause."
                    },
                    {
                        "ruleId": "LM-RULE-NETQTY-002",
                        "ruleName": "Net Quantity Declaration Check",
                        "status": "PASS",
                        "severity": "HIGH",
                        "message": "Net Quantity declaration is present in standard units."
                    },
                    {
                        "ruleId": "LM-RULE-MFG-003",
                        "ruleName": "Manufacturer / Packer Details Check",
                        "status": "FAIL",
                        "severity": "HIGH",
                        "message": "Manufacturer address is incomplete; missing pincode/city."
                    },
                    {
                        "ruleId": "LM-RULE-DATE-004",
                        "ruleName": "Month and Year of Packing Check",
                        "status": "MANUAL_REVIEW",
                        "severity": "MEDIUM",
                        "message": "Date format '08/2026' requires verification against standard date rules."
                    }
                ],
                "violations": [
                    {
                        "ruleId": "LM-RULE-MFG-003",
                        "ruleName": "Manufacturer / Packer Details Check",
                        "severity": "HIGH",
                        "message": "Manufacturer address is incomplete; missing pincode/city.",
                        "remediation": "Provide complete street, city, state, and pincode in manufacturer address."
                    },
                    {
                        "ruleId": "LM-RULE-DATE-004",
                        "ruleName": "Month and Year of Packing Check",
                        "severity": "MEDIUM",
                        "message": "Date format '08/2026' requires verification against standard date rules.",
                        "remediation": "Verify that month is written as words or 2-digit number with 4-digit year."
                    }
                ]
            }
        }
    )



class ComplianceReport(BaseModel):
    """Final aggregated compliance summary report JSON response (Legacy internal model)."""
    product_id: str = Field(..., description="Target product identifier")
    overall_status: ComplianceStatus = Field(..., description="Overall compliance status")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="Percentage compliance score (0-100)")
    total_rules_evaluated: int = Field(..., ge=0, description="Total rules evaluated")
    passed_rules_count: int = Field(..., ge=0, description="Count of compliant rules")
    failed_rules_count: int = Field(..., ge=0, description="Count of non-compliant rules")
    rule_results: List[RuleResult] = Field(default_factory=list, description="Individual rule evaluation results")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of evaluation")

