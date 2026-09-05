"""
Compliance Summary Result Generator.
Aggregates individual rule results into final EvaluateComplianceResponse payload.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, ViolationDetail
from app.models.compliance import EvaluateComplianceResponse



class ComplianceResultGenerator:
    """
    Component responsible for generating the final compliance summary response
    from a collection of individual rule results.
    """

    def generate_report(
        self,
        product: EvaluateProductRequest,
        results: List[IndividualRuleResult],
        remediation_map: Dict[str, str] = None
    ) -> EvaluateComplianceResponse:
        """
        Calculates rule statistics and generates the EvaluateComplianceResponse with decision trace.
        """
        remediation_map = remediation_map or {}
        total = len(results)
        passed = sum(1 for r in results if r.status == RuleStatus.PASS)
        failed = sum(1 for r in results if r.status == RuleStatus.FAIL)
        manual_review = sum(1 for r in results if r.status == RuleStatus.MANUAL_REVIEW)
        not_applicable = sum(1 for r in results if r.status == RuleStatus.NOT_APPLICABLE)

        # Explicit Status Precedence: FAIL > MANUAL_REVIEW > PASS > NOT_APPLICABLE
        if failed > 0:
            overall_status = RuleStatus.FAIL
        elif manual_review > 0:
            overall_status = RuleStatus.MANUAL_REVIEW
        elif passed > 0:
            overall_status = RuleStatus.PASS
        elif not_applicable == total and total > 0:
            overall_status = RuleStatus.NOT_APPLICABLE
        else:
            overall_status = RuleStatus.PASS

        # Decision Trace Assembly
        sources_used = list({r.evidence.source for r in results if r.evidence and r.evidence.source})
        decision_trace: Dict[str, Any] = {
            "summary": {
                "pass": passed,
                "fail": failed,
                "manualReview": manual_review,
                "notApplicable": not_applicable
            },
            "evidenceSources": sources_used,
            "evaluatedAt": datetime.now(timezone.utc).isoformat()
        }


        # Build violation list for FAIL and MANUAL_REVIEW rules
        violations: List[ViolationDetail] = []
        for r in results:
            if r.status in (RuleStatus.FAIL, RuleStatus.MANUAL_REVIEW):
                remediation = remediation_map.get(r.ruleId, f"Review and rectify statutory declaration for rule {r.ruleId}.")
                violations.append(
                    ViolationDetail(
                        ruleId=r.ruleId,
                        ruleName=r.ruleName,
                        severity=r.severity,
                        message=r.message,
                        field=r.field,
                        remediation=remediation,
                        evidence=r.evidence
                    )
                )

        return EvaluateComplianceResponse(
            productId=product.productId,
            overallStatus=overall_status,
            totalRules=total,
            passedRules=passed,
            failedRules=failed,
            manualReviewRules=manual_review,
            notApplicableRules=not_applicable,
            decisionTrace=decision_trace,
            individualRuleResults=results,
            violations=violations
        )


