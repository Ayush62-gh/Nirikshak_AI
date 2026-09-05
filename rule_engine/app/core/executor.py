"""
Rule Executor component.
Safely executes selected rules against product data.
"""

from typing import List
import logging
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity

logger = logging.getLogger("rule_engine.executor")


class RuleExecutor:
    """
    Component responsible for running individual rule evaluate methods,
    capturing errors gracefully, and producing a list of IndividualRuleResult objects.
    """

    def execute_rules(self, rules: List[AbstractRule], product: EvaluateProductRequest) -> List[IndividualRuleResult]:
        """
        Executes a list of rules against the product data.
        """
        results: List[IndividualRuleResult] = []

        for rule in rules:
            try:
                result = rule.evaluate(product)
                results.append(result)
            except Exception as exc:
                logger.error(f"Error executing rule {rule.rule_id}: {str(exc)}", exc_info=True)
                results.append(
                    IndividualRuleResult(
                        ruleId=rule.rule_id,
                        ruleName=rule.rule_name,
                        status=RuleStatus.FAIL,
                        severity=RuleSeverity.CRITICAL,
                        message=f"Internal rule execution failure: {str(exc)}"
                    )
                )

        return results

