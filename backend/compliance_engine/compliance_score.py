from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from compliance_engine.rules.base_rule import RuleResult, RuleStatus
from compliance_engine.severity import Severity
from app.models.inspection import ComplianceResultStatus


@dataclass
class ComplianceScoreResult:
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "max_score": round(self.max_score, 1),
            "percentage": round(self.percentage, 1),
            "status": self.status.value,
            "total_rules": self.total_rules,
            "passed": self.passed,
            "warnings": self.warnings,
            "failed": self.failed,
            "not_applicable": self.not_applicable,
            "critical_failures": self.critical_failures,
            "high_failures": self.high_failures,
        }


class ComplianceScoreCalculator:
    """Calculates weighted compliance scores and derives final compliance status."""

    @staticmethod
    def calculate(
        rule_results: List[RuleResult],
        warning_multiplier: float = 0.5,
    ) -> ComplianceScoreResult:
        total_rules = len(rule_results)
        passed = 0
        warnings = 0
        failed = 0
        not_applicable = 0
        critical_failures = 0
        high_failures = 0

        earned_score = 0.0
        max_possible_score = 0.0

        for r in rule_results:
            if r.status == RuleStatus.NOT_APPLICABLE:
                not_applicable += 1
                continue

            rule_weight = float(r.weight)
            max_possible_score += rule_weight

            if r.status == RuleStatus.PASS:
                passed += 1
                earned_score += rule_weight
            elif r.status == RuleStatus.WARNING:
                warnings += 1
                earned_score += rule_weight * warning_multiplier
            elif r.status == RuleStatus.FAIL:
                failed += 1
                if r.severity == Severity.CRITICAL:
                    critical_failures += 1
                elif r.severity == Severity.HIGH:
                    high_failures += 1

        if max_possible_score > 0:
            percentage = round((earned_score / max_possible_score) * 100.0, 1)
        else:
            percentage = 100.0

        # Status determination logic
        # 1. Any CRITICAL failure automatically disqualifies compliance
        if critical_failures > 0:
            overall_status = ComplianceResultStatus.NON_COMPLIANT
        elif percentage >= 90.0 and high_failures == 0:
            overall_status = ComplianceResultStatus.COMPLIANT
        elif percentage >= 70.0:
            overall_status = ComplianceResultStatus.WARNING
        else:
            overall_status = ComplianceResultStatus.NON_COMPLIANT

        return ComplianceScoreResult(
            score=earned_score,
            max_score=max_possible_score,
            percentage=percentage,
            status=overall_status,
            total_rules=total_rules,
            passed=passed,
            warnings=warnings,
            failed=failed,
            not_applicable=not_applicable,
            critical_failures=critical_failures,
            high_failures=high_failures,
        )
