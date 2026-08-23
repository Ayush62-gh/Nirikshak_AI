"""
Legal Metrology Compliance Rule: Consumer Care Details Declaration Rule.
Statutory Provision: Rule 6(1)(h) & Rule 6(2), Legal Metrology (Packaged Commodities) Rules, 2011.
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class ConsumerCareRule(AbstractRule):
    """
    Validates declaration of Consumer Care contact details (Name, Address, Phone, Email).
    Legal Reference: Rule 6(1)(h) & Rule 6(2), Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-CARE-008"

    @property
    def rule_name(self) -> str:
        return "Consumer Care Details Declaration Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> str:
        return "consumerCare"

    @property
    def remediation_hint(self) -> Optional[str]:

        return "Declare name, complete address, telephone number, and email address of the Consumer Care officer/office."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """Consumer Care declaration applies to all retail packaged commodities."""
        return True

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        # Case 1: Consumer Care details are completely missing
        if not product.consumerCare or not product.consumerCare.strip():
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Consumer care contact details are completely missing from product payload."
            )

        care_text = product.consumerCare.strip().lower()

        has_email = "@" in care_text or "email" in care_text
        has_phone = any(c.isdigit() for c in care_text) or "tel" in care_text or "phone" in care_text or "call" in care_text

        # Case 2: Both contact number/email and contact info declared
        if has_email or has_phone:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.PASS,
                severity=self.severity,
                message="Consumer care contact details (phone/email/address) are declared."
            )

        # Case 3: Text provided but lacks clear phone number or email address
        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.MANUAL_REVIEW,
            severity=RuleSeverity.MEDIUM,
            message="Consumer care details provided but lack clear telephone/email contact format; manual verification required."
        )
