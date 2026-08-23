from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from app.core.logging import logger
from compliance_engine.compliance_score import ComplianceScoreCalculator, ComplianceScoreResult
from compliance_engine.rule_registry import RuleRegistry
from compliance_engine.rules.base_rule import BaseRule, RuleResult, RuleStatus


@dataclass
class ComplianceResult:
    score_result: ComplianceScoreResult
    rule_results: List[RuleResult]
    violations: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score_result.to_dict(),
            "rule_results": [r.to_dict() for r in self.rule_results],
            "violations": self.violations,
        }


class LegalMetrologyComplianceEngine:
    """
    Core Compliance Engine for Legal Metrology (Packaged Commodities) Rules, 2011.
    Executes rules against normalized declarations, records violations, and computes scores.
    """

    def __init__(self, rules: Optional[List[BaseRule]] = None):
        self.rules: List[BaseRule] = rules or RuleRegistry.load_rules_from_json()

    def reload_rules(self) -> None:
        """Reload active rules from configuration source."""
        self.rules = RuleRegistry.load_rules_from_json()

    def evaluate(
        self,
        declarations: List[Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ComplianceResult:
        """
        Evaluate extracted declarations against active Legal Metrology rules.
        """
        # Map declarations by declaration_type for easy rule lookup
        decl_dict: Dict[str, Any] = {}
        for d in declarations:
            decl_type = getattr(d, "declaration_type", None)
            if decl_type is None and isinstance(d, dict):
                decl_type = d.get("declaration_type")
            if decl_type:
                decl_dict[decl_type] = d

        rule_results: List[RuleResult] = []
        violations: List[Dict[str, Any]] = []

        ctx = context or {}

        for rule in self.rules:
            try:
                result = rule.evaluate(declarations=decl_dict, context=ctx)
                rule_results.append(result)

                # If rule failed or generated a warning, format a violation
                if result.status in (RuleStatus.FAIL, RuleStatus.WARNING):
                    violations.append({
                        "rule_id": result.rule_id,
                        "rule_number": result.rule_number,
                        "violation_type": f"{result.category}_VIOLATION",
                        "description": result.message,
                        "severity": result.severity.value,
                        "detected_value": result.detected_value,
                        "expected_value": result.expected_value,
                        "evidence_image": result.evidence_image,
                        "status": "OPEN",
                    })

            except Exception as e:
                logger.error(f"Error executing rule {rule.rule_id}: {e}")
                rule_results.append(
                    RuleResult(
                        rule_id=rule.rule_id,
                        rule_number=rule.rule_number,
                        name=rule.name,
                        category=rule.category,
                        status=RuleStatus.FAIL,
                        severity=rule.severity,
                        weight=rule.weight,
                        message=f"Rule evaluation error: {str(e)}",
                        legal_reference=rule.legal_reference,
                    )
                )

        score_res = ComplianceScoreCalculator.calculate(rule_results)

        logger.info(
            f"Compliance evaluated: {score_res.passed}/{score_res.total_rules} passed, "
            f"score={score_res.percentage}%, status={score_res.status.value}"
        )

        return ComplianceResult(
            score_result=score_res,
            rule_results=rule_results,
            violations=violations,
        )
