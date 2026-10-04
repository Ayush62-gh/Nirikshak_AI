"""
Legal Metrology Compliance Rule: Country of Origin Declaration Rule for Imported Commodities.
Statutory Provision: Rule 6(1)(ab), Legal Metrology (Packaged Commodities) Rules, 2011 (as amended).
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class CountryOfOriginRule(AbstractRule):
    """
    Validates Country of Origin declaration on imported packaged commodities.
    Legal Reference: Rule 6(1)(ab), Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-COO-009"

    @property
    def rule_name(self) -> str:
        return "Country of Origin Declaration Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.CRITICAL

    @property
    def target_field(self) -> str:
        return "countryOfOrigin"

    @property
    def remediation_hint(self) -> Optional[str]:
        return "Declare Country of Origin (e.g., 'Country of Origin: India' or 'Made in India') prominently on package labels."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """
        Applicability Condition:
        - Applicable if product is explicitly imported (isImported is True) OR if countryOfOrigin is provided.
        - Returns False (NOT_APPLICABLE) if product is domestic (isImported is False) or import status is unconfirmed without origin input.
        """
        if product.isImported is True or (product.countryOfOrigin and product.countryOfOrigin.strip()):
            return True
        return False

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        country = (product.countryOfOrigin or "").strip()

        # Case 1: Country of origin declaration is missing for an imported commodity
        if not country and product.isImported is True:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Mandatory Country of Origin declaration is missing on imported package."
            )

        # Case 2: Country of Origin declared
        if country:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.PASS,
                severity=self.severity,
                message=f"Country of Origin declaration is present: '{country}'."
            )

        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.MANUAL_REVIEW,
            severity=RuleSeverity.LOW,
            message="Country of Origin detail requires manual label review."
        )
