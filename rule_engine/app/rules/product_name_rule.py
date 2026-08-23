"""
Legal Metrology Compliance Rule: Generic / Commodity Name Declaration Rule.
Statutory Provision: Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011.
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class ProductNameRule(AbstractRule):
    """
    Validates declaration of common or generic name of the commodity.
    Legal Reference: Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-NAME-004"

    @property
    def rule_name(self) -> str:
        return "Generic / Commodity Name Declaration Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> str:
        return "productName"

    @property
    def remediation_hint(self) -> Optional[str]:

        return "Declare the generic or common name of the commodity on the principal display panel."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """Generic name declaration applies to all retail packaged commodities."""
        return True

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        # Case 1: Product / Commodity Name is completely missing
        if not product.productName or not product.productName.strip():
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Generic or common name of the commodity is completely missing from product payload."
            )

        name_text = product.productName.strip()

        # Case 2: Extremely short or purely non-alphabetic commodity name
        if len(name_text) < 2 or not any(c.isalpha() for c in name_text):
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.MANUAL_REVIEW,
                severity=RuleSeverity.MEDIUM,
                message="Declared commodity name appears vague or numerical; manual label verification required."
            )

        # Case 3: Valid generic name declared
        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.PASS,
            severity=self.severity,
            message="Generic or common name of commodity is declared."
        )
