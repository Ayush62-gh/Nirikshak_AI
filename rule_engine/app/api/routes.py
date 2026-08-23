"""
API Layer Routes for Health Checks and Rule Evaluation.
"""

from fastapi import APIRouter, Depends, status
from app.models.product import ProductData, EvaluateProductRequest
from app.models.compliance import ComplianceReport, EvaluateComplianceResponse
from app.core.engine import RuleEngine
from app.api.dependencies import get_rule_engine

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
@router.get("/api/v1/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """
    Health check endpoint confirming that the Rule Engine API process is running and ready.
    """
    return {
        "status": "healthy",
        "service": "Legal Metrology Compliance Rule Engine",
        "version": "1.0.0"
    }



@router.post(
    "/api/v1/compliance/check",
    response_model=EvaluateComplianceResponse,
    status_code=status.HTTP_200_OK,
    tags=["Compliance v1 API"]
)
async def check_compliance_v1(
    request: EvaluateProductRequest,
    engine: RuleEngine = Depends(get_rule_engine)
) -> EvaluateComplianceResponse:
    """
    Production-Ready Compliance Evaluation Endpoint (v1 API).
    
    Accepts structured product information and optional field evidence metadata.
    Invokes the core Compliance Engine and returns an aggregated compliance decision.
    HTTP 200 is returned for all completed evaluations regardless of overall compliance status (PASS, FAIL, MANUAL_REVIEW).
    """
    return engine.evaluate(request)


@router.post(
    "/api/rules/evaluate",
    response_model=EvaluateComplianceResponse,
    status_code=status.HTTP_200_OK,
    tags=["Teammates API Contract (Legacy Alias)"]
)
async def evaluate_rules_contract(
    request: EvaluateProductRequest,
    engine: RuleEngine = Depends(get_rule_engine)
) -> EvaluateComplianceResponse:
    """
    Teammate Backend API Contract Endpoint for Legal Metrology Rule Engine evaluation.
    Maintained for backward compatibility. Delegation target for /api/v1/compliance/check.
    """
    return engine.evaluate(request)


@router.post(
    "/api/v1/compliance/evaluate",
    response_model=ComplianceReport,
    status_code=status.HTTP_200_OK,
    tags=["Internal Legacy Evaluation"]
)
async def evaluate_compliance_legacy(
    product: ProductData,
    engine: RuleEngine = Depends(get_rule_engine)
) -> ComplianceReport:
    """
    Evaluates structured product data against Legal Metrology Compliance Rules (Internal legacy route).
    """
    return engine.evaluate_product(product)
